"""
北京9月新功能测试 - TDD测试先行
这些测试定义了北京9月活动的期望行为，必须先写测试再写实现
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.config import REWARD_CONFIGS


class TestBeijingSepConfig:
    """测试北京9月配置"""
    
    def test_bj_2025_09_config_exists(self):
        """测试BJ-2025-09配置存在且正确"""
        config = REWARD_CONFIGS.get("BJ-2025-09")
        assert config is not None, "BJ-2025-09配置必须存在"
        
        # 验证幸运数字配置
        assert config["lucky_number"] == "5", "幸运数字必须是5"
        assert config.get("lucky_number_mode") == "personal_sequence", "必须是个人顺序模式"
        
        # 验证幸运奖励统一
        lucky_rewards = config["lucky_rewards"]
        assert lucky_rewards["base"]["name"] == "接好运", "基础奖励名称必须是接好运"
        assert lucky_rewards["high"]["threshold"] >= 999999, "高额门槛必须很大，实现统一奖励"
        
        # 验证节节高门槛提升
        tiered_rewards = config["tiered_rewards"]
        assert tiered_rewards["min_contracts"] == 10, "最低合同数必须是10"
        
        # 验证奖励金额翻倍
        awards_mapping = config["awards_mapping"]
        assert awards_mapping["接好运"] == "58", "接好运奖励必须是58元"
        assert awards_mapping["达标奖"] == "400", "达标奖必须是400元"
        assert awards_mapping["优秀奖"] == "800", "优秀奖必须是800元"
        assert awards_mapping["精英奖"] == "1600", "精英奖必须是1600元"
        
        # 验证徽章禁用
        badge_config = config.get("badge_config", {})
        assert badge_config.get("enable_elite_badge") == False, "精英徽章必须禁用"
        assert badge_config.get("enable_rising_star_badge") == False, "新星徽章必须禁用"
        
        # 验证工单金额上限调整
        performance_limits = config["performance_limits"]
        assert performance_limits["single_project_limit"] == 50000, "工单上限必须是5万"
        assert performance_limits["single_contract_cap"] == 50000, "合同上限必须是5万"


class TestPersonalSequenceLuckyNumber:
    """测试基于个人顺序的幸运数字"""
    
    def test_lucky_number_generic_function_exists(self):
        """测试幸运数字通用函数存在"""
        try:
            from modules.data_processing_module import determine_lucky_number_reward_generic
            assert callable(determine_lucky_number_reward_generic), "通用幸运数字函数必须可调用"
        except ImportError:
            pytest.skip("通用幸运数字函数尚未实现")
    
    def test_personal_sequence_mode_5th_contract(self):
        """测试第5个合同获得幸运奖励"""
        try:
            from modules.data_processing_module import determine_lucky_number_reward_generic
            
            # 第5个合同应该获得奖励
            reward_type, reward_name = determine_lucky_number_reward_generic(
                contract_number=123,  # 合同编号不重要
                current_contract_amount=8000,  # 金额不重要
                housekeeper_contract_count=5,  # 第5个合同
                config_key="BJ-2025-09"
            )
            
            assert reward_type == "幸运数字", "第5个合同应该获得幸运数字奖励"
            assert reward_name == "接好运", "奖励名称应该是接好运"
            
        except ImportError:
            pytest.skip("通用幸运数字函数尚未实现")
    
    def test_personal_sequence_mode_10th_contract(self):
        """测试第10个合同获得幸运奖励"""
        try:
            from modules.data_processing_module import determine_lucky_number_reward_generic
            
            # 第10个合同应该获得奖励
            reward_type, reward_name = determine_lucky_number_reward_generic(
                contract_number=456,
                current_contract_amount=15000,
                housekeeper_contract_count=10,  # 第10个合同
                config_key="BJ-2025-09"
            )
            
            assert reward_type == "幸运数字", "第10个合同应该获得幸运数字奖励"
            assert reward_name == "接好运", "奖励名称应该是接好运"
            
        except ImportError:
            pytest.skip("通用幸运数字函数尚未实现")
    
    def test_personal_sequence_mode_non_multiple(self):
        """测试非5倍数合同不获得奖励"""
        try:
            from modules.data_processing_module import determine_lucky_number_reward_generic
            
            # 第4个合同不应该获得奖励
            reward_type, reward_name = determine_lucky_number_reward_generic(
                contract_number=789,
                current_contract_amount=12000,
                housekeeper_contract_count=4,  # 第4个合同
                config_key="BJ-2025-09"
            )
            
            assert reward_type == "", "第4个合同不应该获得幸运数字奖励"
            assert reward_name == "", "不应该有奖励名称"
            
        except ImportError:
            pytest.skip("通用幸运数字函数尚未实现")
    
    def test_unified_reward_amount(self):
        """测试统一奖励金额（不区分1万上下）"""
        try:
            from modules.data_processing_module import determine_lucky_number_reward_generic
            
            # 5000元合同
            reward_type1, reward_name1 = determine_lucky_number_reward_generic(
                contract_number=111, current_contract_amount=5000,
                housekeeper_contract_count=5, config_key="BJ-2025-09"
            )
            
            # 15000元合同
            reward_type2, reward_name2 = determine_lucky_number_reward_generic(
                contract_number=222, current_contract_amount=15000,
                housekeeper_contract_count=10, config_key="BJ-2025-09"
            )
            
            # 两者应该获得相同奖励
            assert reward_name1 == reward_name2 == "接好运", "不同金额应该获得相同奖励"
            
        except ImportError:
            pytest.skip("通用幸运数字函数尚未实现")


class TestTieredRewardsNewThreshold:
    """测试新的节节高门槛和奖励"""
    
    def test_min_contracts_threshold_10(self):
        """测试10个合同门槛"""
        try:
            from modules.data_processing_module import determine_rewards_generic
            
            # 9个合同不应该获得节节高奖励
            housekeeper_data_9 = {
                'count': 9,
                'total_amount': 100000.0,
                'performance_amount': 100000.0,
                'awarded': []
            }
            
            reward_types, reward_names, _ = determine_rewards_generic(
                contract_number=1,
                housekeeper_data=housekeeper_data_9,
                current_contract_amount=10000,
                config_key="BJ-2025-09"
            )
            
            assert "节节高" not in reward_types, "9个合同不应该获得节节高奖励"
            
        except ImportError:
            pytest.skip("通用奖励函数尚未支持新配置")
    
    def test_new_reward_amounts(self):
        """测试新的奖励金额"""
        try:
            from modules.data_processing_module import determine_rewards_generic
            
            # 10个合同且8万元应该获得400元达标奖
            housekeeper_data = {
                'count': 10,
                'total_amount': 80000.0,
                'performance_amount': 80000.0,
                'awarded': []
            }
            
            reward_types, reward_names, _ = determine_rewards_generic(
                contract_number=1,
                housekeeper_data=housekeeper_data,
                current_contract_amount=10000,
                config_key="BJ-2025-09"
            )
            
            assert "节节高" in reward_types, "10个合同且8万元应该获得节节高奖励"
            assert "达标奖" in reward_names, "应该获得达标奖"
            
        except ImportError:
            pytest.skip("通用奖励函数尚未支持新配置")


class TestBadgeDisabled:
    """测试徽章功能禁用"""
    
    def test_should_enable_badge_function_exists(self):
        """测试徽章配置检查函数存在"""
        try:
            from modules.data_processing_module import should_enable_badge
            assert callable(should_enable_badge), "徽章配置检查函数必须可调用"
        except ImportError:
            pytest.skip("徽章配置检查函数尚未实现")
    
    def test_elite_badge_disabled(self):
        """测试精英徽章禁用"""
        try:
            from modules.data_processing_module import should_enable_badge
            
            elite_enabled = should_enable_badge("BJ-2025-09", "elite")
            assert elite_enabled == False, "BJ-2025-09配置下精英徽章必须禁用"
            
        except ImportError:
            pytest.skip("徽章配置检查函数尚未实现")
    
    def test_rising_star_badge_disabled(self):
        """测试新星徽章禁用"""
        try:
            from modules.data_processing_module import should_enable_badge
            
            rising_star_enabled = should_enable_badge("BJ-2025-09", "rising_star")
            assert rising_star_enabled == False, "BJ-2025-09配置下新星徽章必须禁用"
            
        except ImportError:
            pytest.skip("徽章配置检查函数尚未实现")


class TestProjectAmountLimit:
    """测试5万元工单金额上限"""
    
    def test_single_contract_limit_5w(self):
        """测试单个合同5万元上限"""
        # 这个测试需要在数据处理逻辑中验证
        # 6万元合同应该按5万计入业绩
        config = REWARD_CONFIGS["BJ-2025-09"]
        assert config["performance_limits"]["single_contract_cap"] == 50000, "单个合同上限必须是5万"
    
    def test_project_limit_5w(self):
        """测试工单累计5万元上限"""
        config = REWARD_CONFIGS["BJ-2025-09"]
        assert config["performance_limits"]["single_project_limit"] == 50000, "工单累计上限必须是5万"


class TestWrapperFunctions:
    """测试包装函数"""
    
    def test_process_data_sep_beijing_exists(self):
        """测试北京9月数据处理函数存在"""
        try:
            from modules.data_processing_module import process_data_sep_beijing
            assert callable(process_data_sep_beijing), "北京9月数据处理函数必须可调用"
        except ImportError:
            pytest.skip("北京9月数据处理函数尚未实现")
    
    def test_notify_awards_sep_beijing_exists(self):
        """测试北京9月通知函数存在"""
        try:
            from modules.notification_module import notify_awards_sep_beijing
            assert callable(notify_awards_sep_beijing), "北京9月通知函数必须可调用"
        except ImportError:
            pytest.skip("北京9月通知函数尚未实现")
    
    def test_signing_and_sales_incentive_sep_beijing_exists(self):
        """测试北京9月Job函数存在"""
        try:
            from jobs import signing_and_sales_incentive_sep_beijing
            assert callable(signing_and_sales_incentive_sep_beijing), "北京9月Job函数必须可调用"
        except ImportError:
            pytest.skip("北京9月Job函数尚未实现")


if __name__ == "__main__":
    # 运行新功能测试
    pytest.main([__file__, "-v", "--tb=short"])
