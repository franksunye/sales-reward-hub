import json
import os
import sqlite3
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

try:
    from zoneinfo import ZoneInfo
    BEIJING_TZ = ZoneInfo("Asia/Shanghai")
except Exception:  # pragma: no cover - fallback for environments without tzdata
    BEIJING_TZ = timezone.utc


def _ms_for_naive_beijing(text: str) -> str:
    """Helper: build the millisecond timestamp string the service should emit
    for a naive Beijing-local datetime string."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=BEIJING_TZ)
            return str(int(dt.timestamp() * 1000))
        except ValueError:
            continue
    raise ValueError(f"unsupported datetime literal: {text}")


if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")
    requests_exceptions_stub = types.ModuleType("requests.exceptions")

    class _RequestException(Exception):
        pass

    class _Timeout(_RequestException):
        pass

    requests_stub.post = MagicMock()
    requests_stub.RequestException = _RequestException
    requests_exceptions_stub.Timeout = _Timeout
    sys.modules["requests"] = requests_stub
    sys.modules["requests.exceptions"] = requests_exceptions_stub

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub


os.environ.setdefault("CONTACT_PHONE_NUMBER", "13800000000")
os.environ.setdefault("METABASE_USERNAME", "test@example.com")
os.environ.setdefault("METABASE_PASSWORD", "test-password")
os.environ.setdefault("WECOM_WEBHOOK_DEFAULT", "https://example.com/default")
os.environ.setdefault("WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT", "https://example.com/sign-broadcast")
os.environ.setdefault("WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK", "https://example.com/wedoc")
os.environ.setdefault("WECOM_CONTRACT_COMPLETION_SMARTSHEET_WEBHOOK", "https://example.com/wedoc-contract-completion")
os.environ.setdefault("WECOM_PAYMENT_RECORDS_SMARTSHEET_WEBHOOK", "https://example.com/wedoc-payment-records")
os.environ.setdefault("DB_SOURCE", "local")

from modules.core.project_settlement_jobs import CONTRACT_COMPLETION_SYNC_CONFIG
from modules.core.project_settlement_jobs import PAYMENT_RECORDS_SYNC_CONFIG
from modules.core.project_settlement_jobs import ProjectSettlementSmartsheetService
from modules.core.project_settlement_jobs import SmartsheetSyncService
from modules.core.storage import create_data_store


class ProjectSettlementSmartsheetJobTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "project-settlement-smartsheet.db")
        os.environ["LOCAL_DB_PATH"] = self.db_path
        os.environ.pop("PROJECT_SETTLEMENT_SMARTSHEET_DRY_RUN", None)
        self.storage = create_data_store(storage_type="sqlite", db_path=self.db_path)
        self.now = datetime(2026, 4, 15, 10, 0, 0)

    def tearDown(self):
        os.environ.pop("PROJECT_SETTLEMENT_SMARTSHEET_DRY_RUN", None)
        self.temp_dir.cleanup()

    def _response(self, rows):
        cols = [{"name": name} for name in [
            "合同编号", "项目施工地址", "业主姓名", "联系电话", "serviceHousekeeper", "部位", "进场日期", "完工日期",
            "项目用工数", "班组名称", "是否发起预结单", "结算状态", "合同金额",
        ]]
        return {"data": {"cols": cols, "rows": rows}}

    def _row(self, contract_no="HT001", team_name="刘振海", settle_status="已发起", housekeeper="王管家"):
        return [
            contract_no,
            "北京市朝阳区测试地址",
            "张三",
            "13800138000",
            housekeeper,
            "客厅",
            "2026-04-01",
            "2026-04-10",
            "3",
            team_name,
            "已发起",
            settle_status,
            "9999",
        ]

    def test_first_run_sends_new_records_with_expected_payload(self):
        response = self._response([self._row("HT001"), self._row("HT002", team_name="李四")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            stats = ProjectSettlementSmartsheetService(self.storage, now=self.now).run()

        self.assertEqual(stats["raw_records"], 2)
        self.assertEqual(stats["eligible_records"], 2)
        self.assertEqual(stats["sent"], 2)
        self.assertEqual(mock_post.call_count, 2)

        first_payload = mock_post.call_args_list[0].kwargs["json"]
        self.assertIn("schema", first_payload)
        self.assertEqual(first_payload["schema"]["f04Gwj"], "合同编号")
        self.assertEqual(first_payload["schema"]["foyhkS"], "管家")
        values = first_payload["add_records"][0]["values"]
        self.assertEqual(values["f04Gwj"], "HT001")
        self.assertEqual(values["foyhkS"], "王管家")
        self.assertEqual(values["fMqDX0"], 3)
        self.assertEqual(values["f8xImK"], [{"text": "刘振海"}])
        self.assertEqual(values["fESKNz"], [{"text": "已发起"}])

        with sqlite3.connect(self.db_path) as conn:
            outbox_rows = conn.execute(
                "SELECT message_type, status FROM notification_outbox ORDER BY id"
            ).fetchall()
        self.assertEqual(outbox_rows, [("wedoc_add_record", "sent"), ("wedoc_add_record", "sent")])

    def test_second_run_does_not_resend_same_identity_record(self):
        response = self._response([self._row("HT001", settle_status="已发起")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            service = ProjectSettlementSmartsheetService(self.storage, now=self.now)
            first_stats = service.run()
            service.now = datetime(2026, 4, 15, 10, 30, 0)
            second_stats = service.run()

        self.assertEqual(first_stats["sent"], 1)
        self.assertEqual(second_stats["sent"], 0)
        self.assertEqual(mock_post.call_count, 1)

        with sqlite3.connect(self.db_path) as conn:
            outbox_total = conn.execute(
                "SELECT COUNT(*) FROM notification_outbox WHERE message_type = 'wedoc_add_record'"
            ).fetchone()[0]
        self.assertEqual(outbox_total, 1)

    def test_same_identity_with_changed_status_does_not_create_new_add_record(self):
        first_response = self._response([self._row("HT001", settle_status="已发起")])
        second_response = self._response([self._row("HT001", settle_status="已结算")])

        with patch(
            "modules.core.project_settlement_jobs.send_request_with_managed_session",
            side_effect=[first_response, second_response],
        ), patch("modules.core.project_settlement_jobs.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            service = ProjectSettlementSmartsheetService(self.storage, now=self.now)
            service.run()
            service.now = datetime(2026, 4, 15, 11, 0, 0)
            second_stats = service.run()

        self.assertEqual(second_stats["sent"], 0)
        self.assertEqual(mock_post.call_count, 1)

        with sqlite3.connect(self.db_path) as conn:
            stored_payload = conn.execute(
                "SELECT payload_json FROM notification_outbox WHERE message_type = 'wedoc_add_record' LIMIT 1"
            ).fetchone()[0]
        payload = json.loads(stored_payload)
        self.assertEqual(payload["add_records"][0]["values"]["f28Fkl"], [{"text": "已发起"}])

    def test_dry_run_previews_without_sending(self):
        os.environ["PROJECT_SETTLEMENT_SMARTSHEET_DRY_RUN"] = "1"
        response = self._response([self._row("HT001")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            stats = ProjectSettlementSmartsheetService(self.storage, now=self.now).run()

        self.assertEqual(stats["dry_run"], 1)
        self.assertEqual(stats["eligible_records"], 1)
        self.assertEqual(stats["sent"], 0)
        mock_post.assert_not_called()


class ContractCompletionSmartsheetJobTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "contract-completion-smartsheet.db")
        os.environ["LOCAL_DB_PATH"] = self.db_path
        os.environ.pop("CONTRACT_COMPLETION_SMARTSHEET_DRY_RUN", None)
        self.storage = create_data_store(storage_type="sqlite", db_path=self.db_path)
        self.now = datetime(2026, 4, 15, 10, 0, 0)

    def tearDown(self):
        os.environ.pop("CONTRACT_COMPLETION_SMARTSHEET_DRY_RUN", None)
        self.temp_dir.cleanup()

    def _response(self, rows):
        cols = [{"name": name} for name in ["contractdocNum", "endDateExts"]]
        return {"data": {"cols": cols, "rows": rows}}

    def _row(self, contract_no="HT001", end_date="2026-04-12"):
        return [contract_no, end_date]

    def test_first_run_sends_completion_payload(self):
        response = self._response([self._row("HT001"), self._row("HT002", "2026-04-13")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            stats = SmartsheetSyncService(
                storage=self.storage,
                sync_config=CONTRACT_COMPLETION_SYNC_CONFIG,
                now=self.now,
            ).run()

        self.assertEqual(stats["raw_records"], 2)
        self.assertEqual(stats["sent"], 2)
        first_payload = mock_post.call_args_list[0].kwargs["json"]
        values = first_payload["add_records"][0]["values"]
        self.assertEqual(first_payload["schema"], CONTRACT_COMPLETION_SYNC_CONFIG.schema)
        self.assertEqual(values["fDeUpD"], "HT001")
        # WeCom smartsheet 日期字段要求毫秒 unix 时间戳字符串
        self.assertEqual(values["f2fKLq"], _ms_for_naive_beijing("2026-04-12"))

    def test_timestamp_value_is_normalized_for_completion_date(self):
        response = self._response([self._row("HT001", "1735660800000")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            stats = SmartsheetSyncService(
                storage=self.storage,
                sync_config=CONTRACT_COMPLETION_SYNC_CONFIG,
                now=self.now,
            ).run()

        self.assertEqual(stats["raw_records"], 1)
        self.assertEqual(stats["sent"], 1)
        first_payload = mock_post.call_args_list[0].kwargs["json"]
        values = first_payload["add_records"][0]["values"]
        # 入参已经是毫秒时间戳字符串，原样下发即可
        self.assertEqual(values["f2fKLq"], "1735660800000")

    def test_metabase_nested_column_name_is_resolved_via_display_name(self):
        # Metabase 对嵌套 JSON 字段会把 cols[i].name 返回 "exts.endDateExts"，
        # 同时把 display_name 返回 "endDateExts"。之前只用 name 作为 record key，
        # 会导致 source_field_map 中配置的 "endDateExts" 永远取不到值，
        # 电子表格里合同编号写进去了但 "完工日期" 一直为空。
        cols = [
            {"name": "contractdocNum", "display_name": "contractdocNum"},
            {"name": "exts.endDateExts", "display_name": "endDateExts"},
        ]
        response = {"data": {"cols": cols, "rows": [["HT001", "2026-03-27"]]}}

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            stats = SmartsheetSyncService(
                storage=self.storage,
                sync_config=CONTRACT_COMPLETION_SYNC_CONFIG,
                now=self.now,
            ).run()

        self.assertEqual(stats["raw_records"], 1)
        self.assertEqual(stats["sent"], 1)
        values = mock_post.call_args_list[0].kwargs["json"]["add_records"][0]["values"]
        self.assertEqual(values["fDeUpD"], "HT001")
        self.assertEqual(values["f2fKLq"], _ms_for_naive_beijing("2026-03-27"))

    def test_second_run_does_not_resend_same_completion_record(self):
        response = self._response([self._row("HT001", "2026-04-12")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            service = SmartsheetSyncService(
                storage=self.storage,
                sync_config=CONTRACT_COMPLETION_SYNC_CONFIG,
                now=self.now,
            )
            first_stats = service.run()
            service.now = datetime(2026, 4, 15, 10, 30, 0)
            second_stats = service.run()

        self.assertEqual(first_stats["sent"], 1)
        self.assertEqual(second_stats["sent"], 0)
        self.assertEqual(mock_post.call_count, 1)


class PaymentRecordsSmartsheetJobTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "payment-records-smartsheet.db")
        os.environ["LOCAL_DB_PATH"] = self.db_path
        os.environ.pop("PAYMENT_RECORDS_SMARTSHEET_DRY_RUN", None)
        self.storage = create_data_store(storage_type="sqlite", db_path=self.db_path)
        self.now = datetime(2026, 4, 15, 10, 0, 0)

    def tearDown(self):
        os.environ.pop("PAYMENT_RECORDS_SMARTSHEET_DRY_RUN", None)
        self.temp_dir.cleanup()

    def _response(self, rows):
        cols = [{"name": name} for name in ["contractCode", "payPrice", "auditstate2Time"]]
        return {"data": {"cols": cols, "rows": rows}}

    def _row(self, contract_no="HT001", pay_price="1200.5", pay_time="1735660800000"):
        return [contract_no, pay_price, pay_time]

    def test_first_run_sends_payment_payload(self):
        response = self._response([self._row("HT001"), self._row("HT002", "800", "2026-04-13 09:00:00")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            stats = SmartsheetSyncService(
                storage=self.storage,
                sync_config=PAYMENT_RECORDS_SYNC_CONFIG,
                now=self.now,
            ).run()

        self.assertEqual(stats["raw_records"], 2)
        self.assertEqual(stats["sent"], 2)
        first_payload = mock_post.call_args_list[0].kwargs["json"]
        values = first_payload["add_records"][0]["values"]
        self.assertEqual(first_payload["schema"], PAYMENT_RECORDS_SYNC_CONFIG.schema)
        self.assertEqual(values["fi9MN0"], "HT001")
        self.assertEqual(values["fO4cAe"], 1200.5)
        # 入参是毫秒时间戳字符串，服务端按 WeCom 要求原样下发
        self.assertEqual(values["fBaRQ1"], "1735660800000")
        second_values = mock_post.call_args_list[1].kwargs["json"]["add_records"][0]["values"]
        self.assertEqual(
            second_values["fBaRQ1"],
            _ms_for_naive_beijing("2026-04-13 09:00:00"),
        )

    def test_pay_time_is_always_emitted_as_millisecond_timestamp_string(self):
        # 回归 errcode 2022034 (Smartsheet invalid date time value):
        # WeCom smartsheet FIELD_TYPE_DATE_TIME 要求毫秒 unix 时间戳字符串，
        # 不能下发 "YYYY-MM-DD HH:MM:SS" 这种本地时间格式。
        response = self._response([self._row("HT001", "5350", "2026-04-16 20:13:28")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":0}')
            SmartsheetSyncService(
                storage=self.storage,
                sync_config=PAYMENT_RECORDS_SYNC_CONFIG,
                now=self.now,
            ).run()

        values = mock_post.call_args_list[0].kwargs["json"]["add_records"][0]["values"]
        pay_time = values["fBaRQ1"]
        self.assertIsInstance(pay_time, str)
        self.assertTrue(pay_time.lstrip("-").isdigit(), f"expected unix ms ts, got {pay_time!r}")
        self.assertEqual(pay_time, _ms_for_naive_beijing("2026-04-16 20:13:28"))

    def test_failed_payment_webhook_is_marked_as_failed(self):
        response = self._response([self._row("HT001")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text='{"errcode":40013, "errmsg":"invalid appid"}')
            stats = SmartsheetSyncService(
                storage=self.storage,
                sync_config=PAYMENT_RECORDS_SYNC_CONFIG,
                now=self.now,
            ).run()

        self.assertEqual(stats["raw_records"], 1)
        self.assertEqual(stats["sent"], 0)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(mock_post.call_count, 1)

    def test_missing_contract_number_is_skipped(self):
        response = self._response([self._row("", "1200.5", "2026-04-12 10:20:30")])

        with patch("modules.core.project_settlement_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.project_settlement_jobs.requests.post"
        ) as mock_post:
            stats = SmartsheetSyncService(
                storage=self.storage,
                sync_config=PAYMENT_RECORDS_SYNC_CONFIG,
                now=self.now,
            ).run()

        self.assertEqual(stats["eligible_records"], 0)
        self.assertEqual(stats["sent"], 0)
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
