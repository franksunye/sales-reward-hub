"""SLA 日报/周报任务 - 数据库优先版本。"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

from modules.config import API_URL_DAILY_SERVICE_REPORT
from modules.core.storage import PerformanceDataStore, create_data_store
from modules.core.webhook_router import (
    CHANNEL_SLA_DAILY_REPORT,
    get_configured_provider_names,
    resolve_wecom_webhook,
)
from modules.request_module import send_request_with_managed_session


SLA_ACTIVITY_CODE = "SLA-DAILY-SERVICE-REPORT"
SLA_REPORT_COLUMNS = [
    "_id",
    "sid",
    "saCreateTime",
    "orderNum",
    "province",
    "orgName",
    "supervisorName",
    "sourceType",
    "status",
    "msg",
    "memo",
    "workType",
    "createTime",
]


def _is_truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _beijing_now(now: Optional[datetime] = None) -> datetime:
    tz = ZoneInfo("Asia/Shanghai") if ZoneInfo is not None else timezone(timedelta(hours=8))
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=tz)
    return now.astimezone(tz)


def _safe_parse_datetime(time_str: str) -> datetime:
    normalized = (time_str or "").replace("Z", "")
    if "+" in normalized:
        head, tail = normalized.rsplit("+", 1)
        tz = f"+{tail}"
    elif "-" in normalized[19:]:
        head, tail = normalized.rsplit("-", 1)
        tz = f"-{tail}"
    else:
        return datetime.fromisoformat(normalized)

    if "." in head:
        base, micros = head.split(".", 1)
        micros = micros[:6].ljust(6, "0")
        normalized = f"{base}.{micros}{tz}"
    else:
        normalized = f"{head}{tz}"
    return datetime.fromisoformat(normalized)


def construct_sla_violation_message(violation_record: Dict) -> str:
    create_time = _safe_parse_datetime(violation_record["saCreateTime"])
    formatted_time = create_time.strftime("%Y-%m-%d %H:%M")
    return (
        f"超时通知:\n"
        f"工单编号：{violation_record['orderNum']}\n"
        f"建单时间：{formatted_time}\n"
        f"管家：{violation_record['supervisorName']}\n"
        f"违规类型：{violation_record['msg']}\n"
        f"违规描述：{violation_record['memo']}\n"
        f"说明：以上数据为服务商昨日工单超时统计，如有异议请于下周一十二点前联系运营申诉。"
    )


def build_sla_compliance_message() -> str:
    return "上周无超时工单，请继续保持。👍"


def build_sla_performance_report(provider: str, records: List[Dict], now: datetime) -> str:
    monday = now - timedelta(days=now.weekday())
    period_start = (monday - timedelta(days=7)).strftime("%Y.%m.%d")
    period_end = (monday - timedelta(days=1)).strftime("%Y.%m.%d")
    appeal_deadline = monday.strftime("%Y.%m.%d")

    report = [f"数据周期: {period_start}-{period_end}", f"服务商: {provider}", ""]
    for record in records:
        report.append(
            f"- 工单编号：{record['order_num']} 管家：{record['supervisor_name']} 违规类型：{record['violation_type']}"
        )
    report.append("")
    report.append(f"如有异议，请于 {appeal_deadline} 24 时前，联系运营人员申诉")
    return "\n".join(report)


class DailyServiceReportService:
    """SLA 日报/周报服务。"""

    def __init__(self, storage: PerformanceDataStore, now: Optional[datetime] = None):
        self.storage = storage
        self.now = _beijing_now(now)
        self.logger = logging.getLogger(__name__)
        self.activity_code = SLA_ACTIVITY_CODE
        self.dry_run = _is_truthy(os.getenv("DAILY_SERVICE_REPORT_DRY_RUN", ""))

    def run(self) -> Dict[str, int]:
        stats = {
            "raw_records": 0,
            "stored_records": 0,
            "daily_enqueued": 0,
            "weekly_enqueued": 0,
            "sent": 0,
            "failed": 0,
            "dead_letter": 0,
            "dry_run": 1 if self.dry_run else 0,
        }

        report_data = self._fetch_report_data()
        stats["raw_records"] = len(report_data)
        business_date = self._business_date()
        stats["stored_records"] = self.storage.replace_sla_violations_for_date(business_date, report_data)

        if self.dry_run:
            self._log_daily_preview(report_data)
            if self._is_monday():
                self._log_weekly_preview()
            return stats

        for record in report_data:
            if self._enqueue_daily_violation(record, business_date):
                stats["daily_enqueued"] += 1

        if self._is_monday():
            weekly_stats = self._enqueue_weekly_reports()
            stats["weekly_enqueued"] = weekly_stats["weekly_enqueued"]

        dispatch_stats = self._dispatch_outbox()
        stats["sent"] = dispatch_stats["sent"]
        stats["failed"] = dispatch_stats["failed"]
        stats["dead_letter"] = dispatch_stats["dead_letter"]
        return stats

    def _fetch_report_data(self) -> List[Dict]:
        self.logger.info("获取 SLA 日报数据: %s", API_URL_DAILY_SERVICE_REPORT)
        response = send_request_with_managed_session(API_URL_DAILY_SERVICE_REPORT)
        if not response or "data" not in response:
            self.logger.warning("SLA 日报接口返回为空或格式异常")
            return []

        data = response.get("data", {})
        rows = data.get("rows", []) or []
        cols = data.get("cols", []) or []
        if cols:
            names = [col.get("name") for col in cols]
        else:
            names = SLA_REPORT_COLUMNS

        return [dict(zip(names, row)) for row in rows]

    def _business_date(self) -> str:
        return (self.now.date() - timedelta(days=1)).strftime("%Y-%m-%d")

    def _is_monday(self) -> bool:
        return self.now.weekday() == 0

    def _enqueue_daily_violation(self, record: Dict, business_date: str) -> int:
        msg = construct_sla_violation_message(record)
        payload = {"msgtype": "text", "text": {"content": msg}}
        dedupe_key = self._build_hash_key(
            "sla-daily",
            business_date,
            record.get("orgName", ""),
            record.get("orderNum", ""),
            record.get("msg", ""),
            record.get("memo", ""),
        )
        return self.storage.enqueue_outbox_message(
            activity_code=self.activity_code,
            contract_id=f"sla::{business_date}::{record.get('orderNum', '')}",
            message_type="sla_daily_violation",
            webhook_url=resolve_wecom_webhook(CHANNEL_SLA_DAILY_REPORT, record.get("orgName", "")),
            payload_json=json.dumps(payload, ensure_ascii=False),
            dedupe_key=dedupe_key,
        )

    def _enqueue_weekly_reports(self) -> Dict[str, int]:
        weekly_enqueued = 0
        start_date = (self.now.date() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (self.now.date() - timedelta(days=1)).strftime("%Y-%m-%d")
        records = self.storage.get_sla_violations_for_window(start_date, end_date)
        violating_providers = sorted({row["org_name"] for row in records})
        all_providers = set(get_configured_provider_names())
        compliant_providers = sorted(all_providers - set(violating_providers))
        period_marker = end_date

        for provider in compliant_providers:
            payload = {"msgtype": "text", "text": {"content": build_sla_compliance_message()}}
            if self.storage.enqueue_outbox_message(
                activity_code=self.activity_code,
                contract_id=f"sla-weekly::{provider}",
                message_type="sla_weekly_compliance",
                webhook_url=resolve_wecom_webhook(CHANNEL_SLA_DAILY_REPORT, provider),
                payload_json=json.dumps(payload, ensure_ascii=False),
                dedupe_key=self._build_hash_key("sla-weekly-compliance", period_marker, provider),
            ):
                weekly_enqueued += 1

        for provider in violating_providers:
            provider_records = [row for row in records if row["org_name"] == provider]
            report = build_sla_performance_report(provider, provider_records, self.now)
            payload = {"msgtype": "text", "text": {"content": report}}
            if self.storage.enqueue_outbox_message(
                activity_code=self.activity_code,
                contract_id=f"sla-weekly::{provider}",
                message_type="sla_weekly_report",
                webhook_url=resolve_wecom_webhook(CHANNEL_SLA_DAILY_REPORT, provider),
                payload_json=json.dumps(payload, ensure_ascii=False),
                dedupe_key=self._build_hash_key("sla-weekly-report", period_marker, provider),
            ):
                weekly_enqueued += 1

        return {"weekly_enqueued": weekly_enqueued}

    def _dispatch_outbox(self) -> Dict[str, int]:
        stats = {"sent": 0, "failed": 0, "dead_letter": 0}
        max_attempts = int(os.getenv("NOTIFICATION_OUTBOX_MAX_ATTEMPTS", "5"))
        limit = int(os.getenv("NOTIFICATION_OUTBOX_BATCH_LIMIT", "200"))
        outbox_items = self.storage.get_retryable_outbox_messages(self.activity_code, max_attempts=max_attempts, limit=limit)

        for item in outbox_items:
            try:
                payload = json.loads(item.get("payload_json") or "{}")
                response = requests.post(item["webhook_url"], json=payload, timeout=20)
                body_text = (response.text or "")[:2000]
                if 200 <= response.status_code < 300:
                    self.storage.mark_outbox_sent(item["id"], response.status_code, body_text)
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

    def _log_daily_preview(self, records: List[Dict]) -> None:
        if not records:
            self.logger.info("[DRY RUN] SLA 日报无违规记录")
            return
        for record in records[:10]:
            self.logger.info("[DRY RUN] SLA 日报预览:\n%s", construct_sla_violation_message(record))

    def _log_weekly_preview(self) -> None:
        start_date = (self.now.date() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (self.now.date() - timedelta(days=1)).strftime("%Y-%m-%d")
        records = self.storage.get_sla_violations_for_window(start_date, end_date)
        violating_providers = sorted({row["org_name"] for row in records})
        all_providers = set(get_configured_provider_names())
        compliant_providers = sorted(all_providers - set(violating_providers))
        self.logger.info(
            "[DRY RUN] SLA 周报预览: 违规服务商=%s, 达标服务商=%s",
            violating_providers,
            compliant_providers,
        )
        for provider in violating_providers[:5]:
            provider_records = [row for row in records if row["org_name"] == provider]
            self.logger.info("[DRY RUN] SLA 周报消息预览:\n%s", build_sla_performance_report(provider, provider_records, self.now))

    @staticmethod
    def _build_hash_key(*parts: str) -> str:
        raw = "::".join(str(part) for part in parts)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
        return f"{raw}::{digest}"


def generate_daily_service_report_v2(now: Optional[datetime] = None) -> Dict[str, int]:
    storage = create_data_store(storage_type="sqlite", db_path="performance_data.db")
    service = DailyServiceReportService(storage, now=now)
    stats = service.run()
    logging.info("SLA 日报任务完成: %s", stats)
    return stats


def generate_daily_service_report() -> Dict[str, int]:
    return generate_daily_service_report_v2()
