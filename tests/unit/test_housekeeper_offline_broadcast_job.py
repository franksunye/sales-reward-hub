import json
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from modules.core.housekeeper_offline_jobs import (
    HousekeeperOfflineBroadcastService,
    _event_fingerprint,
    _format_housekeeper_offline_message,
    _parse_metabase_records,
)
from modules.core.storage import SQLitePerformanceDataStore


class HousekeeperOfflineBroadcastJobTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 1, 9, 30, tzinfo=timezone.utc)
        self.response = {
            "data": {
                "cols": [
                    {"name": "eventId", "display_name": "事件ID"},
                    {"name": "createTime"},
                    {"name": "createUserName"},
                    {"name": "动作"},
                ],
                "rows": [["event-1", "2026-07-01T17:19:09.72+08:00", "张三", ["下线"]]],
            }
        }

    def test_parse_and_format(self):
        records = _parse_metabase_records(self.response)

        self.assertEqual(records[0]["createUserName"], "张三")
        self.assertEqual(records[0]["事件ID"], "event-1")
        self.assertEqual(
            _format_housekeeper_offline_message(
                "张三",
                "下线",
                datetime(2026, 7, 1, 9, 19, 9, tzinfo=timezone.utc),
            ),
            "管家【张三】于【2026-07-01 17:19:09】【下线】了。",
        )
        self.assertEqual(
            _format_housekeeper_offline_message(
                "李四",
                "上线",
                datetime(2026, 7, 1, 10, 5, tzinfo=timezone.utc),
            ),
            "管家【李四】于【2026-07-01 18:05:00】【上线】了。",
        )

    def test_full_source_row_distinguishes_repeated_operations(self):
        records = _parse_metabase_records({
            "data": {
                "cols": self.response["data"]["cols"],
                "rows": [
                    ["event-1", "2026-07-01T17:19:09.72+08:00", "张三", ["下线"]],
                    ["event-2", "2026-07-01T17:20:09.72+08:00", "张三", ["下线"]],
                ],
            }
        })
        self.assertNotEqual(_event_fingerprint(records[0]), _event_fingerprint(records[1]))

    def test_run_sends_once_and_deduplicates_next_poll(self):
        fake_response = Mock(status_code=200, text='{"errcode":0,"errmsg":"ok"}')
        fake_response.json.return_value = {"errcode": 0, "errmsg": "ok"}

        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = SQLitePerformanceDataStore(tmp.name)
            service = HousekeeperOfflineBroadcastService(store, now=self.now)
            with patch("modules.core.housekeeper_offline_jobs.send_request_with_managed_session", return_value=self.response), patch(
                "modules.core.housekeeper_offline_jobs.resolve_wecom_webhook", return_value="https://example.com/offline"
            ), patch("modules.core.housekeeper_offline_jobs.requests.post", return_value=fake_response) as post:
                first = service.run()
                second = service.run()

        self.assertEqual(first["sent"], 1)
        self.assertEqual(second["sent"], 0)
        self.assertEqual(post.call_count, 1)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(
            payload,
            {
                "msgtype": "text",
                "text": {"content": "管家【张三】于【2026-07-01 17:19:09】【下线】了。"},
            },
        )

    def test_wecom_business_error_is_retryable_failure(self):
        fake_response = Mock(status_code=200, text='{"errcode":93000,"errmsg":"invalid webhook"}')
        fake_response.json.return_value = {"errcode": 93000, "errmsg": "invalid webhook"}

        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = SQLitePerformanceDataStore(tmp.name)
            service = HousekeeperOfflineBroadcastService(store, now=self.now)
            with patch("modules.core.housekeeper_offline_jobs.send_request_with_managed_session", return_value=self.response), patch(
                "modules.core.housekeeper_offline_jobs.resolve_wecom_webhook", return_value="https://example.com/offline"
            ), patch("modules.core.housekeeper_offline_jobs.requests.post", return_value=fake_response):
                stats = service.run()
                failed = store.get_retryable_outbox_messages(service.activity_code, max_attempts=5)

        self.assertEqual(stats["failed"], 1)
        self.assertEqual(failed[0]["status"], "failed")
        self.assertIn("invalid webhook", failed[0]["last_error"])

    def test_historical_rows_are_not_replayed_on_first_run(self):
        self.response["data"]["rows"].append(
            ["old-event", "2025-09-23T14:38:34.48+08:00", "李四", ["下线"]]
        )
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = SQLitePerformanceDataStore(tmp.name)
            service = HousekeeperOfflineBroadcastService(store, now=self.now)
            with patch("modules.core.housekeeper_offline_jobs.send_request_with_managed_session", return_value=self.response), patch(
                "modules.core.housekeeper_offline_jobs.resolve_wecom_webhook", return_value="https://example.com/offline"
            ), patch("modules.core.housekeeper_offline_jobs.requests.post") as post:
                service.dry_run = True
                stats = service.run()

        self.assertEqual(stats["raw_events"], 2)
        self.assertEqual(stats["valid_events"], 1)
        self.assertEqual(stats["stale_events"], 1)
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
