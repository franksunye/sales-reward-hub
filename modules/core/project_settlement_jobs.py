"""项目结算数据同步到企业微信电子表格。"""

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests

from modules.config import (
    API_URL_PROJECT_SETTLEMENT_SMARTSHEET,
    WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK,
)
from modules.core.storage import PerformanceDataStore, create_data_store
from modules.request_module import send_request_with_managed_session


PROJECT_SETTLEMENT_ACTIVITY_CODE = "PROJECT-SETTLEMENT-SMARTSHEET-SYNC"
PROJECT_SETTLEMENT_SCHEMA = {
    "f04Gwj": "合同编号",
    "ftQMc5": "项目施工地址",
    "ftk5Tx": "业主姓名",
    "ffFwIh": "联系电话",
    "fn8TJd": "部位",
    "fkf93Q": "进场日期",
    "fXjBwS": "完工日期",
    "fMqDX0": "项目用工数",
    "f8xImK": "班组名称",
    "fESKNz": "是否发起预结单",
    "f28Fkl": "结算状态",
    "f5Cx2q": "支付金额",
    "fStRfT": "合同金额",
}
PROJECT_SETTLEMENT_COLUMNS = list(PROJECT_SETTLEMENT_SCHEMA.values())
PROJECT_SETTLEMENT_MULTI_TEXT_FIELDS = {"f8xImK", "fESKNz", "f28Fkl"}
PROJECT_SETTLEMENT_NUMERIC_FIELDS = {"fMqDX0", "f5Cx2q", "fStRfT"}
PROJECT_SETTLEMENT_SOURCE_FIELD_MAP = {
    "f04Gwj": "contractdocNum",
    "ftQMc5": "address",
    "ftk5Tx": "contactsName",
    "ffFwIh": "contactsPhone",
    "fn8TJd": "leakagesiteText",
    "fkf93Q": "",
    "fXjBwS": "",
    "fMqDX0": "",
    "f8xImK": "",
    "fESKNz": "",
    "f28Fkl": "",
    "f5Cx2q": "paidAmount",
    "fStRfT": "adjustRefundMoney",
}
PROJECT_SETTLEMENT_IDENTITY_COLUMNS = (
    "contractdocNum",
    "address",
    "contactsName",
    "contactsPhone",
    "leakagesiteText",
    "signedDate",
)


def _is_truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _stringify(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_multi_text_value(value) -> List[Dict[str, str]]:
    if isinstance(value, list):
        items = []
        for item in value:
            text = item.get("text", "") if isinstance(item, dict) else _stringify(item)
            if text:
                items.append({"text": text})
        return items

    text = _stringify(value)
    if not text:
        return []

    parts = re.split(r"[\n,，、;；/]+", text)
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return [{"text": part} for part in cleaned] if cleaned else [{"text": text}]


def _normalize_numeric_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = _stringify(value).replace(",", "")
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None

    if number.is_integer():
        return int(number)
    return number


def _get_record_value(record: Dict, field_id: str):
    source_field = PROJECT_SETTLEMENT_SOURCE_FIELD_MAP.get(field_id, "")
    schema_label = PROJECT_SETTLEMENT_SCHEMA.get(field_id, "")
    if source_field and record.get(source_field) not in (None, ""):
        return record.get(source_field)
    if schema_label and record.get(schema_label) not in (None, ""):
        return record.get(schema_label)
    return None


class ProjectSettlementSmartsheetService:
    """Metabase -> 企业微信电子表格同步服务。"""

    def __init__(self, storage: PerformanceDataStore, now: Optional[datetime] = None):
        self.storage = storage
        self.now = now or datetime.now()
        self.logger = logging.getLogger(__name__)
        self.activity_code = PROJECT_SETTLEMENT_ACTIVITY_CODE
        self.dry_run = _is_truthy(os.getenv("PROJECT_SETTLEMENT_SMARTSHEET_DRY_RUN", ""))
        if not WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK:
            raise ValueError("WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK 环境变量未设置")

    def run(self) -> Dict[str, int]:
        stats = {
            "raw_records": 0,
            "eligible_records": 0,
            "enqueued": 0,
            "sent": 0,
            "failed": 0,
            "dead_letter": 0,
            "dry_run": 1 if self.dry_run else 0,
        }

        records = self._fetch_records_from_metabase()
        stats["raw_records"] = len(records)

        eligible_records = []
        for record in records:
            values = self._build_smartsheet_values(record)
            if not values or not values.get("f04Gwj"):
                self.logger.warning("跳过无效项目结算记录，缺少合同编号: %s", record)
                continue
            eligible_records.append((record, values))

        stats["eligible_records"] = len(eligible_records)
        if self.dry_run:
            self._log_dry_run_preview(eligible_records)
            return stats

        for record, values in eligible_records:
            outbox_id = self._enqueue_record(record, values)
            if not outbox_id:
                continue

            outbox = self.storage.get_outbox_message(outbox_id)
            if outbox.get("status") == "sent":
                continue
            stats["enqueued"] += 1

        dispatch_stats = self._dispatch_outbox()
        for key in ("sent", "failed", "dead_letter"):
            stats[key] = dispatch_stats[key]
        return stats

    def _fetch_records_from_metabase(self) -> List[Dict]:
        self.logger.info("获取项目结算数据: %s", API_URL_PROJECT_SETTLEMENT_SMARTSHEET)
        response = send_request_with_managed_session(API_URL_PROJECT_SETTLEMENT_SMARTSHEET)
        if not response or "data" not in response:
            self.logger.warning("项目结算接口返回为空或格式异常")
            return []

        data = response.get("data", {})
        rows = data.get("rows", []) or []
        cols = data.get("cols", []) or []
        names = [col.get("name") for col in cols] if cols else list(dict.fromkeys(PROJECT_SETTLEMENT_SOURCE_FIELD_MAP.values()))
        return [dict(zip(names, row)) for row in rows]

    def _build_smartsheet_values(self, record: Dict) -> Dict:
        values = {}
        for field_id in PROJECT_SETTLEMENT_SCHEMA:
            raw_value = _get_record_value(record, field_id)
            if field_id in PROJECT_SETTLEMENT_MULTI_TEXT_FIELDS:
                items = _build_multi_text_value(raw_value)
                if items:
                    values[field_id] = items
                continue

            if field_id in PROJECT_SETTLEMENT_NUMERIC_FIELDS:
                number = _normalize_numeric_value(raw_value)
                if number is not None:
                    values[field_id] = number
                continue

            text = _stringify(raw_value)
            if text:
                values[field_id] = text
        return values

    def _enqueue_record(self, record: Dict, values: Dict) -> int:
        dedupe_key = self._build_dedupe_key(record)
        payload = {
            "schema": PROJECT_SETTLEMENT_SCHEMA,
            "add_records": [{"values": values}],
        }
        metadata = {
            "contract_no": _stringify(_get_record_value(record, "f04Gwj")),
            "identity_fields": {key: _stringify(record.get(key)) for key in PROJECT_SETTLEMENT_IDENTITY_COLUMNS},
            "run_marker": self.now.isoformat(),
        }
        return self.storage.enqueue_outbox_message(
            activity_code=self.activity_code,
            contract_id=_stringify(_get_record_value(record, "f04Gwj")) or dedupe_key,
            message_type="wedoc_add_record",
            webhook_url=WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK,
            payload_json=json.dumps(payload, ensure_ascii=False),
            metadata_json=json.dumps(metadata, ensure_ascii=False),
            dedupe_key=dedupe_key,
        )

    def _dispatch_outbox(self) -> Dict[str, int]:
        stats = {"sent": 0, "failed": 0, "dead_letter": 0}
        max_attempts = int(os.getenv("NOTIFICATION_OUTBOX_MAX_ATTEMPTS", "5"))
        limit = int(os.getenv("NOTIFICATION_OUTBOX_BATCH_LIMIT", "200"))
        outbox_items = self.storage.get_retryable_outbox_messages(
            self.activity_code,
            max_attempts=max_attempts,
            limit=limit,
        )

        for item in outbox_items:
            try:
                payload = json.loads(item.get("payload_json") or "{}")
                self.logger.info(
                    "发送企业微信电子表格 webhook: activity=%s, outbox_id=%s, contract=%s",
                    item.get("activity_code"),
                    item.get("id"),
                    item.get("contract_id"),
                )
                response = requests.post(item["webhook_url"], json=payload, timeout=20)
                body_text = (response.text or "")[:2000]
                if self._is_success_response(response.status_code, body_text):
                    self.storage.mark_outbox_sent(item["id"], response.status_code, body_text)
                    stats["sent"] += 1
                else:
                    self.storage.mark_outbox_failed(
                        outbox_id=item["id"],
                        last_error=f"HTTP {response.status_code}: {body_text}",
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

    def _log_dry_run_preview(self, eligible_records: List[Tuple[Dict, Dict]]) -> None:
        for record, values in eligible_records[:10]:
            self.logger.info(
                "[DRY RUN] 项目结算记录将写入电子表格: contract=%s, values=%s",
                _stringify(_get_record_value(record, "f04Gwj")),
                json.dumps(values, ensure_ascii=False),
            )

    @staticmethod
    def _build_dedupe_key(record: Dict) -> str:
        identity_parts = [
            _stringify(_get_record_value(record, "f04Gwj")),
            _stringify(_get_record_value(record, "ftQMc5")),
            _stringify(_get_record_value(record, "ftk5Tx")),
            _stringify(_get_record_value(record, "ffFwIh")),
            _stringify(_get_record_value(record, "fn8TJd")),
            _stringify(record.get("signedDate")),
            _stringify(_get_record_value(record, "f8xImK")),
        ]
        raw = "::".join(identity_parts)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
        return f"wedoc-project-settlement::{raw}::{digest}"

    @staticmethod
    def _is_success_response(status_code: int, body_text: str) -> bool:
        if not (200 <= status_code < 300):
            return False
        if not body_text:
            return True
        try:
            body = json.loads(body_text)
        except json.JSONDecodeError:
            return True
        errcode = body.get("errcode")
        return errcode in (None, 0, "0")


def sync_project_settlement_smartsheet_v2(now: Optional[datetime] = None) -> Dict[str, int]:
    storage = create_data_store(storage_type="sqlite", db_path="performance_data.db")
    service = ProjectSettlementSmartsheetService(storage, now=now)
    stats = service.run()
    logging.info("项目结算电子表格同步完成: %s", stats)
    return stats


def sync_project_settlement_smartsheet() -> Dict[str, int]:
    return sync_project_settlement_smartsheet_v2()
