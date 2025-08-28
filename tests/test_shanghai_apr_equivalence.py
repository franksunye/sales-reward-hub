"""
功能等价性验证测试：确保 determine_rewards_shanghai_apr 和 determine_rewards_apr_shanghai_generic 
在所有场景下输出完全一致。

这是生产环境替换前的关键验证步骤。
"""

import unittest
import sys
import os
import copy
from datetime import date
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.data_processing_module import (
    determine_rewards_shanghai_apr,
    determine_rewards_apr_shanghai_generic
)
import modules.config

class TestShanghaiAprEquivalence(unittest.TestCase):
    """测试上海4月奖励函数的功能等价性"""
    
    def setUp(self):
        """每个测试用例前的初始化"""
        self.base_housekeeper_data = {
            'count': 0,
            'total_amount': 0,
            'performance_amount': 0,
            'awarded': []
        }
    
    def compare_functions(self, contract_number, housekeeper_data, contract_amount, test_name=""):
        """比较两个函数的输出是否完全一致"""
        # 深拷贝数据，避免函数修改影响比较
        data_original = copy.deepcopy(housekeeper_data)
        data_generic = copy.deepcopy(housekeeper_data)
        
        # 调用原函数
        result_original = determine_rewards_shanghai_apr(
            contract_number, data_original, contract_amount
        )
        
        # 调用通用函数
        result_generic = determine_rewards_apr_shanghai_generic(
            contract_number, data_generic, contract_amount
        )
        
        # 打印详细信息用于调试
        if result_original != result_generic:
            print(f"\n=== 不一致检测 - {test_name} ===")
            print(f"输入参数:")
            print(f"  合同编号: {contract_number}")
            print(f"  管家数据: {housekeeper_data}")
            print(f"  合同金额: {contract_amount}")
            print(f"原函数结果: {result_original}")
            print(f"通用函数结果: {result_generic}")
            print(f"原函数修改后的数据: {data_original}")
            print(f"通用函数修改后的数据: {data_generic}")
        
        # 验证结果完全一致
        self.assertEqual(result_original, result_generic, 
                        f"{test_name}: 函数输出不一致")
        
        # 验证数据修改也一致（awarded字段）
        self.assertEqual(data_original, data_generic, 
                        f"{test_name}: 数据修改不一致")
    
    def test_no_rewards_scenario(self):
        """测试无奖励场景"""
        test_cases = [
            # 合同数量不足
            {'count': 4, 'total_amount': 50000, 'performance_amount': 50000, 'awarded': []},
            # 金额不足
            {'count': 5, 'total_amount': 30000, 'performance_amount': 30000, 'awarded': []},
            # 零值
            {'count': 0, 'total_amount': 0, 'performance_amount': 0, 'awarded': []},
        ]
        
        for i, data in enumerate(test_cases):
            with self.subTest(case=i):
                self.compare_functions(11, data, 5000, f"无奖励场景{i+1}")
    
    def test_basic_tier_rewards(self):
        """测试基础档位奖励"""
        test_cases = [
            # 基础奖
            {'count': 5, 'total_amount': 40000, 'performance_amount': 40000, 'awarded': []},
            # 达标奖
            {'count': 5, 'total_amount': 60000, 'performance_amount': 60000, 'awarded': []},
            # 优秀奖
            {'count': 5, 'total_amount': 80000, 'performance_amount': 80000, 'awarded': []},
            # 精英奖
            {'count': 5, 'total_amount': 120000, 'performance_amount': 120000, 'awarded': []},
            # 卓越奖
            {'count': 5, 'total_amount': 160000, 'performance_amount': 160000, 'awarded': []},
        ]
        
        for i, data in enumerate(test_cases):
            with self.subTest(case=i):
                self.compare_functions(11, data, 5000, f"基础档位{i+1}")
    
    def test_boundary_values(self):
        """测试边界值"""
        boundary_amounts = [39999, 40000, 40001, 59999, 60000, 60001, 
                           79999, 80000, 80001, 119999, 120000, 120001,
                           159999, 160000, 160001]
        
        for amount in boundary_amounts:
            data = {'count': 5, 'total_amount': amount, 'performance_amount': amount, 'awarded': []}
            with self.subTest(amount=amount):
                self.compare_functions(11, data, 5000, f"边界值{amount}")
    
    @patch('modules.data_processing_module.date')
    def test_lucky_number_in_june(self, mock_date):
        """测试6月份的幸运数字逻辑（原函数的特殊逻辑）"""
        # 模拟6月份
        mock_date.today.return_value.month = 6
        
        test_cases = [
            # 幸运数字6，低金额
            {'contract_number': 16, 'amount': 5000, 'expected_lucky': True},
            # 幸运数字6，高金额
            {'contract_number': 26, 'amount': 15000, 'expected_lucky': True},
            # 非幸运数字
            {'contract_number': 15, 'amount': 5000, 'expected_lucky': False},
        ]
        
        for case in test_cases:
            data = {'count': 5, 'total_amount': 50000, 'performance_amount': 50000, 'awarded': []}
            with self.subTest(contract_number=case['contract_number']):
                self.compare_functions(
                    case['contract_number'], data, case['amount'], 
                    f"6月幸运数字{case['contract_number']}"
                )
    
    @patch('modules.data_processing_module.date')
    def test_lucky_number_not_in_june(self, mock_date):
        """测试非6月份的幸运数字逻辑（应该没有幸运数字奖励）"""
        # 模拟4月份
        mock_date.today.return_value.month = 4
        
        data = {'count': 5, 'total_amount': 50000, 'performance_amount': 50000, 'awarded': []}
        
        # 在4月份，即使是幸运数字6也不应该有奖励（原函数的逻辑）
        self.compare_functions(16, data, 15000, "4月幸运数字6")
        self.compare_functions(26, data, 5000, "4月幸运数字6_低金额")
    
    def test_performance_cap_scenarios(self):
        """测试业绩上限场景"""
        # 测试启用和禁用业绩上限的情况
        original_cap = modules.config.ENABLE_PERFORMANCE_AMOUNT_CAP
        original_config = modules.config.REWARD_CONFIGS["SH-2025-04"]["performance_limits"]["enable_cap"]

        try:
            # 测试禁用业绩上限
            modules.config.ENABLE_PERFORMANCE_AMOUNT_CAP = False
            modules.config.REWARD_CONFIGS["SH-2025-04"]["performance_limits"]["enable_cap"] = False
            data = {'count': 5, 'total_amount': 100000, 'performance_amount': 50000, 'awarded': []}
            self.compare_functions(11, data, 5000, "禁用业绩上限")

            # 测试启用业绩上限
            modules.config.ENABLE_PERFORMANCE_AMOUNT_CAP = True
            modules.config.REWARD_CONFIGS["SH-2025-04"]["performance_limits"]["enable_cap"] = True
            data = {'count': 5, 'total_amount': 100000, 'performance_amount': 50000, 'awarded': []}
            self.compare_functions(11, data, 5000, "启用业绩上限")

        finally:
            # 恢复原始配置
            modules.config.ENABLE_PERFORMANCE_AMOUNT_CAP = original_cap
            modules.config.REWARD_CONFIGS["SH-2025-04"]["performance_limits"]["enable_cap"] = original_config
    
    def test_already_awarded_scenarios(self):
        """测试已获奖场景"""
        test_cases = [
            # 已获得基础奖
            {'count': 5, 'total_amount': 60000, 'performance_amount': 60000, 'awarded': ['基础奖']},
            # 已获得多个奖项
            {'count': 5, 'total_amount': 120000, 'performance_amount': 120000, 'awarded': ['基础奖', '达标奖']},
            # 已获得所有奖项
            {'count': 5, 'total_amount': 200000, 'performance_amount': 200000, 
             'awarded': ['基础奖', '达标奖', '优秀奖', '精英奖', '卓越奖']},
        ]
        
        for i, data in enumerate(test_cases):
            with self.subTest(case=i):
                self.compare_functions(11, data, 5000, f"已获奖场景{i+1}")
    
    def test_edge_cases(self):
        """测试边缘情况"""
        # 极大数值
        data = {'count': 100, 'total_amount': 1000000, 'performance_amount': 1000000, 'awarded': []}
        self.compare_functions(99, data, 50000, "极大数值")
        
        # 合同数量刚好达标
        data = {'count': 5, 'total_amount': 40000, 'performance_amount': 40000, 'awarded': []}
        self.compare_functions(11, data, 5000, "合同数量刚好达标")

if __name__ == '__main__':
    unittest.main(verbosity=2)
