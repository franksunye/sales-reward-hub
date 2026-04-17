#!/usr/bin/env python3
"""一次性维护脚本：清理企业微信智能表格同步任务里因历史 bug 卡住的 outbox。

使用场景：payload 用的日期格式不对（旧代码下发 "YYYY-MM-DD HH:MM:SS"，
WeCom smartsheet 要求毫秒 unix 时间戳字符串 → errcode 2022034），
失败记录会一直占着 dedupe_key，导致修复代码后仍无法重新生成正确 payload。

本脚本按 activity_code 删除 status != 'sent' 的 outbox 行。已成功发送的行
(`sent`) 不会被清理，避免下次同步时在智能表格里写出重复记录。

示例：
    # 默认按 .env 里的 DB_SOURCE 选择 sqlite(local) / turso(cloud)
    python scripts/reset_failed_smartsheet_outbox.py \
        --activity-code PAYMENT-RECORDS-SMARTSHEET-SYNC

    # 先查看将要删除多少条
    python scripts/reset_failed_smartsheet_outbox.py \
        --activity-code PAYMENT-RECORDS-SMARTSHEET-SYNC --dry-run

    # 强制显式指定 sqlite / turso
    DB_SOURCE=cloud python scripts/reset_failed_smartsheet_outbox.py \
        --activity-code CONTRACT-COMPLETION-SMARTSHEET-SYNC
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable

from dotenv import load_dotenv

from modules.core.storage import create_data_store


DEFAULT_ACTIVITY_CODES = (
    "PAYMENT-RECORDS-SMARTSHEET-SYNC",
    "CONTRACT-COMPLETION-SMARTSHEET-SYNC",
    "PROJECT-SETTLEMENT-SMARTSHEET-SYNC",
)


def _count_and_delete(store, activity_code: str, dry_run: bool) -> tuple[int, int]:
    with store._connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM notification_outbox WHERE activity_code = ?",
            (activity_code,),
        ).fetchone()[0]
        to_delete = conn.execute(
            "SELECT COUNT(*) FROM notification_outbox WHERE activity_code = ? AND status != 'sent'",
            (activity_code,),
        ).fetchone()[0]

        if dry_run or to_delete == 0:
            return total, to_delete

        conn.execute(
            "DELETE FROM notification_outbox WHERE activity_code = ? AND status != 'sent'",
            (activity_code,),
        )
        conn.commit()
        return total, to_delete


def _run(activity_codes: Iterable[str], dry_run: bool) -> int:
    load_dotenv()
    store = create_data_store(storage_type="sqlite")
    logger = logging.getLogger(__name__)
    logger.info("Storage backend: %s", type(store).__name__)

    exit_code = 0
    for code in activity_codes:
        try:
            total, deleted = _count_and_delete(store, code, dry_run)
        except Exception as exc:
            logger.error("清理 %s 失败: %s", code, exc)
            exit_code = 1
            continue

        action = "将删除" if dry_run else "已删除"
        logger.info(
            "[%s] outbox 总行数=%s, %s 非 sent 行数=%s",
            code,
            total,
            action,
            deleted,
        )

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--activity-code",
        action="append",
        dest="activity_codes",
        help="要清理的 activity_code，可多次指定；不填则处理所有智能表格同步任务。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要删除的数量，不做实际变更。",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    codes = args.activity_codes or list(DEFAULT_ACTIVITY_CODES)
    return _run(codes, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
