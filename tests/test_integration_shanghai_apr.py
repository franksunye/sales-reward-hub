"""
集成测试：验证替换后的上海4月奖励函数在实际场景中正常工作
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.data_processing_module import determine_rewards_apr_shanghai_generic

class TestShanghaiAprIntegration(unittest.TestCase):
    """测试替换后的上海4月奖励函数集成功能"""
    
    def test_real_scenario_basic_reward(self):
        """测试真实场景：基础奖励"""
        housekeeper_data = {
            'count': 5,
            'total_amount': 45000,
            'performance_amount': 45000,
            'awarded': []
        }
        
        reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
            contract_number=12345,
            housekeeper_data=housekeeper_data,
            current_contract_amount=5000
        )
        
        self.assertEqual(reward_types, "节节高")
        self.assertEqual(reward_names, "基础奖")
        self.assertIn("距离 达标奖 还需", gap)
        self.assertIn("基础奖", housekeeper_data['awarded'])
    
    def test_real_scenario_no_lucky_number(self):
        """测试真实场景：确认幸运数字奖励已禁用"""
        housekeeper_data = {
            'count': 5,
            'total_amount': 30000,
            'performance_amount': 30000,
            'awarded': []
        }

        reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
            contract_number=16,  # 末位为6，但幸运奖已禁用
            housekeeper_data=housekeeper_data,
            current_contract_amount=15000
        )

        # 验证幸运奖已禁用
        self.assertNotIn("幸运数字", reward_types)
        self.assertNotIn("接好运", reward_names)
        self.assertNotIn("接好运万元以上", reward_names)
    
    def test_real_scenario_tiered_rewards_only(self):
        """测试真实场景：只有节节高奖励（幸运奖已禁用）"""
        housekeeper_data = {
            'count': 5,
            'total_amount': 65000,
            'performance_amount': 65000,
            'awarded': []
        }

        reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
            contract_number=26,  # 末位为6，但幸运奖已禁用
            housekeeper_data=housekeeper_data,
            current_contract_amount=12000
        )

        # 应该只有节节高奖励，没有幸运奖
        self.assertNotIn("幸运数字", reward_types)
        self.assertIn("节节高", reward_types)
        self.assertNotIn("接好运", reward_names)
        self.assertNotIn("接好运万元以上", reward_names)
        self.assertIn("基础奖", reward_names)
        self.assertIn("达标奖", reward_names)
    
    def test_real_scenario_no_rewards(self):
        """测试真实场景：无奖励"""
        housekeeper_data = {
            'count': 4,  # 未达到最低合同数量
            'total_amount': 30000,
            'performance_amount': 30000,
            'awarded': []
        }
        
        reward_types, reward_names, gap = determine_rewards_apr_shanghai_generic(
            contract_number=15,  # 非幸运数字
            housekeeper_data=housekeeper_data,
            current_contract_amount=5000
        )
        
        self.assertEqual(reward_types, "")
        self.assertEqual(reward_names, "")
        self.assertIn("距离达成节节高奖励条件还需", gap)
    
    def test_configuration_loaded_correctly(self):
        """测试配置是否正确加载"""
        import modules.config
        
        # 验证配置存在
        self.assertIn("SH-2025-04", modules.config.REWARD_CONFIGS)
        
        config = modules.config.REWARD_CONFIGS["SH-2025-04"]
        
        # 验证关键配置项
        self.assertEqual(config["lucky_number"], "")  # 幸运奖已禁用
        self.assertEqual(config["tiered_rewards"]["min_contracts"], 5)
        self.assertEqual(len(config["tiered_rewards"]["tiers"]), 5)
        
        # 验证奖励等级
        tier_names = [tier["name"] for tier in config["tiered_rewards"]["tiers"]]
        expected_names = ["基础奖", "达标奖", "优秀奖", "精英奖", "卓越奖"]
        self.assertEqual(tier_names, expected_names)

if __name__ == '__main__':
    unittest.main(verbosity=2)
