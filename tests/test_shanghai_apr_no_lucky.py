"""
测试上海4月配置禁用幸运奖的功能
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.data_processing_module import determine_rewards_apr_shanghai_generic

class TestShanghaiAprNoLucky(unittest.TestCase):
    """测试上海4月配置禁用幸运奖的功能"""
    
    def test_no_lucky_rewards_with_lucky_number(self):
        """测试幸运数字不会触发幸运奖"""

        # 测试幸运数字6，低金额 - 使用独立的数据
        housekeeper_data1 = {
            'count': 5,
            'total_amount': 50000,
            'performance_amount': 50000,
            'awarded': []
        }

        reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
            contract_number=16,  # 末位为6，但不应该触发幸运奖
            housekeeper_data=housekeeper_data1,
            current_contract_amount=5000
        )

        print(f"幸运数字6低金额结果: {reward_types}, {reward_names}")

        # 验证没有幸运奖
        self.assertNotIn("幸运数字", reward_types)
        self.assertNotIn("接好运", reward_names)
        self.assertNotIn("接好运万元以上", reward_names)

        # 但应该有节节高奖励
        self.assertIn("节节高", reward_types)
        self.assertIn("基础奖", reward_names)

        # 测试幸运数字6，高金额 - 使用独立的数据
        housekeeper_data2 = {
            'count': 5,
            'total_amount': 50000,
            'performance_amount': 50000,
            'awarded': []
        }

        reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
            contract_number=26,  # 末位为6，但不应该触发幸运奖
            housekeeper_data=housekeeper_data2,
            current_contract_amount=15000
        )

        print(f"幸运数字6高金额结果: {reward_types}, {reward_names}")

        # 验证没有幸运奖
        self.assertNotIn("幸运数字", reward_types)
        self.assertNotIn("接好运", reward_names)
        self.assertNotIn("接好运万元以上", reward_names)

        # 但应该有节节高奖励
        self.assertIn("节节高", reward_types)
        self.assertIn("基础奖", reward_names)
    
    def test_other_lucky_numbers_also_disabled(self):
        """测试其他可能的幸运数字也不会触发奖励"""

        # 测试各种可能的"幸运"数字
        lucky_numbers = [8, 18, 28, 38, 9, 19, 29]

        for number in lucky_numbers:
            with self.subTest(contract_number=number):
                # 每个测试使用独立的数据
                housekeeper_data = {
                    'count': 5,
                    'total_amount': 50000,
                    'performance_amount': 50000,
                    'awarded': []
                }

                reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
                    contract_number=number,
                    housekeeper_data=housekeeper_data,
                    current_contract_amount=15000
                )

                # 验证没有任何幸运奖
                self.assertNotIn("幸运数字", reward_types)
                self.assertNotIn("接好运", reward_names)
                self.assertNotIn("接好运万元以上", reward_names)

                # 但应该有节节高奖励
                self.assertIn("节节高", reward_types)
                self.assertIn("基础奖", reward_names)
    
    def test_tiered_rewards_still_work(self):
        """测试节节高奖励仍然正常工作"""
        test_cases = [
            # 基础奖
            {'amount': 45000, 'expected_rewards': ['基础奖']},
            # 达标奖
            {'amount': 65000, 'expected_rewards': ['基础奖', '达标奖']},
            # 优秀奖
            {'amount': 85000, 'expected_rewards': ['基础奖', '达标奖', '优秀奖']},
            # 精英奖
            {'amount': 125000, 'expected_rewards': ['基础奖', '达标奖', '优秀奖', '精英奖']},
            # 卓越奖
            {'amount': 165000, 'expected_rewards': ['基础奖', '达标奖', '优秀奖', '精英奖', '卓越奖']},
        ]
        
        for case in test_cases:
            with self.subTest(amount=case['amount']):
                housekeeper_data = {
                    'count': 5,
                    'total_amount': case['amount'],
                    'performance_amount': case['amount'],
                    'awarded': []
                }
                
                reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
                    contract_number=16,  # 使用可能的幸运数字，确保不影响节节高
                    housekeeper_data=housekeeper_data,
                    current_contract_amount=5000
                )
                
                print(f"金额{case['amount']}结果: {reward_types}, {reward_names}")
                
                # 验证没有幸运奖
                self.assertNotIn("幸运数字", reward_types)
                
                # 验证有节节高奖励
                self.assertIn("节节高", reward_types)
                
                # 验证具体的奖励等级
                for expected_reward in case['expected_rewards']:
                    self.assertIn(expected_reward, reward_names)
                    self.assertIn(expected_reward, housekeeper_data['awarded'])
    
    def test_configuration_is_correct(self):
        """测试配置是否正确设置"""
        import modules.config
        
        # 验证配置存在
        self.assertIn("SH-2025-04", modules.config.REWARD_CONFIGS)
        
        config = modules.config.REWARD_CONFIGS["SH-2025-04"]
        
        # 验证幸运数字被禁用
        self.assertEqual(config.get("lucky_number", ""), "")
        
        # 验证节节高配置正常
        self.assertEqual(config["tiered_rewards"]["min_contracts"], 5)
        self.assertEqual(len(config["tiered_rewards"]["tiers"]), 5)
        
        # 验证奖励等级
        tier_names = [tier["name"] for tier in config["tiered_rewards"]["tiers"]]
        expected_names = ["基础奖", "达标奖", "优秀奖", "精英奖", "卓越奖"]
        self.assertEqual(tier_names, expected_names)

if __name__ == '__main__':
    unittest.main(verbosity=2)
