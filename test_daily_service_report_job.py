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
os.environ.setdefault(
    "WECOM_WEBHOOK_PENDING_ORDERS_ORG_MAP",
    '{"服务商A":"https://example.com/a","服务商B":"https://example.com/b"}',
)
os.environ.setdefault("DB_SOURCE", "local")

from modules.core.sla_jobs import DailyServiceReportService
from modules.core.storage import create_data_store


class DailyServiceReportJobTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "daily-service-report.db")
        os.environ["LOCAL_DB_PATH"] = self.db_path
        os.environ.pop("DAILY_SERVICE_REPORT_DRY_RUN", None)
        self.storage = create_data_store(storage_type="sqlite", db_path=self.db_path)

    def tearDown(self):
        os.environ.pop("DAILY_SERVICE_REPORT_DRY_RUN", None)
        self.temp_dir.cleanup()

    def _response(self, rows):
        cols = [{"name": name} for name in [
            "_id", "sid", "saCreateTime", "orderNum", "province", "orgName",
            "supervisorName", "sourceType", "status", "msg", "memo", "workType", "createTime"
        ]]
        return {"data": {"cols": cols, "rows": rows}}

    def _row(self, order_num="GD001", org_name="服务商A", violation_type="超时", memo="超时详情"):
        return [
            f"id-{order_num}",
            f"sid-{order_num}",
            "2026-03-29T09:38:53+08:00",
            order_num,
            "110000",
            org_name,
            "管家A",
            5,
            201,
            violation_type,
            memo,
            1,
            "2026-03-29T03:02:00.17+08:00",
        ]

    def test_daily_run_sends_daily_violations_and_stores_snapshot(self):
        response = self._response([self._row("GD001", "服务商A"), self._row("GD002", "服务商A")])
        now = datetime(2026, 3, 31, 8, 10)  # Tuesday in Beijing

        with patch("modules.core.sla_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.sla_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text="ok")
            stats = DailyServiceReportService(self.storage, now=now).run()

        self.assertEqual(stats["raw_records"], 2)
        self.assertEqual(stats["stored_records"], 2)
        self.assertEqual(stats["daily_enqueued"], 2)
        self.assertEqual(stats["sent"], 2)
        self.assertEqual(mock_post.call_count, 2)

        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM sla_violation_records").fetchone()[0]
            outbox_count = conn.execute("SELECT COUNT(*) FROM notification_outbox").fetchone()[0]
        self.assertEqual(count, 2)
        self.assertEqual(outbox_count, 2)

    def test_second_run_does_not_resend_same_daily_records(self):
        response = self._response([self._row("GD001", "服务商A")])
        now = datetime(2026, 3, 31, 8, 10)

        with patch("modules.core.sla_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.sla_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text="ok")
            service = DailyServiceReportService(self.storage, now=now)
            first = service.run()
            second = service.run()

        self.assertEqual(first["sent"], 1)
        self.assertEqual(second["sent"], 0)
        self.assertEqual(mock_post.call_count, 1)

    def test_monday_run_sends_weekly_reports(self):
        self.storage.replace_sla_violations_for_date(
            "2026-03-23",
            [{
                "_id": "id-1",
                "sid": "sid-1",
                "saCreateTime": "2026-03-23T09:38:53+08:00",
                "orderNum": "GD100",
                "province": "110000",
                "orgName": "服务商A",
                "supervisorName": "管家A",
                "sourceType": 5,
                "status": 201,
                "msg": "超时",
                "memo": "超时详情",
                "workType": 1,
                "createTime": "2026-03-23T03:02:00.17+08:00",
            }]
        )
        response = self._response([])
        now = datetime(2026, 3, 30, 8, 10)  # Monday in Beijing

        with patch("modules.core.sla_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.sla_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text="ok")
            stats = DailyServiceReportService(self.storage, now=now).run()

        self.assertEqual(stats["weekly_enqueued"], 2)
        self.assertEqual(stats["sent"], 2)
        self.assertEqual(mock_post.call_count, 2)

    def test_dry_run_generates_preview_without_sending(self):
        os.environ["DAILY_SERVICE_REPORT_DRY_RUN"] = "1"
        response = self._response([self._row("GD001", "服务商A")])
        now = datetime(2026, 3, 31, 8, 10)

        with patch("modules.core.sla_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.sla_jobs.requests.post"
        ) as mock_post:
            stats = DailyServiceReportService(self.storage, now=now).run()

        self.assertEqual(stats["dry_run"], 1)
        self.assertEqual(stats["sent"], 0)
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
