"""
销售激励系统重构 - 核心架构测试
版本: v1.0
创建日期: 2025-01-08

测试新的核心架构组件是否正常工作。
"""

import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock

# 导入核心模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.core import (
    HousekeeperStats, ProcessingConfig, ContractData, RewardInfo,
    SQLitePerformanceDataStore, CSVPerformanceDataStore,
    RewardCalculator, RecordBuilder, DataProcessingPipeline,
    City, OrderType, create_standard_pipeline
)


class TestDataModels(unittest.TestCase):
    """测试数据模型"""
    
    def test_housekeeper_stats_creation(self):
        """测试管家统计数据创建"""
        stats = HousekeeperStats(
            housekeeper="张三",
            activity_code="BJ-JUN",
            contract_count=5,
            total_amount=100000.0
        )
        
        self.assertEqual(stats.housekeeper, "张三")
        self.assertEqual(stats.activity_code, "BJ-JUN")
        self.assertEqual(stats.contract_count, 5)
        self.assertEqual(stats.total_amount, 100000.0)
        
        # 测试转换为字典
        stats_dict = stats.to_dict()
        self.assertEqual(stats_dict['count'], 5)
        self.assertEqual(stats_dict['total_amount'], 100000.0)
    
    def test_processing_config_creation(self):
        """测试处理配置创建"""
        config = ProcessingConfig(
            config_key="BJ-2025-06",
            activity_code="BJ-JUN",
            city=City.BEIJING,
            housekeeper_key_format="管家"
        )
        
        self.assertEqual(config.config_key, "BJ-2025-06")
        self.assertEqual(config.city, City.BEIJING)
        self.assertFalse(config.enable_dual_track)
    
    def test_contract_data_from_dict(self):
        """测试从字典创建合同数据"""
        contract_dict = {
            '合同ID(_id)': '12345',
            '管家(serviceHousekeeper)': '张三',
            '服务商(orgName)': '测试服务商',
            '合同金额(adjustRefundMoney)': 50000,
            '支付金额(paidAmount)': 30000,
            '款项来源类型(tradeIn)': 1
        }
        
        contract_data = ContractData.from_dict(contract_dict)
        
        self.assertEqual(contract_data.contract_id, '12345')
        self.assertEqual(contract_data.housekeeper, '张三')
        self.assertEqual(contract_data.contract_amount, 50000)
        self.assertEqual(contract_data.order_type, OrderType.SELF_REFERRAL)


class TestSQLiteStorage(unittest.TestCase):
    """测试SQLite存储"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.store = SQLitePerformanceDataStore(self.temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """测试数据库初始化"""
        # 检查数据库文件是否存在
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # 检查表是否创建
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='performance_data'
            """)
            self.assertIsNotNone(cursor.fetchone())
    
    def test_contract_exists(self):
        """测试合同存在性检查"""
        # 初始状态应该不存在
        self.assertFalse(self.store.contract_exists('12345', 'BJ-JUN'))
        
        # 插入一条记录
        with sqlite3.connect(self.temp_db.name) as conn:
            conn.execute("""
                INSERT INTO performance_data (activity_code, contract_id, housekeeper, contract_amount, performance_amount)
                VALUES (?, ?, ?, ?, ?)
            """, ('BJ-JUN', '12345', '张三', 50000, 50000))
        
        # 现在应该存在
        self.assertTrue(self.store.contract_exists('12345', 'BJ-JUN'))
        # 不同活动编码应该不存在
        self.assertFalse(self.store.contract_exists('12345', 'SH-APR'))
    
    def test_housekeeper_stats(self):
        """测试管家统计查询"""
        # 插入测试数据
        with sqlite3.connect(self.temp_db.name) as conn:
            conn.execute("""
                INSERT INTO performance_data (activity_code, contract_id, housekeeper, contract_amount, performance_amount, order_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('BJ-JUN', '12345', '张三', 50000, 50000, 'platform'))
            
            conn.execute("""
                INSERT INTO performance_data (activity_code, contract_id, housekeeper, contract_amount, performance_amount, order_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('BJ-JUN', '12346', '张三', 30000, 30000, 'self_referral'))
        
        # 查询统计数据
        stats = self.store.get_housekeeper_stats('张三', 'BJ-JUN')
        
        self.assertEqual(stats.contract_count, 2)
        self.assertEqual(stats.total_amount, 80000)
        self.assertEqual(stats.performance_amount, 80000)
        self.assertEqual(stats.platform_count, 1)
        self.assertEqual(stats.platform_amount, 50000)
        self.assertEqual(stats.self_referral_count, 1)
        self.assertEqual(stats.self_referral_amount, 30000)


class TestRewardCalculator(unittest.TestCase):
    """测试奖励计算器"""
    
    def setUp(self):
        """设置测试环境"""
        # Mock配置
        self.mock_config = {
            "lucky_number": "8",
            "lucky_rewards": {
                "base": {"name": "接好运", "threshold": 0},
                "high": {"name": "接好运万元以上", "threshold": 10000}
            },
            "tiered_rewards": {
                "min_contracts": 6,
                "tiers": [
                    {"name": "达标奖", "threshold": 80000},
                    {"name": "优秀奖", "threshold": 120000}
                ]
            }
        }
    
    @patch('modules.core.reward_calculator.REWARD_CONFIGS')
    def test_lucky_reward_calculation(self, mock_configs):
        """测试幸运数字奖励计算"""
        mock_configs.get.return_value = self.mock_config
        
        calculator = RewardCalculator("BJ-2025-06")
        
        # 创建包含幸运数字的合同
        contract_data = ContractData(
            contract_id="12345678",  # 包含幸运数字8
            housekeeper="张三",
            service_provider="测试服务商",
            contract_amount=15000
        )
        
        housekeeper_stats = HousekeeperStats(
            housekeeper="张三",
            activity_code="BJ-JUN"
        )
        
        rewards = calculator.calculate(contract_data, housekeeper_stats)
        
        # 应该获得高额幸运数字奖励
        self.assertEqual(len(rewards), 1)
        self.assertEqual(rewards[0].reward_name, "接好运万元以上")
    
    @patch('modules.core.reward_calculator.REWARD_CONFIGS')
    def test_tiered_reward_calculation(self, mock_configs):
        """测试节节高奖励计算"""
        mock_configs.get.return_value = self.mock_config
        
        calculator = RewardCalculator("BJ-2025-06")
        
        contract_data = ContractData(
            contract_id="12345",
            housekeeper="张三",
            service_provider="测试服务商",
            contract_amount=50000
        )
        
        # 创建达到达标奖门槛的管家统计
        housekeeper_stats = HousekeeperStats(
            housekeeper="张三",
            activity_code="BJ-JUN",
            contract_count=6,
            performance_amount=85000
        )
        
        rewards = calculator.calculate(contract_data, housekeeper_stats)
        
        # 应该获得达标奖
        tiered_rewards = [r for r in rewards if r.reward_type == "节节高"]
        self.assertEqual(len(tiered_rewards), 1)
        self.assertEqual(tiered_rewards[0].reward_name, "达标奖")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_create_standard_pipeline(self):
        """测试创建标准处理管道"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()
            
            try:
                pipeline, config, store = create_standard_pipeline(
                    config_key="BJ-2025-06",
                    activity_code="BJ-JUN",
                    city="BJ",
                    db_path=temp_db.name
                )
                
                self.assertIsInstance(pipeline, DataProcessingPipeline)
                self.assertEqual(config.activity_code, "BJ-JUN")
                self.assertEqual(config.city, City.BEIJING)
                self.assertIsInstance(store, SQLitePerformanceDataStore)
                
            finally:
                os.unlink(temp_db.name)


if __name__ == '__main__':
    unittest.main()
