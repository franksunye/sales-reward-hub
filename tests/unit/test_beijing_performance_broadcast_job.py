import unittest
import os
import json
import tempfile
from datetime import datetime
from importlib import reload

from modules.core.beijing_jobs import (
    _apply_latest_housekeeper_conversion_rate,
    _get_bj_performance_broadcast_activity_code,
    _parse_metabase_response,
)
from modules.core.data_models import City, ProcessingConfig
from modules.core.notification_service import NotificationService
from modules.core.processing_pipeline import DataProcessingPipeline
from modules.core.storage import SQLitePerformanceDataStore


class BeijingPerformanceBroadcastJobTest(unittest.TestCase):
    def test_parse_2084_response_maps_adjust_refund_money_as_performance_field(self):
        response = {
            "data": {
                "cols": [
                    {"name": "_id"},
                    {"name": "serviceHousekeeper"},
                    {"name": "contractdocNum"},
                    {"name": "adjustRefundMoney"},
                    {"name": "paidAmount"},
                    {"name": "signedDate"},
                    {"name": "sourceType"},
                    {"name": "afterRefundMoney"},
                    {"name": "scount"},
                    {"name": "ccount"},
                    {"name": "conversionRate"},
                ],
                "rows": [
                    [
                        "contract-1",
                        "刘沐泽",
                        "YHWX-BJ-JSJZ-2026050029",
                        50000,
                        18000,
                        "2026-05-11T10:17:08.317+08:00",
                        "2",
                        36000,
                        27,
                        6,
                        0.2222222222222222,
                    ]
                ],
            }
        }

        records = _parse_metabase_response(response)

        self.assertEqual(records[0]["计入业绩金额"], 50000)
        self.assertEqual(records[0]["转化率(conversion)"], 0.2222222222222222)
        self.assertEqual(records[0]["个人累计签约单数"], 6)

    def test_activity_code_uses_beijing_month(self):
        self.assertEqual(
            _get_bj_performance_broadcast_activity_code(datetime(2026, 5, 11)),
            "BJ-PERFORMANCE-BROADCAST-2026-05",
        )

    def test_performance_broadcast_uses_latest_housekeeper_conversion_rate(self):
        records = [
            {
                "合同ID(_id)": "old",
                "管家(serviceHousekeeper)": "刘沐泽",
                "签约时间(signedDate)": "2026-05-02T09:27:18.774+08:00",
                "转化率(conversion)": 0.18,
            },
            {
                "合同ID(_id)": "latest",
                "管家(serviceHousekeeper)": "刘沐泽",
                "签约时间(signedDate)": "2026-05-11T10:17:08.317+08:00",
                "转化率(conversion)": 0.2222222222222222,
            },
        ]

        updated = _apply_latest_housekeeper_conversion_rate(records)

        self.assertEqual(updated[0]["转化率(conversion)"], 0.2222222222222222)
        self.assertEqual(updated[1]["转化率(conversion)"], 0.2222222222222222)

    def test_performance_broadcast_message_format_and_webhook_channel(self):
        config = ProcessingConfig(
            config_key="BJ-PERFORMANCE-BROADCAST",
            activity_code="BJ-PERFORMANCE-BROADCAST-2026-05",
            city=City.BEIJING,
            housekeeper_key_format="管家",
        )
        service = NotificationService(storage=None, config=config)
        record = {
            "合同ID(_id)": "contract-1",
            "管家(serviceHousekeeper)": "刘沐泽",
            "合同编号(contractdocNum)": "YHWX-BJ-JSJZ-2026050029",
            "计入业绩金额": 16900,
            "管家累计业绩金额": 75799,
            "转化率(conversion)": 0.2222222222222222,
            "是否发送通知": "N",
        }

        msg = service._build_group_notification_message(record)

        self.assertIn("恭喜 刘沐泽 签约合同 YHWX-BJ-JSJZ-2026050029 并完成首付款支付条件", msg)
        self.assertIn("本合同计入业绩金额为16900，本月个人累计签约业绩 75,799 元", msg)
        self.assertIn("🌻 当前全年平台转化率为22%", msg)
        os.environ["WECOM_WEBHOOK_BJ_PERFORMANCE_BROADCAST"] = "https://example.com/bj-performance-broadcast"
        from modules import config as config_module
        from modules.core import webhook_router as webhook_router_module
        reload(config_module)
        reload(webhook_router_module)

        self.assertEqual(
            webhook_router_module.resolve_wecom_webhook(webhook_router_module.CHANNEL_BJ_PERFORMANCE_BROADCAST),
            "https://example.com/bj-performance-broadcast",
        )

    def test_performance_broadcast_refreshes_existing_contract_snapshot(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            store = SQLitePerformanceDataStore(tmp.name)
            activity_code = "BJ-PERFORMANCE-BROADCAST-2026-05"
            config = ProcessingConfig(
                config_key="BJ-PERFORMANCE-BROADCAST",
                activity_code=activity_code,
                city=City.BEIJING,
                housekeeper_key_format="管家",
            )

            with store._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO performance_data (
                        activity_code, contract_id, housekeeper, service_provider,
                        contract_amount, performance_amount, order_type, project_id,
                        contract_sequence, reward_types, reward_names, is_historical,
                        notification_sent, remarks, extensions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        activity_code,
                        "4094726635973593636",
                        "李俊达",
                        "",
                        24000,
                        15000,
                        "platform",
                        "GD2026040513",
                        1,
                        "[]",
                        "[]",
                        0,
                        1,
                        "无",
                        json.dumps({"管家累计业绩金额": 15000}, ensure_ascii=False),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO performance_data (
                        activity_code, contract_id, housekeeper, service_provider,
                        contract_amount, performance_amount, order_type, project_id,
                        contract_sequence, reward_types, reward_names, is_historical,
                        notification_sent, remarks, extensions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        activity_code,
                        "missing-from-source",
                        "李俊达",
                        "",
                        9000,
                        9000,
                        "platform",
                        "GD-OLD",
                        2,
                        "[]",
                        "[]",
                        0,
                        1,
                        "无",
                        "{}",
                    ),
                )

            pipeline = DataProcessingPipeline(config, store)
            pipeline.process([
                {
                    "合同ID(_id)": "4094726635973593636",
                    "管家(serviceHousekeeper)": "李俊达",
                    "合同编号(contractdocNum)": "YHWX-BJ-JSJZ-2026040024",
                    "合同金额(adjustRefundMoney)": 24000,
                    "计入业绩金额": 24000,
                    "支付金额(paidAmount)": 24000,
                    "工单编号(serviceAppointmentNum)": "GD2026040513",
                    "签约时间(signedDate)": "2026-04-03T20:00:14.471+08:00",
                    "工单类型(sourceType)": "2",
                },
                {
                    "合同ID(_id)": "new-contract",
                    "管家(serviceHousekeeper)": "李俊达",
                    "合同编号(contractdocNum)": "YHWX-BJ-JSJZ-2026050002",
                    "合同金额(adjustRefundMoney)": 1000,
                    "计入业绩金额": 1000,
                    "支付金额(paidAmount)": 1000,
                    "工单编号(serviceAppointmentNum)": "GD2026050002",
                    "签约时间(signedDate)": "2026-05-03T10:46:30.383+08:00",
                    "工单类型(sourceType)": "2",
                },
            ])

            rows = {row["contract_id"]: row for row in store.get_all_records(activity_code)}
            refreshed = rows["4094726635973593636"]
            new_row_extensions = json.loads(rows["new-contract"]["extensions"])

            self.assertNotIn("missing-from-source", rows)
            self.assertEqual(refreshed["performance_amount"], 24000)
            self.assertEqual(refreshed["notification_sent"], 1)
            self.assertEqual(new_row_extensions["管家累计业绩金额"], 25000)


if __name__ == "__main__":
    unittest.main()
