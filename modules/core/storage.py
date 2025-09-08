"""
销售激励系统重构 - 存储抽象层
版本: v1.0
创建日期: 2025-01-08

这个模块提供了统一的存储接口，支持SQLite和CSV两种实现方式。
SQLite实现用于生产环境，提供高性能的查询和事务支持。
CSV实现用于向后兼容和测试验证。
"""

from abc import ABC, abstractmethod
from typing import Set, List, Dict, Optional, Tuple
import sqlite3
import csv
import json
import logging
import os
from datetime import datetime

from .data_models import HousekeeperStats, ContractData, PerformanceRecord, OrderType


class PerformanceDataStore(ABC):
    """性能数据存储抽象接口"""

    @abstractmethod
    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """检查合同是否已存在"""
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


class SQLitePerformanceDataStore(PerformanceDataStore):
    """SQLite实现 - 大幅简化累计计算"""

    def __init__(self, db_path: str = "performance_data.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 读取并执行schema文件
                schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema_sql = f.read()
                    conn.executescript(schema_sql)
                    logging.info(f"Database initialized with schema from {schema_path}")
                else:
                    logging.warning(f"Schema file not found: {schema_path}")
                    self._create_basic_schema(conn)
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise

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
                reward_types TEXT,
                reward_names TEXT,
                is_historical BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extensions TEXT,
                UNIQUE(activity_code, contract_id)
            )
        """)
        
        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_housekeeper_activity ON performance_data(housekeeper, activity_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_contract_lookup ON performance_data(contract_id, activity_code)")

    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """简化的去重查询 - O(1)索引查询替代O(n)文件扫描"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM performance_data WHERE contract_id = ? AND activity_code = ?",
                    (contract_id, activity_code)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking contract existence: {e}")
            return False

    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> HousekeeperStats:
        """数据库聚合查询 - 替代复杂的内存计算"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as contract_count,
                        COALESCE(SUM(contract_amount), 0) as total_amount,
                        COALESCE(SUM(performance_amount), 0) as performance_amount,
                        COALESCE(SUM(CASE WHEN order_type = 'platform' THEN 1 ELSE 0 END), 0) as platform_count,
                        COALESCE(SUM(CASE WHEN order_type = 'platform' THEN contract_amount ELSE 0 END), 0) as platform_amount,
                        COALESCE(SUM(CASE WHEN order_type = 'self_referral' THEN 1 ELSE 0 END), 0) as self_referral_count,
                        COALESCE(SUM(CASE WHEN order_type = 'self_referral' THEN contract_amount ELSE 0 END), 0) as self_referral_amount,
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT reward_types FROM performance_data
                    WHERE housekeeper = ? AND activity_code = ? AND reward_types IS NOT NULL
                """, (housekeeper, activity_code))
                
                awards = []
                for row in cursor.fetchall():
                    if row[0]:
                        try:
                            reward_list = json.loads(row[0]) if row[0].startswith('[') else [row[0]]
                            awards.extend(reward_list)
                        except json.JSONDecodeError:
                            awards.append(row[0])
                
                return list(set(awards))  # 去重
        except Exception as e:
            logging.error(f"Error getting housekeeper awards: {e}")
            return []

    def save_performance_record(self, record: PerformanceRecord) -> None:
        """保存业绩记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                reward_types = json.dumps([r.reward_type for r in record.rewards])
                reward_names = json.dumps([r.reward_name for r in record.rewards])
                
                conn.execute("""
                    INSERT OR REPLACE INTO performance_data (
                        activity_code, contract_id, housekeeper, service_provider,
                        contract_amount, performance_amount, order_type, project_id,
                        reward_types, reward_names, is_historical, extensions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.activity_code,
                    record.contract_data.contract_id,
                    record.contract_data.housekeeper,
                    record.contract_data.service_provider,
                    record.contract_data.contract_amount,
                    record.performance_amount,
                    record.contract_data.order_type.value,
                    record.contract_data.project_id,
                    reward_types,
                    reward_names,
                    record.contract_data.is_historical,
                    json.dumps(record.contract_data.raw_data)
                ))
                
                logging.debug(f"Saved performance record for contract {record.contract_data.contract_id}")
        except Exception as e:
            logging.error(f"Error saving performance record: {e}")
            raise

    def get_project_usage(self, project_id: str, activity_code: str) -> float:
        """获取项目累计使用金额（北京工单上限用）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # 返回字典格式
                cursor = conn.execute("""
                    SELECT * FROM performance_data
                    WHERE activity_code = ?
                    ORDER BY created_at
                """, (activity_code,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting all records: {e}")
            return []


class CSVPerformanceDataStore(PerformanceDataStore):
    """CSV实现 - 向后兼容现有系统"""

    def __init__(self, performance_file: str):
        self.performance_file = performance_file

    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """检查合同是否已存在 - 兼容现有的CSV查询方式"""
        if not os.path.exists(self.performance_file):
            return False

        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row.get('合同ID(_id)') == contract_id and
                        row.get('活动编号') == activity_code):
                        return True
            return False
        except Exception as e:
            logging.error(f"Error checking contract existence in CSV: {e}")
            return False

    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> HousekeeperStats:
        """从CSV文件计算管家统计 - 兼容现有逻辑"""
        stats = HousekeeperStats(housekeeper=housekeeper, activity_code=activity_code)

        if not os.path.exists(self.performance_file):
            return stats

        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row.get('管家(serviceHousekeeper)') == housekeeper and
                        row.get('活动编号') == activity_code):

                        stats.contract_count += 1
                        stats.total_amount += float(row.get('合同金额(adjustRefundMoney)', 0))
                        stats.performance_amount += float(row.get('计入业绩金额', 0))

                        # 双轨统计
                        if row.get('工单类型') == '平台单':
                            stats.platform_count += 1
                            stats.platform_amount += float(row.get('合同金额(adjustRefundMoney)', 0))
                        elif row.get('工单类型') == '自引单':
                            stats.self_referral_count += 1
                            stats.self_referral_amount += float(row.get('合同金额(adjustRefundMoney)', 0))

                        # 收集奖励信息
                        reward_types = row.get('奖励类型', '')
                        if reward_types and reward_types not in stats.awarded:
                            stats.awarded.append(reward_types)

            return stats
        except Exception as e:
            logging.error(f"Error getting housekeeper stats from CSV: {e}")
            return stats

    def get_housekeeper_awards(self, housekeeper: str, activity_code: str) -> List[str]:
        """获取管家历史奖励列表"""
        awards = []

        if not os.path.exists(self.performance_file):
            return awards

        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row.get('管家(serviceHousekeeper)') == housekeeper and
                        row.get('活动编号') == activity_code):
                        reward_types = row.get('奖励类型', '')
                        if reward_types and reward_types not in awards:
                            awards.append(reward_types)

            return awards
        except Exception as e:
            logging.error(f"Error getting housekeeper awards from CSV: {e}")
            return []

    def save_performance_record(self, record: PerformanceRecord) -> None:
        """保存业绩记录到CSV - 兼容现有格式"""
        try:
            # 转换为字典格式
            record_dict = record.to_dict()

            # 检查文件是否存在，如果不存在则创建
            file_exists = os.path.exists(self.performance_file)

            with open(self.performance_file, 'a', newline='', encoding='utf-8') as f:
                if record_dict:
                    writer = csv.DictWriter(f, fieldnames=record_dict.keys())

                    # 如果文件不存在，写入表头
                    if not file_exists:
                        writer.writeheader()

                    writer.writerow(record_dict)

            logging.debug(f"Saved performance record to CSV: {record.contract_data.contract_id}")
        except Exception as e:
            logging.error(f"Error saving performance record to CSV: {e}")
            raise

    def get_project_usage(self, project_id: str, activity_code: str) -> float:
        """获取项目累计使用金额"""
        total_usage = 0.0

        if not os.path.exists(self.performance_file):
            return total_usage

        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row.get('工单编号(serviceAppointmentNum)') == project_id and
                        row.get('活动编号') == activity_code):
                        total_usage += float(row.get('计入业绩金额', 0))

            return total_usage
        except Exception as e:
            logging.error(f"Error getting project usage from CSV: {e}")
            return 0.0

    def get_all_records(self, activity_code: str) -> List[Dict]:
        """获取指定活动的所有记录"""
        records = []

        if not os.path.exists(self.performance_file):
            return records

        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('活动编号') == activity_code:
                        records.append(dict(row))

            return records
        except Exception as e:
            logging.error(f"Error getting all records from CSV: {e}")
            return []


def create_data_store(storage_type: str = "sqlite", **kwargs) -> PerformanceDataStore:
    """工厂函数：创建数据存储实例"""
    if storage_type.lower() == "sqlite":
        db_path = kwargs.get('db_path', 'performance_data.db')
        return SQLitePerformanceDataStore(db_path)
    elif storage_type.lower() == "csv":
        performance_file = kwargs.get('performance_file')
        if not performance_file:
            raise ValueError("CSV storage requires 'performance_file' parameter")
        return CSVPerformanceDataStore(performance_file)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
