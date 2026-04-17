"""企业微信电子表格同步任务。"""

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    ZoneInfo = None

from modules.config import (
    API_URL_CONTRACT_COMPLETION_SMARTSHEET,
    API_URL_PAYMENT_RECORDS_SMARTSHEET,
    API_URL_PROJECT_SETTLEMENT_SMARTSHEET,
    WECOM_CONTRACT_COMPLETION_SMARTSHEET_WEBHOOK,
    WECOM_PAYMENT_RECORDS_SMARTSHEET_WEBHOOK,
    WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK,
)
from modules.core.storage import PerformanceDataStore, create_data_store
from modules.request_module import send_request_with_managed_session


@dataclass(frozen=True)
class SmartsheetSyncConfig:
    activity_code: str
    api_url: str
    webhook_url: str
    schema: Dict[str, str]
    source_field_map: Dict[str, str]
    primary_field_id: str
    log_label: str
    dry_run_env: str
    dedupe_prefix: str
    dispatch_delay_seconds: float = 0.2
    numeric_fields: Set[str] = field(default_factory=set)
    datetime_fields: Set[str] = field(default_factory=set)
    multi_text_fields: Set[str] = field(default_factory=set)
    identity_keys: Tuple[str, ...] = ()


def _get_beijing_tz():
    if ZoneInfo is not None:
        return ZoneInfo("Asia/Shanghai")
    return timezone.utc


PROJECT_SETTLEMENT_SYNC_CONFIG = SmartsheetSyncConfig(
    activity_code="PROJECT-SETTLEMENT-SMARTSHEET-SYNC",
    api_url=API_URL_PROJECT_SETTLEMENT_SMARTSHEET,
    webhook_url=WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK,
    schema={
        "f04Gwj": "合同编号",
        "ftQMc5": "项目施工地址",
        "ftk5Tx": "业主姓名",
        "ffFwIh": "联系电话",
        "foyhkS": "管家",
        "fn8TJd": "部位",
        "fkf93Q": "进场日期",
        "fXjBwS": "完工日期",
        "fMqDX0": "项目用工数",
        "f8xImK": "班组名称",
        "fESKNz": "是否发起预结单",
        "f28Fkl": "结算状态",
        "fStRfT": "合同金额",
    },
    source_field_map={
        "f04Gwj": "contractdocNum",
        "ftQMc5": "address",
        "ftk5Tx": "contactsName",
        "ffFwIh": "contactsPhone",
        "foyhkS": "serviceHousekeeper",
        "fn8TJd": "leakagesiteText",
        "fkf93Q": "",
        "fXjBwS": "",
        "fMqDX0": "",
        "f8xImK": "",
        "fESKNz": "",
        "f28Fkl": "",
        "fStRfT": "adjustRefundMoney",
    },
    primary_field_id="f04Gwj",
    log_label="项目结算",
    dry_run_env="PROJECT_SETTLEMENT_SMARTSHEET_DRY_RUN",
    dedupe_prefix="wedoc-project-settlement",
    numeric_fields={"fMqDX0", "fStRfT"},
    multi_text_fields={"f8xImK", "fESKNz", "f28Fkl"},
    identity_keys=("f04Gwj", "ftQMc5", "ftk5Tx", "ffFwIh", "fn8TJd", "signedDate", "f8xImK"),
)

CONTRACT_COMPLETION_SYNC_CONFIG = SmartsheetSyncConfig(
    activity_code="CONTRACT-COMPLETION-SMARTSHEET-SYNC",
    api_url=API_URL_CONTRACT_COMPLETION_SMARTSHEET,
    webhook_url=WECOM_CONTRACT_COMPLETION_SMARTSHEET_WEBHOOK,
    schema={
        "fDeUpD": "合同编号",
        "f2fKLq": "完工日期",
    },
    source_field_map={
        "fDeUpD": "contractdocNum",
        "f2fKLq": "endDateExts",
    },
    primary_field_id="fDeUpD",
    log_label="合同完工",
    dry_run_env="CONTRACT_COMPLETION_SMARTSHEET_DRY_RUN",
    dedupe_prefix="wedoc-contract-completion",
    datetime_fields={"f2fKLq"},
    identity_keys=("fDeUpD", "f2fKLq"),
)

PAYMENT_RECORDS_SYNC_CONFIG = SmartsheetSyncConfig(
    activity_code="PAYMENT-RECORDS-SMARTSHEET-SYNC",
    api_url=API_URL_PAYMENT_RECORDS_SMARTSHEET,
    webhook_url=WECOM_PAYMENT_RECORDS_SMARTSHEET_WEBHOOK,
    schema={
        "fi9MN0": "合同编号",
        "fO4cAe": "本次支付金额",
        "fBaRQ1": "支付时间",
    },
    source_field_map={
        "fi9MN0": "contractCode",
        "fO4cAe": "payPrice",
        "fBaRQ1": "auditstate2Time",
    },
    primary_field_id="fi9MN0",
    log_label="支付记录更新",
    dry_run_env="PAYMENT_RECORDS_SMARTSHEET_DRY_RUN",
    dedupe_prefix="wedoc-payment-records",
    dispatch_delay_seconds=1.5,
    numeric_fields={"fO4cAe"},
    datetime_fields={"fBaRQ1"},
    identity_keys=("fi9MN0", "fO4cAe", "fBaRQ1"),
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


def _normalize_datetime_value(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_get_beijing_tz())
        else:
            dt = dt.astimezone(_get_beijing_tz())
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    text = _stringify(value).replace(",", "")
    if not text:
        return None

    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return text

    try:
        number = float(text)
    except ValueError:
        return text

    if abs(number) >= 1_000_000_000_000:
        seconds = number / 1000.0
    else:
        seconds = number

    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone(_get_beijing_tz())
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _unique_non_empty(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        text = _stringify(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _is_field_id(config: SmartsheetSyncConfig, key: str) -> bool:
    return key in config.schema


def _get_record_value(record: Dict, config: SmartsheetSyncConfig, field_id: str):
    source_field = config.source_field_map.get(field_id, "")
    schema_label = config.schema.get(field_id, "")
    if source_field and record.get(source_field) not in (None, ""):
        return record.get(source_field)
    if schema_label and record.get(schema_label) not in (None, ""):
        return record.get(schema_label)
    return None


def _resolve_identity_value(record: Dict, config: SmartsheetSyncConfig, key: str):
    if _is_field_id(config, key):
        return _get_record_value(record, config, key)
    return record.get(key)


class SmartsheetSyncService:
    """Metabase -> 企业微信电子表格同步服务。"""

    def __init__(
        self,
        storage: PerformanceDataStore,
        sync_config: SmartsheetSyncConfig,
        now: Optional[datetime] = None,
    ):
        self.storage = storage
        self.sync_config = sync_config
        self.now = now or datetime.now()
        self.logger = logging.getLogger(__name__)
        self.activity_code = sync_config.activity_code
        self.dry_run = _is_truthy(os.getenv(sync_config.dry_run_env, ""))
        if not sync_config.webhook_url:
            raise ValueError(f"{sync_config.log_label} webhook 环境变量未设置")

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
            primary_value = values.get(self.sync_config.primary_field_id)
            if not values or not primary_value:
                self.logger.warning(
                    "跳过无效%s记录，缺少主键字段 %s: %s",
                    self.sync_config.log_label,
                    self.sync_config.primary_field_id,
                    record,
                )
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
        self.logger.info("获取%s数据: %s", self.sync_config.log_label, self.sync_config.api_url)
        response = send_request_with_managed_session(self.sync_config.api_url)
        if not response or "data" not in response:
            self.logger.warning("%s接口返回为空或格式异常", self.sync_config.log_label)
            return []

        data = response.get("data", {})
        rows = data.get("rows", []) or []
        cols = data.get("cols", []) or []
        if cols:
            names = [col.get("name") for col in cols]
        else:
            names = _unique_non_empty(list(self.sync_config.source_field_map.values()) + list(self.sync_config.schema.values()))
        return [dict(zip(names, row)) for row in rows]

    def _build_smartsheet_values(self, record: Dict) -> Dict:
        values = {}
        for field_id in self.sync_config.schema:
            raw_value = _get_record_value(record, self.sync_config, field_id)
            if field_id in self.sync_config.multi_text_fields:
                items = _build_multi_text_value(raw_value)
                if items:
                    values[field_id] = items
                continue

            if field_id in self.sync_config.numeric_fields:
                number = _normalize_numeric_value(raw_value)
                if number is not None:
                    values[field_id] = number
                continue

            if field_id in self.sync_config.datetime_fields:
                formatted = _normalize_datetime_value(raw_value)
                if formatted:
                    values[field_id] = formatted
                continue

            text = _stringify(raw_value)
            if text:
                values[field_id] = text
        return values

    def _enqueue_record(self, record: Dict, values: Dict) -> int:
        dedupe_key = self._build_dedupe_key(record)
        primary_value = _stringify(_get_record_value(record, self.sync_config, self.sync_config.primary_field_id))
        payload = {
            "schema": self.sync_config.schema,
            "add_records": [{"values": values}],
        }
        metadata = {
            "primary_value": primary_value,
            "identity_fields": {
                key: _stringify(_resolve_identity_value(record, self.sync_config, key))
                for key in self.sync_config.identity_keys
            },
            "run_marker": self.now.isoformat(),
        }
        return self.storage.enqueue_outbox_message(
            activity_code=self.activity_code,
            contract_id=primary_value or dedupe_key,
            message_type="wedoc_add_record",
            webhook_url=self.sync_config.webhook_url,
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
                    self.logger.warning(
                        "企业微信电子表格 webhook 发送失败: activity=%s, outbox_id=%s, contract=%s, status=%s, body=%s",
                        item.get("activity_code"),
                        item.get("id"),
                        item.get("contract_id"),
                        response.status_code,
                        body_text,
                    )
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
            time.sleep(self.sync_config.dispatch_delay_seconds)
        return stats

    def _log_dry_run_preview(self, eligible_records: List[Tuple[Dict, Dict]]) -> None:
        for record, values in eligible_records[:10]:
            self.logger.info(
                "[DRY RUN] %s记录将写入电子表格: primary=%s, values=%s",
                self.sync_config.log_label,
                _stringify(_get_record_value(record, self.sync_config, self.sync_config.primary_field_id)),
                json.dumps(values, ensure_ascii=False),
            )

    def _build_dedupe_key(self, record: Dict) -> str:
        identity_parts = [
            _stringify(_resolve_identity_value(record, self.sync_config, key))
            for key in self.sync_config.identity_keys
        ]
        raw = "::".join(identity_parts)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
        return f"{self.sync_config.dedupe_prefix}::{raw}::{digest}"

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


class ProjectSettlementSmartsheetService(SmartsheetSyncService):
    """兼容旧名称的项目结算同步服务。"""

    def __init__(self, storage: PerformanceDataStore, now: Optional[datetime] = None):
        super().__init__(storage=storage, sync_config=PROJECT_SETTLEMENT_SYNC_CONFIG, now=now)


def _sync_smartsheet_task(sync_config: SmartsheetSyncConfig, now: Optional[datetime] = None) -> Dict[str, int]:
    storage = create_data_store(storage_type="sqlite", db_path="performance_data.db")
    service = SmartsheetSyncService(storage=storage, sync_config=sync_config, now=now)
    stats = service.run()
    logging.info("%s电子表格同步完成: %s", sync_config.log_label, stats)
    return stats


def sync_project_settlement_smartsheet_v2(now: Optional[datetime] = None) -> Dict[str, int]:
    return _sync_smartsheet_task(PROJECT_SETTLEMENT_SYNC_CONFIG, now=now)


def sync_contract_completion_smartsheet_v2(now: Optional[datetime] = None) -> Dict[str, int]:
    return _sync_smartsheet_task(CONTRACT_COMPLETION_SYNC_CONFIG, now=now)


def sync_payment_records_smartsheet_v2(now: Optional[datetime] = None) -> Dict[str, int]:
    return _sync_smartsheet_task(PAYMENT_RECORDS_SYNC_CONFIG, now=now)


def sync_project_settlement_smartsheet() -> Dict[str, int]:
    return sync_project_settlement_smartsheet_v2()
