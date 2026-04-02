"""待预约工单提醒 - 数据库优先版本。"""

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from modules.config import API_URL_PENDING_ORDERS_REMINDER
from modules.core.storage import PerformanceDataStore, create_data_store
from modules.core.webhook_router import CHANNEL_PENDING_ORDERS, format_safe_webhook_target, resolve_wecom_webhook
from modules.request_module import send_request_with_managed_session


PENDING_ORDERS_ACTIVITY_CODE = "PENDING-ORDERS-REMINDER"


def _is_truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_iso_datetime(value: str) -> datetime:
    if "+" in value:
        parsed = datetime.fromisoformat(value)
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _format_simple_date(value: str) -> str:
    try:
        parsed = _parse_iso_datetime(value)
        return parsed.astimezone(timezone.utc).strftime("%m-%d %H:%M")
    except Exception:
        return value or "-"


def _calculate_retention_duration(value: str, now: Optional[datetime] = None) -> str:
    try:
        parsed = _parse_iso_datetime(value)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        duration = current - parsed
        days = int(duration.total_seconds() // (24 * 3600))
        return f"{days}天"
    except Exception:
        return "未知"


def _simplify_order_number(order_num: str) -> str:
    if not order_num:
        return "-"
    numbers = re.findall(r"\d+", str(order_num))
    if not numbers:
        return str(order_num)
    tail = numbers[-1]
    return tail[-5:] if len(tail) >= 5 else tail


def _format_pending_orders_message(org_name: str, rows: List[Dict]) -> str:
    count = len(rows)
    message_lines = [
        f"📋 待预约工单提醒 ({org_name})",
        "",
        f"共有 {count} 个工单待预约：",
        "",
    ]

    for index, row in enumerate(rows, 1):
        order_text = f"""{index:02d}. 工单号：{_simplify_order_number(row.get('order_num', ''))}
     客户：{row.get('customer_name', '')}
     地址：{row.get('address', '')}
     负责人：{row.get('supervisor_name', '')}
     创建时间：{_format_simple_date(row.get('create_time', ''))}（{_calculate_retention_duration(row.get('create_time', ''))}）
     状态：{row.get('order_status', '')}"""
        message_lines.append(order_text)
        if index < count:
            message_lines.append("")

    message_lines.extend(["", "请及时跟进处理，如有疑问请联系运营人员。"])
    return "\n".join(message_lines)


class PendingOrdersReminderService:
    """待预约工单提醒服务。"""

    def __init__(self, storage: PerformanceDataStore, now: Optional[datetime] = None):
        self.storage = storage
        self.now = now or datetime.now(timezone.utc)
        if self.now.tzinfo is None:
            self.now = self.now.replace(tzinfo=timezone.utc)
        self.logger = logging.getLogger(__name__)
        self.activity_code = PENDING_ORDERS_ACTIVITY_CODE
        self.dry_run = _is_truthy(os.getenv("PENDING_ORDERS_DRY_RUN", ""))

    def run(self) -> Dict[str, int]:
        """执行一次待预约工单提醒。"""
        stats = {
            "raw_orders": 0,
            "eligible_orders": 0,
            "deactivated_orders": 0,
            "orgs_with_new_orders": 0,
            "enqueued": 0,
            "sent": 0,
            "failed": 0,
            "dead_letter": 0,
            "dry_run": 1 if self.dry_run else 0,
        }

        rows = self._fetch_rows_from_metabase()
        stats["raw_orders"] = len(rows)
        snapshots = self._filter_and_build_snapshots(rows)
        stats["eligible_orders"] = len(snapshots)

        active_fingerprints = []
        for snapshot in snapshots:
            self.storage.upsert_pending_order_snapshot(self.activity_code, snapshot)
            active_fingerprints.append(snapshot["status_fingerprint"])

        stats["deactivated_orders"] = self.storage.deactivate_missing_pending_orders(
            self.activity_code,
            active_fingerprints,
        )

        active_by_org: Dict[str, List[Dict]] = {}
        for snapshot in snapshots:
            org_name = snapshot["org_name"]
            active_by_org.setdefault(org_name, [])
        for org_name in list(active_by_org.keys()):
            active_rows = self.storage.get_active_pending_orders_by_org(self.activity_code, org_name)
            if active_rows:
                active_by_org[org_name] = active_rows
            else:
                active_by_org.pop(org_name, None)

        # 兼容原有统计字段名，当前语义为“本次需要提醒的服务商数量”
        stats["orgs_with_new_orders"] = len(active_by_org)
        if self.dry_run and active_by_org:
            self._log_dry_run_preview(active_by_org)

        if self.dry_run:
            return stats

        for org_name, active_rows in active_by_org.items():
            outbox_id = self._enqueue_org_digest(org_name, active_rows)
            if not outbox_id:
                continue

            outbox = self.storage.get_outbox_message(outbox_id)
            if outbox.get("status") == "sent":
                self._mark_rows_notified_from_metadata(outbox)
                continue
            stats["enqueued"] += 1

        dispatch_stats = self._dispatch_outbox()
        for key in ("sent", "failed", "dead_letter"):
            stats[key] = dispatch_stats[key]
        return stats

    def _log_dry_run_preview(self, active_by_org: Dict[str, List[Dict]]) -> None:
        for org_name, active_rows in active_by_org.items():
            preview = _format_pending_orders_message(org_name, active_rows)
            self.logger.info(
                "[DRY RUN] 待预约提醒将发送给 %s，当前活跃工单 %s 条",
                org_name,
                len(active_rows),
            )
            self.logger.info("[DRY RUN] 消息预览:\n%s", preview)

    def _fetch_rows_from_metabase(self) -> List[List]:
        self.logger.info("获取待预约工单数据: %s", API_URL_PENDING_ORDERS_REMINDER)
        response = send_request_with_managed_session(API_URL_PENDING_ORDERS_REMINDER)
        if not response or "data" not in response:
            self.logger.warning("待预约工单接口返回为空或格式异常")
            return []
        return response.get("data", {}).get("rows", []) or []

    def _filter_and_build_snapshots(self, rows: List[List]) -> List[Dict]:
        snapshots = []
        for row in rows:
            try:
                order_num = str(row[0])
                customer_name = row[1] or ""
                address = row[2] or ""
                supervisor_name = row[3] or ""
                create_time = row[4]
                org_name = row[5] or ""
                order_status = row[6] or ""

                created_at = _parse_iso_datetime(create_time)
                hours_elapsed = (self.now - created_at).total_seconds() / 3600
                if ("待预约" in order_status or "暂不上门" in order_status) and hours_elapsed < 48:
                    continue

                fingerprint_seed = f"{order_num}::{order_status}"
                status_fingerprint = hashlib.sha256(fingerprint_seed.encode("utf-8")).hexdigest()
                snapshots.append(
                    {
                        "order_num": order_num,
                        "customer_name": customer_name,
                        "address": address,
                        "supervisor_name": supervisor_name,
                        "create_time": create_time,
                        "org_name": org_name,
                        "order_status": order_status,
                        "status_fingerprint": status_fingerprint,
                        "eligible_since": self.now.isoformat(),
                        "extensions": json.dumps(
                            {"hours_elapsed": round(hours_elapsed, 2)},
                            ensure_ascii=False,
                        ),
                    }
                )
            except Exception as exc:
                self.logger.warning("跳过异常工单数据 %s，错误: %s", row, exc)
        return snapshots

    def _enqueue_org_digest(self, org_name: str, active_rows: List[Dict]) -> int:
        payload = {
            "msgtype": "text",
            "text": {"content": _format_pending_orders_message(org_name, active_rows)},
        }
        metadata = {
            "pending_order_fingerprints": [row["status_fingerprint"] for row in active_rows],
            "org_name": org_name,
            "run_marker": self.now.isoformat(),
        }
        return self.storage.enqueue_outbox_message(
            activity_code=self.activity_code,
            contract_id=f"org::{org_name}",
            message_type="pending_orders_digest",
            webhook_url=resolve_wecom_webhook(CHANNEL_PENDING_ORDERS, org_name=org_name),
            payload_json=json.dumps(payload, ensure_ascii=False),
            metadata_json=json.dumps(metadata, ensure_ascii=False),
            dedupe_key=f"{org_name}::pending_orders_digest::{self.now.isoformat()}",
        )

    def _dispatch_outbox(self) -> Dict[str, int]:
        stats = {"sent": 0, "failed": 0, "dead_letter": 0}
        max_attempts = int(os.getenv("NOTIFICATION_OUTBOX_MAX_ATTEMPTS", "5"))
        limit = int(os.getenv("NOTIFICATION_OUTBOX_BATCH_LIMIT", "200"))
        outbox_items = self.storage.get_retryable_outbox_messages(self.activity_code, max_attempts=max_attempts, limit=limit)

        for item in outbox_items:
            try:
                payload = json.loads(item.get("payload_json") or "{}")
                self.logger.info(
                    "发送 webhook: activity=%s, outbox_id=%s, type=%s, contract=%s, %s",
                    item.get("activity_code"),
                    item.get("id"),
                    item.get("message_type"),
                    item.get("contract_id"),
                    format_safe_webhook_target(item.get("webhook_url", "")),
                )
                response = requests.post(item["webhook_url"], json=payload, timeout=20)
                body_text = (response.text or "")[:2000]
                if 200 <= response.status_code < 300:
                    self.storage.mark_outbox_sent(item["id"], response.status_code, body_text)
                    self._mark_rows_notified_from_metadata(item)
                    stats["sent"] += 1
                else:
                    self.storage.mark_outbox_failed(
                        outbox_id=item["id"],
                        last_error=f"HTTP {response.status_code}",
                        response_code=response.status_code,
                        response_body=body_text,
                        max_attempts=max_attempts,
                    )
                    if int(item.get("attempt_count", 0)) + 1 >= max_attempts:
                        stats["dead_letter"] += 1
                    else:
                        stats["failed"] += 1
            except Exception as exc:
                self.storage.mark_outbox_failed(
                    outbox_id=item["id"],
                    last_error=str(exc),
                    max_attempts=max_attempts,
                )
                if int(item.get("attempt_count", 0)) + 1 >= max_attempts:
                    stats["dead_letter"] += 1
                else:
                    stats["failed"] += 1
            time.sleep(0.2)
        return stats

    def _mark_rows_notified_from_metadata(self, outbox_item: Dict) -> int:
        try:
            metadata = json.loads(outbox_item.get("metadata_json") or "{}")
        except json.JSONDecodeError:
            metadata = {}
        fingerprints = metadata.get("pending_order_fingerprints") or []
        return self.storage.mark_pending_orders_notified(self.activity_code, fingerprints)


def send_pending_orders_reminder_v2(now: Optional[datetime] = None) -> Dict[str, int]:
    """数据库优先版本的待预约工单提醒。"""
    storage = create_data_store(storage_type="sqlite", db_path="performance_data.db")
    service = PendingOrdersReminderService(storage, now=now)
    stats = service.run()
    logging.info("待预约工单提醒完成: %s", stats)
    return stats


def send_pending_orders_reminder() -> Dict[str, int]:
    """兼容入口。"""
    return send_pending_orders_reminder_v2()
