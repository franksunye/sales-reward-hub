"""管家下线企业微信群播报任务。"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import requests

from modules.config import API_URL_HOUSEKEEPER_OFFLINE
from modules.core.storage import PerformanceDataStore, create_data_store
from modules.core.webhook_router import (
    CHANNEL_HOUSEKEEPER_OFFLINE,
    format_safe_webhook_target,
    resolve_wecom_webhook,
)
from modules.request_module import send_request_with_managed_session


HOUSEKEEPER_OFFLINE_ACTIVITY_CODE = "HOUSEKEEPER-OFFLINE-BROADCAST"


def _is_truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _column_keys(column: Dict, index: int) -> List[str]:
    keys = []
    for key in (column.get("name"), column.get("display_name"), column.get("field_ref")):
        if isinstance(key, str) and key.strip() and key not in keys:
            keys.append(key.strip())
    return keys or [f"column_{index}"]


def _parse_metabase_records(response: Dict) -> List[Dict]:
    """按 Metabase cols 元数据把二维 rows 转成字典，同时保留原始行用于去重。"""
    data = response.get("data", {}) if isinstance(response, dict) else {}
    columns = data.get("cols", []) or []
    records = []
    for row in data.get("rows", []) or []:
        values = list(row) if isinstance(row, (list, tuple)) else []
        record = {"_raw_row": values}
        for index, value in enumerate(values):
            column = columns[index] if index < len(columns) and isinstance(columns[index], dict) else {}
            for key in _column_keys(column, index):
                record[key] = value
        records.append(record)
    return records


def _get_field(record: Dict, field_name: str):
    target = field_name.casefold()
    for key, value in record.items():
        if key != "_raw_row" and str(key).casefold() == target:
            return value
    return None


def _normalize_text(value) -> str:
    if isinstance(value, (list, tuple)):
        return "、".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def _get_operation(record: Dict) -> str:
    return _normalize_text(_get_field(record, "operation") or _get_field(record, "动作"))


def _parse_event_time(value) -> datetime | None:
    text = _normalize_text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _format_housekeeper_offline_message(create_user_name: str, operation: str) -> str:
    return f"管家【{create_user_name}】【{operation}】了。"


def _event_fingerprint(record: Dict) -> str:
    """使用完整源记录去重；源数据中的 ID/时间字段可区分同一管家的多次操作。"""
    canonical = json.dumps(record.get("_raw_row", []), ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class HousekeeperOfflineBroadcastService:
    def __init__(self, storage: PerformanceDataStore, now: datetime | None = None):
        self.storage = storage
        self.logger = logging.getLogger(__name__)
        self.activity_code = HOUSEKEEPER_OFFLINE_ACTIVITY_CODE
        self.dry_run = _is_truthy(os.getenv("HOUSEKEEPER_OFFLINE_DRY_RUN", ""))
        self.now = now or datetime.now(timezone.utc)
        if self.now.tzinfo is None:
            self.now = self.now.replace(tzinfo=timezone.utc)
        self.lookback_minutes = max(1, int(os.getenv("HOUSEKEEPER_OFFLINE_LOOKBACK_MINUTES", "60")))

    def run(self) -> Dict[str, int]:
        stats = {
            "raw_events": 0,
            "valid_events": 0,
            "stale_events": 0,
            "invalid_events": 0,
            "enqueued": 0,
            "sent": 0,
            "failed": 0,
            "dead_letter": 0,
            "dry_run": int(self.dry_run),
        }
        records = self._fetch_records()
        stats["raw_events"] = len(records)
        cutoff = self.now - timedelta(minutes=self.lookback_minutes)

        for record in records:
            create_user_name = _normalize_text(_get_field(record, "createUserName"))
            operation = _get_operation(record)
            event_time = _parse_event_time(_get_field(record, "createTime"))
            if not create_user_name or not operation or event_time is None:
                stats["invalid_events"] += 1
                continue
            if event_time < cutoff:
                stats["stale_events"] += 1
                continue

            stats["valid_events"] += 1
            message = _format_housekeeper_offline_message(create_user_name, operation)
            if self.dry_run:
                self.logger.info("[DRY RUN] 管家下线播报预览: %s", message)
                continue

            fingerprint = _event_fingerprint(record)
            outbox_id = self.storage.enqueue_outbox_message(
                activity_code=self.activity_code,
                contract_id=f"event::{fingerprint}",
                message_type="housekeeper_offline_broadcast",
                webhook_url=resolve_wecom_webhook(CHANNEL_HOUSEKEEPER_OFFLINE),
                payload_json=json.dumps({"msgtype": "text", "text": {"content": message}}, ensure_ascii=False),
                metadata_json=json.dumps({"source": "metabase_card_2085"}, ensure_ascii=False),
                dedupe_key=fingerprint,
            )
            if outbox_id and self.storage.get_outbox_message(outbox_id).get("status") != "sent":
                stats["enqueued"] += 1

        if not self.dry_run:
            stats.update(self._dispatch_outbox())
        if stats["invalid_events"]:
            self.logger.warning(
                "跳过 %s 条缺少 createUserName/operation(动作)/createTime 的记录",
                stats["invalid_events"],
            )
        return stats

    def _fetch_records(self) -> List[Dict]:
        self.logger.info("获取管家下线数据: %s", API_URL_HOUSEKEEPER_OFFLINE)
        response = send_request_with_managed_session(API_URL_HOUSEKEEPER_OFFLINE)
        if not response or "data" not in response:
            self.logger.warning("管家下线 Metabase 接口返回为空或格式异常")
            return []
        return _parse_metabase_records(response)

    def _dispatch_outbox(self) -> Dict[str, int]:
        stats = {"sent": 0, "failed": 0, "dead_letter": 0}
        max_attempts = int(os.getenv("NOTIFICATION_OUTBOX_MAX_ATTEMPTS", "5"))
        limit = int(os.getenv("NOTIFICATION_OUTBOX_BATCH_LIMIT", "200"))
        items = self.storage.get_retryable_outbox_messages(self.activity_code, max_attempts=max_attempts, limit=limit)
        for item in items:
            try:
                payload = json.loads(item.get("payload_json") or "{}")
                self.logger.info(
                    "发送 webhook: activity=%s, outbox_id=%s, type=%s, event=%s, %s",
                    item.get("activity_code"), item.get("id"), item.get("message_type"),
                    item.get("contract_id"), format_safe_webhook_target(item.get("webhook_url", "")),
                )
                response = requests.post(item["webhook_url"], json=payload, timeout=20)
                body_text = (response.text or "")[:2000]
                try:
                    response_data = response.json()
                except (ValueError, TypeError):
                    response_data = {}
                success = 200 <= response.status_code < 300 and response_data.get("errcode", 0) == 0
                if success:
                    self.storage.mark_outbox_sent(item["id"], response.status_code, body_text)
                    stats["sent"] += 1
                else:
                    error = response_data.get("errmsg") or f"HTTP {response.status_code}"
                    self._mark_failed(item, error, max_attempts, response.status_code, body_text, stats)
            except Exception as exc:
                self._mark_failed(item, str(exc), max_attempts, 0, "", stats)
            time.sleep(0.2)
        return stats

    def _mark_failed(
        self,
        item: Dict,
        error: str,
        max_attempts: int,
        response_code: int,
        response_body: str,
        stats: Dict[str, int],
    ) -> None:
        self.storage.mark_outbox_failed(
            outbox_id=item["id"], last_error=error, response_code=response_code,
            response_body=response_body, max_attempts=max_attempts,
        )
        key = "dead_letter" if int(item.get("attempt_count", 0)) + 1 >= max_attempts else "failed"
        stats[key] += 1


def broadcast_housekeeper_offline_v2() -> Dict[str, int]:
    storage = create_data_store(storage_type="sqlite", db_path="performance_data.db")
    stats = HousekeeperOfflineBroadcastService(storage).run()
    logging.info("管家下线播报完成: %s", stats)
    return stats


def broadcast_housekeeper_offline() -> Dict[str, int]:
    return broadcast_housekeeper_offline_v2()
