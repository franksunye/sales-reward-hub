"""
TDD测试：上海9月自引单奖励功能
测试 determine_self_referral_rewards() 函数的核心逻辑
"""

import unittest
import sys
import os
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置模块
import modules.config

class TestSelfReferralRewards(unittest.TestCase):
    """测试自引单奖励计算功能"""
    
    def setUp(self):
        """每个测试用例前的初始化"""
        self.config_key = "SH-2025-09"
        self.base_housekeeper_data = {
            'count': 0,
            'total_amount': 0,
            'performance_amount': 0,
            'awarded': [],
            'platform_count': 0,
            'platform_amount': 0,
            'self_referral_count': 0,
            'self_referral_amount': 0,
            'self_referral_projects': set(),
            'self_referral_rewards': 0
        }
    
    def test_self_referral_config_exists(self):
        """测试：自引单配置是否存在"""
        # 这个测试会失败，因为我们还没有添加配置
        # 这是TDD的第一步：写一个失败的测试
        
        # 期望的配置结构
        expected_config = {
            "enable": True,
            "reward_type": "自引单",
            "reward_name": "红包",
            "deduplication_field": "projectAddress"
        }
        
        # 检查配置是否存在
        self.assertIn(self.config_key, modules.config.REWARD_CONFIGS)
        config = modules.config.REWARD_CONFIGS[self.config_key]
        self.assertIn("self_referral_rewards", config)
        
        self_referral_config = config["self_referral_rewards"]
        for key, value in expected_config.items():
            self.assertEqual(self_referral_config[key], value)
    
    def test_get_self_referral_config_function_exists(self):
        """测试：get_self_referral_config函数是否存在"""
        # 这个测试也会失败，因为函数还不存在
        from modules.data_processing_module import get_self_referral_config
        
        config = get_self_referral_config(self.config_key)
        self.assertIsInstance(config, dict)
        self.assertIn("enable", config)
        self.assertIn("reward_type", config)
        self.assertIn("reward_name", config)
        self.assertIn("deduplication_field", config)
    
    def test_determine_self_referral_rewards_function_exists(self):
        """测试：determine_self_referral_rewards函数是否存在"""
        # 这个测试会失败，因为函数还不存在
        from modules.data_processing_module import determine_self_referral_rewards
        
        # 测试函数签名
        project_address = "上海市浦东新区科技园456号"
        housekeeper_data = self.base_housekeeper_data.copy()
        
        result = determine_self_referral_rewards(project_address, housekeeper_data, self.config_key)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
    
    def test_first_self_referral_project_gets_reward(self):
        """测试：第一个自引单项目应该获得奖励"""
        from modules.data_processing_module import determine_self_referral_rewards
        
        project_address = "上海市浦东新区科技园456号"
        housekeeper_data = self.base_housekeeper_data.copy()
        
        reward_type, reward_name, is_qualified = determine_self_referral_rewards(
            project_address, housekeeper_data, self.config_key
        )
        
        # 验证返回值
        self.assertEqual(reward_type, "自引单")
        self.assertEqual(reward_name, "红包")
        self.assertTrue(is_qualified)
        
        # 验证管家数据更新
        self.assertIn(project_address, housekeeper_data['self_referral_projects'])
        self.assertEqual(housekeeper_data['self_referral_rewards'], 1)
    
    def test_duplicate_project_address_no_reward(self):
        """测试：重复的项目地址不应该获得奖励"""
        from modules.data_processing_module import determine_self_referral_rewards
        
        project_address = "上海市浦东新区科技园456号"
        housekeeper_data = self.base_housekeeper_data.copy()
        
        # 第一次调用，应该获得奖励
        reward_type1, reward_name1, is_qualified1 = determine_self_referral_rewards(
            project_address, housekeeper_data, self.config_key
        )
        self.assertTrue(is_qualified1)
        self.assertEqual(housekeeper_data['self_referral_rewards'], 1)
        
        # 第二次调用相同地址，不应该获得奖励
        reward_type2, reward_name2, is_qualified2 = determine_self_referral_rewards(
            project_address, housekeeper_data, self.config_key
        )
        self.assertEqual(reward_type2, "")
        self.assertEqual(reward_name2, "")
        self.assertFalse(is_qualified2)
        self.assertEqual(housekeeper_data['self_referral_rewards'], 1)  # 数量不变
    
    def test_different_project_addresses_get_rewards(self):
        """测试：不同的项目地址都应该获得奖励"""
        from modules.data_processing_module import determine_self_referral_rewards
        
        housekeeper_data = self.base_housekeeper_data.copy()
        
        # 第一个项目地址
        project1 = "上海市浦东新区科技园456号"
        reward_type1, reward_name1, is_qualified1 = determine_self_referral_rewards(
            project1, housekeeper_data, self.config_key
        )
        self.assertTrue(is_qualified1)
        self.assertEqual(housekeeper_data['self_referral_rewards'], 1)
        
        # 第二个项目地址
        project2 = "上海市徐汇区漕河泾开发区789号"
        reward_type2, reward_name2, is_qualified2 = determine_self_referral_rewards(
            project2, housekeeper_data, self.config_key
        )
        self.assertTrue(is_qualified2)
        self.assertEqual(housekeeper_data['self_referral_rewards'], 2)
        
        # 验证两个地址都在集合中
        self.assertIn(project1, housekeeper_data['self_referral_projects'])
        self.assertIn(project2, housekeeper_data['self_referral_projects'])
    
    def test_disabled_self_referral_no_rewards(self):
        """测试：禁用自引单奖励时不应该获得奖励"""
        # 这个测试需要模拟配置被禁用的情况
        with patch('modules.config.REWARD_CONFIGS') as mock_config:
            mock_config.__getitem__.return_value = {
                "self_referral_rewards": {
                    "enable": False,  # 禁用
                    "reward_type": "自引单",
                    "reward_name": "红包",
                    "deduplication_field": "projectAddress"
                }
            }
            
            from modules.data_processing_module import determine_self_referral_rewards
            
            project_address = "上海市浦东新区科技园456号"
            housekeeper_data = self.base_housekeeper_data.copy()
            
            reward_type, reward_name, is_qualified = determine_self_referral_rewards(
                project_address, housekeeper_data, self.config_key
            )
            
            self.assertEqual(reward_type, "")
            self.assertEqual(reward_name, "")
            self.assertFalse(is_qualified)
            self.assertEqual(housekeeper_data['self_referral_rewards'], 0)

if __name__ == '__main__':
    unittest.main()
