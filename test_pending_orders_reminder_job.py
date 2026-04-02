import os
import sqlite3
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from importlib import reload
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
os.environ.setdefault(
    "WECOM_WEBHOOK_PENDING_ORDERS_ORG_MAP",
    '{"北京经常亮工程技术有限公司":"https://example.com/pending-provider-a"}',
)
os.environ.setdefault("DB_SOURCE", "local")

from modules.core.pending_orders_jobs import PendingOrdersReminderService
from modules.core.storage import create_data_store
from modules.core.webhook_router import (
    CHANNEL_PENDING_ORDERS,
    CHANNEL_SIGN_BROADCAST,
    resolve_wecom_webhook,
)


class PendingOrdersReminderJobTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "pending-orders-test.db")
        os.environ["LOCAL_DB_PATH"] = self.db_path
        self.storage = create_data_store(storage_type="sqlite", db_path=self.db_path)
        self.now = datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        os.environ.pop("PENDING_ORDERS_DRY_RUN", None)
        self.temp_dir.cleanup()

    def _build_response(self, rows):
        return {"data": {"rows": rows}}

    def _row(self, order_num, hours_ago, org_name="测试服务商", status="待预约"):
        create_time = (self.now - timedelta(hours=hours_ago)).isoformat()
        return [
            order_num,
            f"客户-{order_num}",
            f"地址-{order_num}",
            f"负责人-{order_num}",
            create_time,
            org_name,
            status,
        ]

    def test_first_run_filters_and_sends_only_eligible_orders(self):
        rows = [
            self._row("A001", 72, org_name="测试服务商A", status="待预约"),
            self._row("A002", 24, org_name="测试服务商A", status="待预约"),
            self._row("B001", 80, org_name="测试服务商B", status="暂不上门"),
        ]
        response = self._build_response(rows)

        with patch("modules.core.pending_orders_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.pending_orders_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text="ok")
            service = PendingOrdersReminderService(self.storage, now=self.now)
            stats = service.run()

        self.assertEqual(stats["raw_orders"], 3)
        self.assertEqual(stats["eligible_orders"], 2)
        self.assertEqual(stats["orgs_with_new_orders"], 2)
        self.assertEqual(stats["sent"], 2)
        self.assertEqual(mock_post.call_count, 2)

        with sqlite3.connect(self.db_path) as conn:
            reminder_rows = conn.execute(
                "SELECT org_name, notification_sent, is_active FROM pending_order_reminders ORDER BY org_name"
            ).fetchall()
            outbox_rows = conn.execute(
                "SELECT message_type, status FROM notification_outbox ORDER BY id"
            ).fetchall()

        self.assertEqual(reminder_rows, [("测试服务商A", 1, 1), ("测试服务商B", 1, 1)])
        self.assertEqual(outbox_rows, [("pending_orders_digest", "sent"), ("pending_orders_digest", "sent")])

    def test_second_run_with_same_snapshot_resends_active_orders(self):
        rows = [self._row("A001", 72, org_name="测试服务商A", status="待预约")]
        response = self._build_response(rows)

        with patch(
            "modules.core.pending_orders_jobs.send_request_with_managed_session",
            return_value=response,
        ), patch(
            "modules.core.pending_orders_jobs.requests.post"
        ) as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text="ok")
            service = PendingOrdersReminderService(self.storage, now=self.now)
            first_stats = service.run()
            service.now = self.now + timedelta(minutes=30)
            second_stats = service.run()

        self.assertEqual(first_stats["sent"], 1)
        self.assertEqual(second_stats["sent"], 1)
        self.assertEqual(mock_post.call_count, 2)

        with sqlite3.connect(self.db_path) as conn:
            outbox_total = conn.execute(
                "SELECT COUNT(*) FROM notification_outbox WHERE message_type = 'pending_orders_digest'"
            ).fetchone()[0]
        self.assertEqual(outbox_total, 2)

    def test_existing_org_still_sends_when_new_order_appears(self):
        first_response = self._build_response([self._row("A001", 72, org_name="测试服务商A", status="待预约")])
        second_response = self._build_response(
            [
                self._row("A001", 72, org_name="测试服务商A", status="待预约"),
                self._row("A002", 73, org_name="测试服务商A", status="待预约"),
            ]
        )

        with patch(
            "modules.core.pending_orders_jobs.send_request_with_managed_session",
            side_effect=[first_response, second_response],
        ), patch("modules.core.pending_orders_jobs.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, text="ok")
            service = PendingOrdersReminderService(self.storage, now=self.now)
            service.run()
            service.now = self.now + timedelta(minutes=30)
            second_stats = service.run()

        self.assertEqual(second_stats["orgs_with_new_orders"], 1)
        self.assertEqual(second_stats["sent"], 1)
        self.assertEqual(mock_post.call_count, 2)

        with sqlite3.connect(self.db_path) as conn:
            active_count = conn.execute(
                "SELECT COUNT(*) FROM pending_order_reminders WHERE is_active = 1"
            ).fetchone()[0]
        self.assertEqual(active_count, 2)

    def test_webhook_router_pending_orders_uses_default_webhook_and_org_override(self):
        sign_webhook = resolve_wecom_webhook(CHANNEL_SIGN_BROADCAST)
        pending_default = resolve_wecom_webhook(CHANNEL_PENDING_ORDERS, org_name="未知服务商")
        pending_override = resolve_wecom_webhook(CHANNEL_PENDING_ORDERS, org_name="北京经常亮工程技术有限公司")

        self.assertEqual(sign_webhook, os.environ["WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT"])
        self.assertEqual(pending_default, os.environ["WECOM_WEBHOOK_DEFAULT"])
        self.assertNotEqual(pending_override, pending_default)

    def test_webhook_router_can_force_all_pending_order_messages_to_local_url(self):
        os.environ["WECOM_WEBHOOK_PENDING_ORDERS_FORCE_URL"] = "http://127.0.0.1:8787/pending/all"
        import modules.config as config_module
        from modules.core import webhook_router as webhook_router_module

        reload(config_module)
        reload(webhook_router_module)
        try:
            forced_url = webhook_router_module.resolve_wecom_webhook(
                webhook_router_module.CHANNEL_PENDING_ORDERS,
                org_name="北京经常亮工程技术有限公司",
            )
            self.assertEqual(forced_url, "http://127.0.0.1:8787/pending/all")
        finally:
            os.environ.pop("WECOM_WEBHOOK_PENDING_ORDERS_FORCE_URL", None)
            reload(config_module)
            reload(webhook_router_module)

    def test_dry_run_generates_messages_but_does_not_send(self):
        rows = [self._row("A001", 72, org_name="测试服务商A", status="待预约")]
        response = self._build_response(rows)
        os.environ["PENDING_ORDERS_DRY_RUN"] = "1"

        with patch("modules.core.pending_orders_jobs.send_request_with_managed_session", return_value=response), patch(
            "modules.core.pending_orders_jobs.requests.post"
        ) as mock_post:
            service = PendingOrdersReminderService(self.storage, now=self.now)
            stats = service.run()

        self.assertEqual(stats["dry_run"], 1)
        self.assertEqual(stats["orgs_with_new_orders"], 1)
        self.assertEqual(stats["sent"], 0)
        self.assertEqual(stats["enqueued"], 0)
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
