"""
回归测试基线 - 确保现有功能完全不受影响
这是TDD开发的第一步，必须100%通过才能继续开发新功能
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.config import REWARD_CONFIGS
from modules.data_processing_module import (
    determine_lucky_number_reward,
    determine_rewards_jun_beijing_generic,
    determine_rewards_apr_shanghai_generic,
    determine_rewards_generic
)
from modules.notification_module import (
    notify_awards_beijing_generic
)


class TestRegressionBaseline:
    """回归测试基线 - 确保现有功能完全不变"""
    
    def test_existing_configs_unchanged(self):
        """测试现有配置完全不变"""
        # 测试北京8月配置
        bj_aug_config = REWARD_CONFIGS.get("BJ-2025-08")
        assert bj_aug_config is not None, "北京8月配置不能缺失"
        assert bj_aug_config["lucky_number"] == "8", "幸运数字必须是8"
        assert bj_aug_config["tiered_rewards"]["min_contracts"] == 6, "最低合同数必须是6"
        
        # 测试上海4月配置
        sh_apr_config = REWARD_CONFIGS.get("SH-2025-04")
        assert sh_apr_config is not None, "上海4月配置不能缺失"
        
        # 测试上海9月配置
        sh_sep_config = REWARD_CONFIGS.get("SH-2025-09")
        assert sh_sep_config is not None, "上海9月配置不能缺失"
        
    def test_beijing_aug_lucky_number_unchanged(self):
        """测试北京8月幸运数字逻辑完全不变"""
        # 测试合同编号末位为8的情况
        reward_type, reward_name = determine_lucky_number_reward(18, 15000, "8")
        assert reward_type == "幸运数字", "幸运数字类型必须正确"
        assert reward_name == "接好运万元以上", "万元以上奖励名称必须正确"
        
        # 测试合同金额小于1万的情况
        reward_type, reward_name = determine_lucky_number_reward(28, 5000, "8")
        assert reward_type == "幸运数字", "幸运数字类型必须正确"
        assert reward_name == "接好运", "基础奖励名称必须正确"
        
        # 测试合同编号末位不是8的情况
        reward_type, reward_name = determine_lucky_number_reward(17, 15000, "8")
        assert reward_type == "", "非幸运数字不应获得奖励"
        assert reward_name == "", "非幸运数字不应有奖励名称"
        
    def test_beijing_aug_tiered_rewards_unchanged(self):
        """测试北京8月节节高奖励逻辑完全不变"""
        # 模拟管家数据
        housekeeper_data = {
            'count': 6,
            'total_amount': 80000.0,
            'performance_amount': 80000.0,
            'awarded': []
        }
        
        # 测试达标奖
        reward_types, reward_names, next_gap = determine_rewards_jun_beijing_generic(
            contract_number=1, 
            housekeeper_data=housekeeper_data, 
            current_contract_amount=10000
        )
        
        assert "节节高" in reward_types, "应该获得节节高奖励"
        assert "达标奖" in reward_names, "应该获得达标奖"
        
    def test_shanghai_functionality_unchanged(self):
        """测试上海功能完全不变"""
        # 测试上海4月奖励逻辑
        housekeeper_data = {
            'count': 5,
            'total_amount': 40000.0,
            'performance_amount': 40000.0,
            'awarded': []
        }
        
        reward_types, reward_names, next_gap = determine_rewards_apr_shanghai_generic(
            contract_number=1,
            housekeeper_data=housekeeper_data,
            current_contract_amount=10000
        )
        
        assert "节节高" in reward_types, "上海应该获得节节高奖励"
        assert "基础奖" in reward_names, "上海应该获得基础奖"
        
    def test_config_isolation(self):
        """测试配置完全隔离"""
        # 确保各配置项独立存在
        configs = ["BJ-2025-08", "SH-2025-04", "SH-2025-09"]
        for config_key in configs:
            config = REWARD_CONFIGS.get(config_key)
            assert config is not None, f"配置 {config_key} 必须存在"
            assert "awards_mapping" in config, f"配置 {config_key} 必须有奖励映射"
            
    def test_badge_functionality_unchanged(self):
        """测试徽章功能保持不变"""
        # 测试徽章相关配置存在
        from modules.config import ENABLE_BADGE_MANAGEMENT, ELITE_HOUSEKEEPER
        assert isinstance(ENABLE_BADGE_MANAGEMENT, bool), "徽章管理开关必须是布尔值"
        assert isinstance(ELITE_HOUSEKEEPER, list), "精英管家列表必须是列表"
            
    def test_notification_functions_exist(self):
        """测试通知函数存在且可调用"""
        # 确保关键通知函数存在
        from modules.notification_module import (
            notify_awards_jun_beijing,
            notify_awards_may_beijing,
            notify_awards_shanghai_generate_message_march
        )
        
        # 函数应该可以导入（不测试实际调用，避免副作用）
        assert callable(notify_awards_jun_beijing), "北京6月通知函数必须可调用"
        assert callable(notify_awards_may_beijing), "北京5月通知函数必须可调用"
        assert callable(notify_awards_shanghai_generate_message_march), "上海通知函数必须可调用"
        
    def test_data_processing_functions_exist(self):
        """测试数据处理函数存在且可调用"""
        from modules.data_processing_module import (
            process_data_jun_beijing,
            process_data_shanghai_apr
        )
        
        assert callable(process_data_jun_beijing), "北京6月数据处理函数必须可调用"
        assert callable(process_data_shanghai_apr), "上海4月数据处理函数必须可调用"
        
    def test_job_functions_exist(self):
        """测试现有Job函数存在且可调用"""
        from jobs import (
            signing_and_sales_incentive_aug_beijing,
            signing_and_sales_incentive_aug_shanghai
        )
        
        assert callable(signing_and_sales_incentive_aug_beijing), "北京8月Job必须可调用"
        assert callable(signing_and_sales_incentive_aug_shanghai), "上海8月Job必须可调用"


class TestConfigIntegrity:
    """配置完整性测试"""
    
    def test_beijing_aug_config_complete(self):
        """测试北京8月配置完整性"""
        config = REWARD_CONFIGS["BJ-2025-08"]
        
        # 必须包含的配置项
        required_keys = [
            "lucky_number",
            "lucky_rewards", 
            "performance_limits",
            "tiered_rewards",
            "awards_mapping"
        ]
        
        for key in required_keys:
            assert key in config, f"北京8月配置必须包含 {key}"
            
        # 验证奖励映射
        awards = config["awards_mapping"]
        expected_awards = ["接好运", "接好运万元以上", "达标奖", "优秀奖", "精英奖"]
        for award in expected_awards:
            assert award in awards, f"北京8月必须包含 {award} 奖励"
            
    def test_shanghai_configs_complete(self):
        """测试上海配置完整性"""
        # 测试上海4月配置
        sh_apr_config = REWARD_CONFIGS["SH-2025-04"]
        assert "awards_mapping" in sh_apr_config, "上海4月必须有奖励映射"
        
        # 测试上海9月配置
        sh_sep_config = REWARD_CONFIGS["SH-2025-09"]
        assert "awards_mapping" in sh_sep_config, "上海9月必须有奖励映射"


if __name__ == "__main__":
    # 运行回归测试
    pytest.main([__file__, "-v", "--tb=short"])
