"""
销售激励系统重构 - 存储抽象层
版本: v1.0
创建日期: 2025-01-08

这个模块提供了统一的存储接口，使用SQLite实现。
SQLite实现用于生产环境，提供高性能的查询和事务支持。
"""

from abc import ABC, abstractmethod
from typing import List, Dict
import sqlite3
import json
import logging
import os
import math
import time
try:
    import requests
except ImportError:  # pragma: no cover - optional dependency for Turso mode
    requests = None

from .data_models import HousekeeperStats, PerformanceRecord


def _resolve_storage_type(storage_type: str = "sqlite") -> str:
    """根据环境变量解析最终存储类型（local=sqlite, cloud=turso）。"""
    db_source = os.getenv("DB_SOURCE", "").strip().lower()
    if db_source == "local":
        return "sqlite"
    if db_source == "cloud":
        return "turso"

    direct_storage = os.getenv("STORAGE_TYPE", "").strip().lower()
    if direct_storage in {"sqlite", "turso"}:
        return direct_storage

    return (storage_type or "sqlite").strip().lower()


def _resolve_local_db_path(default_path: str = "performance_data.db") -> str:
    return os.getenv("LOCAL_DB_PATH", default_path)


class TursoHttpCursor:
    """最小 DB-API 兼容 Cursor，基于 Turso HTTP Pipeline API。"""

    def __init__(self, conn: "TursoHttpConnection"):
        self.conn = conn
        self.rowcount = -1
        self.lastrowid = None
        self.description = None
        self._rows = []
        self._idx = 0

    @staticmethod
    def _encode_arg(value):
        if value is None:
            return {"type": "null", "value": None}
        if isinstance(value, bool):
            return {"type": "integer", "value": "1" if value else "0"}
        if isinstance(value, int):
            return {"type": "integer", "value": str(value)}
        if isinstance(value, float):
            if not math.isfinite(value):
                return {"type": "null", "value": None}
            return {"type": "float", "value": value}
        return {"type": "text", "value": str(value)}

    def execute(self, sql, params=None):
        args = [self._encode_arg(p) for p in (params or [])]
        stmt = {"sql": sql}
        if args:
            stmt["args"] = args

        payload = {"requests": [{"type": "execute", "stmt": stmt}, {"type": "close"}]}
        resp = self.conn._send(payload)
        self._process_response(resp)
        return self

    def _process_response(self, resp_json):
        if not resp_json:
            return
        results = resp_json.get("results", [])
        if not results:
            return

        exec_res = results[0]
        if exec_res.get("type") == "error":
            raise RuntimeError(f"Turso Error: {exec_res.get('error')}")

        if exec_res.get("type") != "ok":
            return

        result = exec_res["response"]["result"]
        self.rowcount = result.get("affected_row_count", 0)
        self.lastrowid = result.get("last_insert_rowid")

        cols = result.get("cols", [])
        self.description = [(c["name"], c.get("decltype")) for c in cols] if cols else None

        self._rows = []
        for row in result.get("rows", []):
            converted = []
            for cell in row:
                val = cell.get("value")
                t = cell.get("type", "text")
                if t == "integer":
                    converted.append(int(val) if val is not None else None)
                elif t == "float":
                    converted.append(float(val) if val is not None else None)
                elif t == "null":
                    converted.append(None)
                else:
                    converted.append(str(val) if val is not None else None)
            self._rows.append(tuple(converted))
        self._idx = 0

    def fetchone(self):
        if self._idx >= len(self._rows):
            return None
        row = self._rows[self._idx]
        self._idx += 1
        return row

    def fetchall(self):
        rows = self._rows[self._idx:]
        self._idx = len(self._rows)
        return rows

    def close(self):
        return None


class TursoHttpConnection:
    """最小 DB-API 兼容 Connection，供现有 SQL 逻辑直接复用。"""

    def __init__(self, url: str, token: str):
        base = url.replace("libsql://", "https://").replace("wss://", "https://").rstrip("/")
        self.url = f"{base}/v2/pipeline"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.max_retries = int(os.getenv("TURSO_HTTP_MAX_RETRIES", "3"))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def _send(self, payload: Dict):
        if requests is None:
            raise RuntimeError("requests is required for Turso mode. Please install dependencies first.")
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                wait_seconds = 0.8 * attempt
                logging.warning("Turso HTTP request failed (attempt %s/%s): %s", attempt, self.max_retries, exc)
                time.sleep(wait_seconds)
        raise last_error

    def cursor(self):
        return TursoHttpCursor(self)

    def execute(self, sql, params=None):
        cursor = self.cursor()
        return cursor.execute(sql, params)

    def executescript(self, script: str):
        statements = []
        for chunk in script.split(";"):
            stmt = chunk.strip()
            if not stmt:
                continue
            if stmt.startswith("--"):
                lines = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
                stmt = "\n".join(lines).strip()
                if not stmt:
                    continue
            statements.append(stmt)
        for stmt in statements:
            self.execute(stmt)

    def commit(self):
        return None

    def close(self):
        return None


class PerformanceDataStore(ABC):
    """性能数据存储抽象接口"""

    @abstractmethod
    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """检查合同是否已存在"""
        pass

    @abstractmethod
    def get_existing_contract_ids(self, activity_code: str) -> set:
        """获取已存在的合同ID集合"""
        pass

    @abstractmethod
    def get_existing_non_historical_contract_count(self, activity_code: str) -> int:
        """获取已存在的非历史合同数量（用于全局序号计算）"""
        pass

    @abstractmethod
    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> HousekeeperStats:
        """获取管家累计统计数据"""
        pass

    @abstractmethod
    def get_housekeeper_awards(self, housekeeper: str, activity_code: str) -> List[str]:
        """获取管家历史奖励列表"""
        pass

    @abstractmethod
    def save_performance_record(self, record: PerformanceRecord) -> None:
        """保存业绩记录"""
        pass

    @abstractmethod
    def get_project_usage(self, project_id: str, activity_code: str) -> float:
        """获取项目累计使用金额（北京工单上限用）"""
        pass

    @abstractmethod
    def get_all_records(self, activity_code: str) -> List[Dict]:
        """获取指定活动的所有记录"""
        pass

    @abstractmethod
    def enqueue_outbox_message(
        self,
        activity_code: str,
        contract_id: str,
        message_type: str,
        webhook_url: str,
        payload_json: str,
        dedupe_key: str,
        metadata_json: str = "",
    ) -> int:
        """创建或复用 outbox 消息，返回 outbox id。"""
        pass

    @abstractmethod
    def get_retryable_outbox_messages(self, activity_code: str, max_attempts: int, limit: int = 100) -> List[Dict]:
        """获取可重试发送的 outbox 消息。"""
        pass

    @abstractmethod
    def get_outbox_message(self, outbox_id: int) -> Dict:
        """按 id 获取 outbox 消息。"""
        pass

    @abstractmethod
    def mark_outbox_sent(self, outbox_id: int, response_code: int, response_body: str) -> None:
        """标记 outbox 消息发送成功。"""
        pass

    @abstractmethod
    def mark_outbox_failed(
        self,
        outbox_id: int,
        last_error: str,
        response_code: int = 0,
        response_body: str = "",
        max_attempts: int = 5,
    ) -> None:
        """标记 outbox 消息发送失败并累加尝试次数。"""
        pass

    @abstractmethod
    def upsert_pending_order_snapshot(self, activity_code: str, snapshot: Dict) -> None:
        """写入或更新待预约工单快照。"""
        pass

    @abstractmethod
    def deactivate_missing_pending_orders(self, activity_code: str, active_fingerprints: List[str]) -> int:
        """将当前未出现的活跃待预约工单标记为失活。"""
        pass

    @abstractmethod
    def get_pending_orders_requiring_notification(self, activity_code: str) -> List[Dict]:
        """获取当前需要提醒的待预约工单。"""
        pass

    @abstractmethod
    def get_active_pending_orders_by_org(self, activity_code: str, org_name: str) -> List[Dict]:
        """获取指定服务商当前活跃的全部待预约工单。"""
        pass

    @abstractmethod
    def mark_pending_orders_notified(self, activity_code: str, fingerprints: List[str]) -> int:
        """将待预约工单标记为已提醒。"""
        pass

    @abstractmethod
    def replace_sla_violations_for_date(self, business_date: str, records: List[Dict]) -> int:
        """以业务日期为粒度替换 SLA 违规快照。"""
        pass

    @abstractmethod
    def get_sla_violations_for_window(
        self,
        start_date: str,
        end_date: str,
        org_name: str | None = None,
    ) -> List[Dict]:
        """查询业务日期窗口内的 SLA 违规记录。"""
        pass


class SQLitePerformanceDataStore(PerformanceDataStore):
    """SQLite实现 - 大幅简化累计计算"""

    def __init__(self, db_path: str = "performance_data.db"):
        self.db_path = db_path
        self._init_database()

    def _connect(self):
        """返回连接（本地 SQLite）。"""
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _cursor_rows_to_dicts(cursor) -> List[Dict]:
        rows = cursor.fetchall()
        if not rows:
            return []
        columns = [col[0] for col in (cursor.description or [])]
        if not columns:
            return []
        return [dict(zip(columns, row)) for row in rows]

    def _init_database(self):
        """初始化数据库"""
        try:
            with self._connect() as conn:
                # 读取并执行schema文件
                schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema_sql = f.read()
                    # 修改SQL语句，使用IF NOT EXISTS
                    schema_sql = schema_sql.replace('CREATE TABLE performance_data', 'CREATE TABLE IF NOT EXISTS performance_data')
                    schema_sql = schema_sql.replace('CREATE VIEW housekeeper_stats', 'CREATE VIEW IF NOT EXISTS housekeeper_stats')
                    schema_sql = schema_sql.replace('CREATE VIEW project_stats', 'CREATE VIEW IF NOT EXISTS project_stats')
                    schema_sql = schema_sql.replace('CREATE VIEW activity_stats', 'CREATE VIEW IF NOT EXISTS activity_stats')
                    schema_sql = schema_sql.replace('CREATE TABLE schema_version', 'CREATE TABLE IF NOT EXISTS schema_version')
                    schema_sql = schema_sql.replace('CREATE TABLE notification_outbox', 'CREATE TABLE IF NOT EXISTS notification_outbox')
                    schema_sql = schema_sql.replace('CREATE TABLE pending_order_reminders', 'CREATE TABLE IF NOT EXISTS pending_order_reminders')
                    schema_sql = schema_sql.replace('CREATE TABLE sla_violation_records', 'CREATE TABLE IF NOT EXISTS sla_violation_records')
                    conn.executescript(schema_sql)
                    self._ensure_column_exists(conn, 'notification_outbox', 'metadata_json', "ALTER TABLE notification_outbox ADD COLUMN metadata_json TEXT DEFAULT ''")
                    logging.info(f"Database initialized with schema from {schema_path}")
                else:
                    logging.warning(f"Schema file not found: {schema_path}")
                    self._create_basic_schema(conn)
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise

    def _ensure_column_exists(self, conn, table_name: str, column_name: str, alter_sql: str) -> None:
        """为历史数据库补齐新增列。"""
        try:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = {row[1] for row in cursor.fetchall()}
            if column_name not in columns:
                conn.execute(alter_sql)
                conn.commit()
                logging.info("Added missing column %s.%s", table_name, column_name)
        except Exception as e:
            logging.warning("Failed ensuring column %s.%s exists: %s", table_name, column_name, e)

    def _create_basic_schema(self, conn):
        """创建基础schema（如果schema文件不存在）"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_code TEXT NOT NULL,
                contract_id TEXT NOT NULL,
                housekeeper TEXT NOT NULL,
                service_provider TEXT,
                contract_amount REAL NOT NULL,
                performance_amount REAL NOT NULL,
                order_type TEXT DEFAULT 'platform',
                project_id TEXT,
                contract_sequence INTEGER DEFAULT 0,
                reward_types TEXT,
                reward_names TEXT,
                is_historical BOOLEAN DEFAULT FALSE,
                notification_sent BOOLEAN DEFAULT FALSE,
                remarks TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extensions TEXT,
                UNIQUE(activity_code, contract_id)
            )
        """)
        
        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_housekeeper_activity ON performance_data(housekeeper, activity_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_contract_lookup ON performance_data(contract_id, activity_code)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notification_outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_code TEXT NOT NULL,
                contract_id TEXT NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'group_broadcast',
                webhook_url TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                metadata_json TEXT DEFAULT '',
                dedupe_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                attempt_count INTEGER NOT NULL DEFAULT 0,
                response_code INTEGER DEFAULT 0,
                response_body TEXT DEFAULT '',
                last_error TEXT DEFAULT '',
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(activity_code, dedupe_key)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_outbox_retry ON notification_outbox(activity_code, status, attempt_count, created_at)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_order_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_code TEXT NOT NULL,
                order_num TEXT NOT NULL,
                customer_name TEXT DEFAULT '',
                address TEXT DEFAULT '',
                supervisor_name TEXT DEFAULT '',
                create_time TEXT NOT NULL,
                org_name TEXT NOT NULL,
                order_status TEXT NOT NULL,
                status_fingerprint TEXT NOT NULL,
                eligible_since TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                notification_sent BOOLEAN DEFAULT FALSE,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_notified_at TIMESTAMP,
                resolved_at TIMESTAMP,
                extensions TEXT DEFAULT '',
                UNIQUE(activity_code, status_fingerprint)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pending_orders_active
            ON pending_order_reminders(activity_code, is_active, notification_sent, org_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_pending_orders_order_num
            ON pending_order_reminders(activity_code, order_num)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sla_violation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_date TEXT NOT NULL,
                violation_id TEXT DEFAULT '',
                sid TEXT DEFAULT '',
                sa_create_time TEXT NOT NULL,
                order_num TEXT NOT NULL,
                province TEXT DEFAULT '',
                org_name TEXT NOT NULL,
                supervisor_name TEXT DEFAULT '',
                source_type TEXT DEFAULT '',
                status TEXT DEFAULT '',
                violation_type TEXT DEFAULT '',
                violation_description TEXT DEFAULT '',
                work_type TEXT DEFAULT '',
                create_time TEXT DEFAULT '',
                raw_json TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(business_date, order_num, org_name, violation_type, violation_description)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sla_violation_business_date
            ON sla_violation_records(business_date, org_name)
        """)

    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """简化的去重查询 - O(1)索引查询替代O(n)文件扫描"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM performance_data WHERE contract_id = ? AND activity_code = ?",
                    (contract_id, activity_code)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking contract existence: {e}")
            return False

    def get_existing_contract_ids(self, activity_code: str) -> set:
        """获取已存在的合同ID集合"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT contract_id FROM performance_data WHERE activity_code = ?",
                    (activity_code,)
                )
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logging.error(f"Error getting existing contract IDs: {e}")
            return set()

    def get_existing_non_historical_contract_count(self, activity_code: str) -> int:
        """获取已存在的非历史合同数量（用于全局序号计算）"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM performance_data WHERE activity_code = ? AND is_historical = 0",
                    (activity_code,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting non-historical contract count: {e}")
            return 0

    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> HousekeeperStats:
        """数据库聚合查询 - 替代复杂的内存计算"""
        try:
            with self._connect() as conn:
                cursor = conn.execute("""
                    SELECT
                        -- 累计统计只包含新增合同（与旧系统保持一致）
                        COALESCE(SUM(CASE WHEN is_historical = 0 THEN 1 ELSE 0 END), 0) as contract_count,
                        COALESCE(SUM(CASE WHEN is_historical = 0 THEN contract_amount ELSE 0 END), 0) as total_amount,
                        -- 🔧 修复：累计业绩金额只包含新增合同，历史工单不计入当期活动累计业绩
                        COALESCE(SUM(CASE WHEN is_historical = 0 THEN performance_amount ELSE 0 END), 0) as performance_amount,
                        COALESCE(SUM(CASE WHEN is_historical = 0 AND order_type = 'platform' THEN 1 ELSE 0 END), 0) as platform_count,
                        COALESCE(SUM(CASE WHEN is_historical = 0 AND order_type = 'platform' THEN contract_amount ELSE 0 END), 0) as platform_amount,
                        COALESCE(SUM(CASE WHEN is_historical = 0 AND order_type = 'self_referral' THEN 1 ELSE 0 END), 0) as self_referral_count,
                        COALESCE(SUM(CASE WHEN is_historical = 0 AND order_type = 'self_referral' THEN contract_amount ELSE 0 END), 0) as self_referral_amount,
                        COALESCE(SUM(CASE WHEN is_historical = 1 THEN 1 ELSE 0 END), 0) as historical_count,
                        COALESCE(SUM(CASE WHEN is_historical = 0 THEN 1 ELSE 0 END), 0) as new_count
                    FROM performance_data
                    WHERE housekeeper = ? AND activity_code = ?
                """, (housekeeper, activity_code))

                result = cursor.fetchone()
                if result:
                    return HousekeeperStats(
                        housekeeper=housekeeper,
                        activity_code=activity_code,
                        contract_count=result[0],
                        total_amount=result[1],
                        performance_amount=result[2],
                        platform_count=result[3],
                        platform_amount=result[4],
                        self_referral_count=result[5],
                        self_referral_amount=result[6],
                        historical_count=result[7],
                        new_count=result[8]
                    )
                else:
                    return HousekeeperStats(housekeeper=housekeeper, activity_code=activity_code)
        except Exception as e:
            logging.error(f"Error getting housekeeper stats: {e}")
            return HousekeeperStats(housekeeper=housekeeper, activity_code=activity_code)

    def get_housekeeper_awards(self, housekeeper: str, activity_code: str) -> List[str]:
        """获取管家历史奖励列表"""
        try:
            with self._connect() as conn:
                cursor = conn.execute("""
                    SELECT reward_names FROM performance_data
                    WHERE housekeeper = ? AND activity_code = ? AND reward_names IS NOT NULL AND reward_names != ''
                """, (housekeeper, activity_code))

                awards = []
                for row in cursor.fetchall():
                    if row[0]:
                        # 解析JSON格式的奖励数据
                        import json
                        try:
                            reward_names = json.loads(row[0])
                            if isinstance(reward_names, list):
                                for reward_name in reward_names:
                                    if reward_name and reward_name not in awards:
                                        awards.append(reward_name)
                        except json.JSONDecodeError as e:
                            logging.error(f"Failed to parse reward data as JSON: {row[0]}, error: {e}")
                            continue

                return awards
        except Exception as e:
            logging.error(f"Error getting housekeeper awards: {e}")
            return []

    def get_all_housekeeper_awards(self, activity_code: str) -> Dict[str, List[str]]:
        """
        获取所有管家的历史奖励列表

        这是修复节节高奖项重复发放问题的关键方法
        返回格式：{管家_服务商: [奖励名称列表]}
        """
        try:
            with self._connect() as conn:
                cursor = conn.execute("""
                    SELECT housekeeper, reward_names FROM performance_data
                    WHERE activity_code = ? AND reward_names IS NOT NULL AND reward_names != ''
                """, (activity_code,))

                housekeeper_awards = {}
                for row in cursor.fetchall():
                    housekeeper = row[0]
                    reward_names_str = row[1]

                    if housekeeper not in housekeeper_awards:
                        housekeeper_awards[housekeeper] = []

                    if reward_names_str:
                        # 解析JSON格式的奖励数据
                        import json
                        try:
                            reward_names = json.loads(reward_names_str)
                            if isinstance(reward_names, list):
                                for reward_name in reward_names:
                                    if reward_name and reward_name not in housekeeper_awards[housekeeper]:
                                        housekeeper_awards[housekeeper].append(reward_name)
                        except json.JSONDecodeError as e:
                            logging.error(f"Failed to parse reward data as JSON for {housekeeper}: {reward_names_str}, error: {e}")
                            continue

                logging.info(f"Retrieved awards for {len(housekeeper_awards)} housekeepers from database")
                return housekeeper_awards

        except Exception as e:
            logging.error(f"Error getting all housekeeper awards: {e}")
            return {}

    def save_performance_record(self, record: PerformanceRecord) -> None:
        """保存业绩记录"""
        try:
            with self._connect() as conn:
                reward_types = json.dumps([r.reward_type for r in record.rewards], ensure_ascii=False)
                reward_names = json.dumps([r.reward_name for r in record.rewards], ensure_ascii=False)

                # 保存完整数据到extensions，包括双轨统计字段
                # 🔧 修复：使用record.to_dict()获取完整数据，而不是只保存原始数据
                record_dict = record.to_dict()
                extensions_data = record_dict.copy()

                # 移除已经单独存储的字段，避免重复
                # 🔧 修复：保留"备注"和"管家累计业绩金额"字段在extensions中，因为通知服务需要从extensions中读取
                fields_to_remove = [
                    '合同ID(_id)', '管家(serviceHousekeeper)', '服务商(orgName)',
                    '合同金额(adjustRefundMoney)', '活动期内第几个合同',
                    '激活奖励状态', '奖励类型', '奖励名称', '是否发送通知'
                ]
                for field in fields_to_remove:
                    extensions_data.pop(field, None)

                conn.execute("""
                    INSERT OR REPLACE INTO performance_data (
                        activity_code, contract_id, housekeeper, service_provider,
                        contract_amount, performance_amount, order_type, project_id,
                        contract_sequence, reward_types, reward_names, is_historical,
                        notification_sent, remarks, extensions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.activity_code,
                    record.contract_data.contract_id,
                    record.housekeeper_stats.housekeeper,  # 使用管家键而不是原始管家名
                    record.contract_data.service_provider,
                    record.contract_data.contract_amount,
                    record.performance_amount,
                    record.contract_data.order_type.value,
                    record.contract_data.project_id,
                    record.contract_sequence,
                    reward_types,
                    reward_names,
                    record.contract_data.is_historical,
                    record.notification_sent,
                    record.remarks,
                    json.dumps(extensions_data, ensure_ascii=False)
                ))
                
                logging.debug(f"Saved performance record for contract {record.contract_data.contract_id}")
        except Exception as e:
            logging.error(f"Error saving performance record: {e}")
            raise

    def get_project_usage(self, project_id: str, activity_code: str) -> float:
        """获取项目累计使用金额（北京工单上限用）"""
        try:
            with self._connect() as conn:
                cursor = conn.execute("""
                    SELECT COALESCE(SUM(performance_amount), 0)
                    FROM performance_data
                    WHERE project_id = ? AND activity_code = ?
                """, (project_id, activity_code))
                
                result = cursor.fetchone()
                return result[0] if result else 0.0
        except Exception as e:
            logging.error(f"Error getting project usage: {e}")
            return 0.0

    def get_all_records(self, activity_code: str) -> List[Dict]:
        """获取指定活动的所有记录"""
        try:
            with self._connect() as conn:
                cursor = conn.execute("""
                    SELECT * FROM performance_data
                    WHERE activity_code = ?
                    ORDER BY created_at
                """, (activity_code,))
                return self._cursor_rows_to_dicts(cursor)
        except Exception as e:
            logging.error(f"Error getting all records: {e}")
            return []



    def query_performance_records(self, conditions: Dict) -> List[Dict]:
        """查询业绩记录"""
        try:
            with self._connect() as conn:
                # 构建查询条件
                where_clauses = []
                params = []

                for key, value in conditions.items():
                    if key == 'notification_sent':
                        # 处理布尔值字段 - 数据库中存储为整数
                        where_clauses.append("notification_sent = ?")
                        params.append(1 if value else 0)
                    elif key == 'is_historical':
                        # 处理布尔值字段
                        where_clauses.append("is_historical = ?")
                        params.append(1 if value else 0)
                    else:
                        where_clauses.append(f"{key} = ?")
                        params.append(value)

                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

                cursor = conn.execute(f"""
                    SELECT * FROM performance_data
                    WHERE {where_clause}
                    ORDER BY created_at
                """, params)
                return self._cursor_rows_to_dicts(cursor)
        except Exception as e:
            logging.error(f"Error querying performance records: {e}")
            return []

    def update_notification_status(self, contract_id: str, activity_code: str, notification_sent: bool):
        """更新通知发送状态"""
        try:
            with self._connect() as conn:
                conn.execute("""
                    UPDATE performance_data
                    SET notification_sent = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE contract_id = ? AND activity_code = ?
                """, (1 if notification_sent else 0, contract_id, activity_code))
                conn.commit()
                logging.debug(f"Updated notification status for {contract_id}")
        except Exception as e:
            logging.error(f"Error updating notification status: {e}")
            raise

    def enqueue_outbox_message(
        self,
        activity_code: str,
        contract_id: str,
        message_type: str,
        webhook_url: str,
        payload_json: str,
        dedupe_key: str,
        metadata_json: str = "",
    ) -> int:
        """创建或复用 outbox 消息，返回 outbox id。"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO notification_outbox (
                        activity_code, contract_id, message_type, webhook_url, payload_json, metadata_json, dedupe_key, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                    """,
                    (activity_code, contract_id, message_type, webhook_url, payload_json, metadata_json, dedupe_key),
                )
                if cursor.lastrowid:
                    conn.commit()
                    return int(cursor.lastrowid)

                existing = conn.execute(
                    """
                    SELECT id FROM notification_outbox
                    WHERE activity_code = ? AND dedupe_key = ?
                    LIMIT 1
                    """,
                    (activity_code, dedupe_key),
                ).fetchone()
                conn.commit()
                return int(existing[0]) if existing else 0
        except Exception as e:
            logging.error(f"Error enqueueing outbox message: {e}")
            raise

    def upsert_pending_order_snapshot(self, activity_code: str, snapshot: Dict) -> None:
        """写入或更新待预约工单快照。"""
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO pending_order_reminders (
                        activity_code, order_num, customer_name, address, supervisor_name,
                        create_time, org_name, order_status, status_fingerprint, eligible_since,
                        is_active, notification_sent, extensions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)
                    ON CONFLICT(activity_code, status_fingerprint) DO UPDATE SET
                        order_num = excluded.order_num,
                        customer_name = excluded.customer_name,
                        address = excluded.address,
                        supervisor_name = excluded.supervisor_name,
                        create_time = excluded.create_time,
                        org_name = excluded.org_name,
                        order_status = excluded.order_status,
                        eligible_since = excluded.eligible_since,
                        is_active = 1,
                        notification_sent = CASE
                            WHEN pending_order_reminders.is_active = 0 THEN 0
                            ELSE pending_order_reminders.notification_sent
                        END,
                        last_seen_at = CURRENT_TIMESTAMP,
                        resolved_at = NULL,
                        extensions = excluded.extensions
                    """,
                    (
                        activity_code,
                        snapshot["order_num"],
                        snapshot.get("customer_name", ""),
                        snapshot.get("address", ""),
                        snapshot.get("supervisor_name", ""),
                        snapshot["create_time"],
                        snapshot["org_name"],
                        snapshot["order_status"],
                        snapshot["status_fingerprint"],
                        snapshot["eligible_since"],
                        snapshot.get("extensions", ""),
                    ),
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Error upserting pending order snapshot: {e}")
            raise

    def deactivate_missing_pending_orders(self, activity_code: str, active_fingerprints: List[str]) -> int:
        """将当前快照中已消失的工单标记为失活。"""
        try:
            with self._connect() as conn:
                params = [activity_code]
                sql = """
                    UPDATE pending_order_reminders
                    SET is_active = 0,
                        resolved_at = CURRENT_TIMESTAMP,
                        last_seen_at = CURRENT_TIMESTAMP
                    WHERE activity_code = ?
                      AND is_active = 1
                """
                if active_fingerprints:
                    placeholders = ",".join(["?"] * len(active_fingerprints))
                    sql += f" AND status_fingerprint NOT IN ({placeholders})"
                    params.extend(active_fingerprints)
                cursor = conn.execute(sql, params)
                conn.commit()
                return cursor.rowcount or 0
        except Exception as e:
            logging.error(f"Error deactivating missing pending orders: {e}")
            raise

    def get_pending_orders_requiring_notification(self, activity_code: str) -> List[Dict]:
        """获取当前活跃且尚未提醒的工单。"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM pending_order_reminders
                    WHERE activity_code = ?
                      AND is_active = 1
                      AND notification_sent = 0
                    ORDER BY org_name ASC, create_time ASC, order_num ASC
                    """,
                    (activity_code,),
                )
                return self._cursor_rows_to_dicts(cursor)
        except Exception as e:
            logging.error(f"Error querying pending orders requiring notification: {e}")
            return []

    def get_active_pending_orders_by_org(self, activity_code: str, org_name: str) -> List[Dict]:
        """获取指定服务商当前全部活跃工单。"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM pending_order_reminders
                    WHERE activity_code = ?
                      AND org_name = ?
                      AND is_active = 1
                    ORDER BY create_time ASC, order_num ASC
                    """,
                    (activity_code, org_name),
                )
                return self._cursor_rows_to_dicts(cursor)
        except Exception as e:
            logging.error(f"Error querying active pending orders by org: {e}")
            return []

    def mark_pending_orders_notified(self, activity_code: str, fingerprints: List[str]) -> int:
        """将指定指纹的工单标记为已提醒。"""
        if not fingerprints:
            return 0
        try:
            with self._connect() as conn:
                placeholders = ",".join(["?"] * len(fingerprints))
                cursor = conn.execute(
                    f"""
                    UPDATE pending_order_reminders
                    SET notification_sent = 1,
                        last_notified_at = CURRENT_TIMESTAMP
                    WHERE activity_code = ?
                      AND status_fingerprint IN ({placeholders})
                    """,
                    [activity_code, *fingerprints],
                )
                conn.commit()
                return cursor.rowcount or 0
        except Exception as e:
            logging.error(f"Error marking pending orders notified: {e}")
            raise

    def replace_sla_violations_for_date(self, business_date: str, records: List[Dict]) -> int:
        """按业务日期覆盖 SLA 违规快照。"""
        try:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM sla_violation_records WHERE business_date = ?",
                    (business_date,),
                )
                if records:
                    conn.executemany(
                        """
                        INSERT INTO sla_violation_records (
                            business_date, violation_id, sid, sa_create_time, order_num,
                            province, org_name, supervisor_name, source_type, status,
                            violation_type, violation_description, work_type, create_time, raw_json,
                            updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        [
                            (
                                business_date,
                                record.get("_id", ""),
                                record.get("sid", ""),
                                record.get("saCreateTime", ""),
                                record.get("orderNum", ""),
                                record.get("province", ""),
                                record.get("orgName", ""),
                                record.get("supervisorName", ""),
                                str(record.get("sourceType", "")),
                                str(record.get("status", "")),
                                record.get("msg", ""),
                                record.get("memo", ""),
                                str(record.get("workType", "")),
                                record.get("createTime", ""),
                                json.dumps(record, ensure_ascii=False),
                            )
                            for record in records
                        ],
                    )
                conn.commit()
                return len(records)
        except Exception as e:
            logging.error(f"Error replacing SLA violations for {business_date}: {e}")
            raise

    def get_sla_violations_for_window(
        self,
        start_date: str,
        end_date: str,
        org_name: str | None = None,
    ) -> List[Dict]:
        """查询业务日期窗口内的 SLA 违规记录。"""
        try:
            with self._connect() as conn:
                params = [start_date, end_date]
                sql = """
                    SELECT *
                    FROM sla_violation_records
                    WHERE business_date >= ?
                      AND business_date <= ?
                """
                if org_name:
                    sql += " AND org_name = ?"
                    params.append(org_name)
                sql += " ORDER BY business_date ASC, org_name ASC, order_num ASC"
                cursor = conn.execute(sql, params)
                return self._cursor_rows_to_dicts(cursor)
        except Exception as e:
            logging.error(f"Error querying SLA violations between {start_date} and {end_date}: {e}")
            return []

    def get_retryable_outbox_messages(self, activity_code: str, max_attempts: int, limit: int = 100) -> List[Dict]:
        """获取可重试发送的 outbox 消息。"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM notification_outbox
                    WHERE activity_code = ?
                      AND status IN ('pending', 'failed')
                      AND attempt_count < ?
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (activity_code, max_attempts, limit),
                )
                return self._cursor_rows_to_dicts(cursor)
        except Exception as e:
            logging.error(f"Error querying retryable outbox messages: {e}")
            return []

    def get_outbox_message(self, outbox_id: int) -> Dict:
        """按 id 获取 outbox 消息。"""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM notification_outbox
                    WHERE id = ?
                    LIMIT 1
                    """,
                    (outbox_id,),
                )
                rows = self._cursor_rows_to_dicts(cursor)
                return rows[0] if rows else {}
        except Exception as e:
            logging.error(f"Error getting outbox message {outbox_id}: {e}")
            return {}

    def mark_outbox_sent(self, outbox_id: int, response_code: int, response_body: str) -> None:
        """标记 outbox 消息发送成功。"""
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE notification_outbox
                    SET status = 'sent',
                        response_code = ?,
                        response_body = ?,
                        last_error = '',
                        sent_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (response_code, response_body[:2000], outbox_id),
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Error marking outbox sent (id={outbox_id}): {e}")
            raise

    def mark_outbox_failed(
        self,
        outbox_id: int,
        last_error: str,
        response_code: int = 0,
        response_body: str = "",
        max_attempts: int = 5,
    ) -> None:
        """标记 outbox 消息发送失败并累加尝试次数。"""
        try:
            with self._connect() as conn:
                current = conn.execute(
                    "SELECT attempt_count FROM notification_outbox WHERE id = ?",
                    (outbox_id,),
                ).fetchone()
                attempts = int(current[0]) + 1 if current else 1
                new_status = "dead_letter" if attempts >= max_attempts else "failed"
                conn.execute(
                    """
                    UPDATE notification_outbox
                    SET status = ?,
                        attempt_count = ?,
                        response_code = ?,
                        response_body = ?,
                        last_error = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        new_status,
                        attempts,
                        response_code,
                        (response_body or "")[:2000],
                        (last_error or "")[:2000],
                        outbox_id,
                    ),
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Error marking outbox failed (id={outbox_id}): {e}")
            raise


class TursoPerformanceDataStore(SQLitePerformanceDataStore):
    """Turso 实现（复用同一套 SQL 逻辑）。"""

    def __init__(self, db_url: str, auth_token: str):
        self.db_url = db_url
        self.auth_token = auth_token
        super().__init__(db_path=":turso:")

    def _connect(self):
        return TursoHttpConnection(self.db_url, self.auth_token)

def create_data_store(storage_type: str = "sqlite", **kwargs) -> PerformanceDataStore:
    """工厂函数：根据环境和参数创建 SQLite 或 Turso 存储实例。"""
    resolved_type = _resolve_storage_type(storage_type)

    if resolved_type == "sqlite":
        db_path = _resolve_local_db_path(kwargs.get("db_path", "performance_data.db"))
        return SQLitePerformanceDataStore(db_path)

    if resolved_type == "turso":
        db_url = kwargs.get("db_url") or os.getenv("TURSO_DB_URL")
        auth_token = kwargs.get("auth_token") or os.getenv("TURSO_AUTH_TOKEN")
        if not db_url or not auth_token:
            raise ValueError("Turso storage requires TURSO_DB_URL and TURSO_AUTH_TOKEN.")
        return TursoPerformanceDataStore(db_url, auth_token)

    raise ValueError(f"Unsupported storage type: {resolved_type}. Only 'sqlite' and 'turso' are supported.")
