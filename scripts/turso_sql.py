#!/usr/bin/env python3
"""通用 SQL 运维工具：快速查询/更新本地或 Turso 数据库。

特点：
- 默认只读模式，防止误删误改
- 显式 `--write` 才允许 INSERT/UPDATE/DELETE/DDL
- 支持 `--sql` 直接执行，或 `--file` 读取 .sql 文件
- 支持 table / json 两种输出格式

示例：
  # 查询 Turso outbox 聚合（默认 cloud）
  python scripts/turso_sql.py --sql "SELECT activity_code, status, COUNT(*) AS cnt FROM notification_outbox GROUP BY activity_code, status ORDER BY activity_code, status"

  # 执行写操作（必须显式 --write）
  python scripts/turso_sql.py --write --sql "DELETE FROM notification_outbox WHERE activity_code='PAYMENT-RECORDS-SMARTSHEET-SYNC' AND status!='sent'"

  # 读取 SQL 文件执行
  python scripts/turso_sql.py --file scripts/sql/check_outbox.sql

  # 强制本地 sqlite
  DB_SOURCE=local python scripts/turso_sql.py --sql "SELECT COUNT(*) FROM notification_outbox"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

from dotenv import load_dotenv

# 允许直接 `python scripts/turso_sql.py` 运行时导入项目模块
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.storage import create_data_store

_READONLY_SQL_PREFIXES = {
    "select",
    "with",
    "pragma",
    "explain",
}


def _strip_leading_sql_comments(sql: str) -> str:
    # Remove leading empty lines and SQL comments for keyword detection
    text = sql.lstrip()
    while True:
        if text.startswith("--"):
            newline_idx = text.find("\n")
            if newline_idx == -1:
                return ""
            text = text[newline_idx + 1 :].lstrip()
            continue
        if text.startswith("/*"):
            end_idx = text.find("*/")
            if end_idx == -1:
                return ""
            text = text[end_idx + 2 :].lstrip()
            continue
        return text


def _first_keyword(sql: str) -> str:
    text = _strip_leading_sql_comments(sql)
    match = re.match(r"([a-zA-Z_]+)", text)
    return match.group(1).lower() if match else ""


def _is_readonly_sql(sql: str) -> bool:
    return _first_keyword(sql) in _READONLY_SQL_PREFIXES


def _split_sql_statements(sql: str) -> List[str]:
    # 轻量分句：按 ';' 切分并去空语句（足够支持运维常见 SQL）
    return [stmt.strip() for stmt in sql.split(";") if stmt.strip()]


def _render_table(columns: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    headers = [str(c) for c in columns]
    body = [["" if v is None else str(v) for v in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in body:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt_row(items: Iterable[str]) -> str:
        return " | ".join(item.ljust(widths[idx]) for idx, item in enumerate(items))

    sep = "-+-".join("-" * w for w in widths)
    lines = [fmt_row(headers), sep]
    lines.extend(fmt_row(row) for row in body)
    return "\n".join(lines)


def _exec_one(conn, sql: str, output: str) -> int:
    cursor = conn.execute(sql)
    statement_type = _first_keyword(sql)

    if statement_type in _READONLY_SQL_PREFIXES:
        rows = cursor.fetchall()
        cols = [desc[0] for desc in (cursor.description or [])]
        if output == "json":
            print(json.dumps([dict(zip(cols, row)) for row in rows], ensure_ascii=False, indent=2))
        else:
            if not cols:
                print("(no columns)")
            elif not rows:
                print(_render_table(cols, []))
                print("\n(0 rows)")
            else:
                print(_render_table(cols, rows))
                print(f"\n({len(rows)} rows)")
        return len(rows)

    # 写操作
    conn.commit()
    affected = cursor.rowcount if cursor.rowcount is not None else 0
    print(f"OK. affected_rows={affected}")
    return affected


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SQL against sqlite/turso safely.")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--sql", help="SQL string to execute")
    source_group.add_argument("--file", help="Path to a .sql file")

    parser.add_argument(
        "--write",
        action="store_true",
        help="Allow write SQL (INSERT/UPDATE/DELETE/DDL). Default is read-only mode.",
    )
    parser.add_argument(
        "--output",
        choices=["table", "json"],
        default="table",
        help="Query output format for SELECT statements.",
    )
    args = parser.parse_args()

    if not args.sql and not args.file:
        parser.error("one of --sql or --file is required")

    load_dotenv()

    sql_text = args.sql
    if args.file:
        if not os.path.exists(args.file):
            print(f"SQL file not found: {args.file}", file=sys.stderr)
            return 2
        with open(args.file, "r", encoding="utf-8") as f:
            sql_text = f.read()

    statements = _split_sql_statements(sql_text or "")
    if not statements:
        print("No SQL statements to execute.", file=sys.stderr)
        return 2

    if not args.write:
        non_readonly = [stmt for stmt in statements if not _is_readonly_sql(stmt)]
        if non_readonly:
            print("Blocked non-read SQL in read-only mode. Re-run with --write.", file=sys.stderr)
            print(f"First blocked statement starts with: {_first_keyword(non_readonly[0]) or '(unknown)'}", file=sys.stderr)
            return 2

    # create_data_store 会根据 DB_SOURCE 决定 sqlite(local) 还是 turso(cloud)
    store = create_data_store(storage_type="sqlite")
    print(f"Backend: {type(store).__name__}")

    with store._connect() as conn:
        for idx, stmt in enumerate(statements, start=1):
            if len(statements) > 1:
                print(f"\n-- statement {idx}/{len(statements)} --")
            _exec_one(conn, stmt, args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
