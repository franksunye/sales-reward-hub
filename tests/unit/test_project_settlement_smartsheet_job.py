import json
import os
import sqlite3
import sys
import tempfile
import types
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch


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
os.environ.setdefault("DB_SOURCE", "local")

from modules.core.project_settlement_jobs import ProjectSettlementSmartsheetService
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
            "项目用工数", "班组名称", "是否发起预结单", "结算状态", "支付金额", "合同金额",
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
            "1200.5",
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
        self.assertEqual(values["f5Cx2q"], 1200.5)
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


if __name__ == "__main__":
    unittest.main()
