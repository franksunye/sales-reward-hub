#!/usr/bin/env python3
"""支付记录智能表格本地一条 E2E 验证。

用法示例：
  .venv/bin/python scripts/local_webhook_sink.py --port 8787
  .venv/bin/python tests/manual/payment_records_smartsheet_local_e2e.py
"""

import argparse
import importlib
import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


def _seed_env(webhook_url: str, db_path: str) -> None:
    os.environ.setdefault("DB_SOURCE", "local")
    os.environ.setdefault("CONTACT_PHONE_NUMBER", "13800000000")
    os.environ.setdefault("METABASE_USERNAME", "test@example.com")
    os.environ.setdefault("METABASE_PASSWORD", "test-password")
    os.environ.setdefault("WECOM_WEBHOOK_DEFAULT", "https://example.com/default")
    os.environ["WECOM_PAYMENT_RECORDS_SMARTSHEET_WEBHOOK"] = webhook_url
    os.environ["LOCAL_DB_PATH"] = db_path


def _build_fake_response():
    return {
        "data": {
            "cols": [
                {"name": "contractCode"},
                {"name": "payPrice"},
                {"name": "auditstate2Time"},
            ],
            "rows": [
                ["PAY-E2E-0001", "1", "1735660800000"],
            ],
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a one-row local E2E for payment-records smartsheet.")
    parser.add_argument(
        "--webhook-url",
        default="http://127.0.0.1:8787/payment-records",
        help="Local webhook sink URL.",
    )
    parser.add_argument(
        "--db-path",
        default="state/payment_records_local_e2e.db",
        help="SQLite DB path for the run.",
    )
    parser.add_argument(
        "--sink-output-file",
        default="state/local_webhook_sink_payment_records.ndjson",
        help="Optional captured output file from the local webhook sink.",
    )
    args = parser.parse_args()

    db_path = str(Path(args.db_path))
    _seed_env(args.webhook_url, db_path)

    import modules.config as config_module

    importlib.reload(config_module)

    import modules.core.project_settlement_jobs as jobs_module

    importlib.reload(jobs_module)

    from modules.core.storage import create_data_store

    storage = create_data_store(storage_type="sqlite", db_path=db_path)
    fake_response = _build_fake_response()
    now = datetime(2026, 4, 17, 13, 30, 0)

    with patch.object(jobs_module, "send_request_with_managed_session", return_value=fake_response):
        service = jobs_module.SmartsheetSyncService(
            storage=storage,
            sync_config=jobs_module.PAYMENT_RECORDS_SYNC_CONFIG,
            now=now,
        )
        stats = service.run()

    print(json.dumps(stats, ensure_ascii=False, indent=2))

    sink_file = Path(args.sink_output_file)
    if sink_file.exists():
        lines = sink_file.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            last = json.loads(lines[-1])
            print("Captured webhook payload:")
            print(json.dumps(last.get("body_json"), ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
