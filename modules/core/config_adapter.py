"""
销售激励系统重构 - 配置适配器
版本: v1.0
创建日期: 2025-01-08

配置适配器，用于将现有的REWARD_CONFIGS集成到新架构中。
解决配置导入问题，提供统一的配置访问接口。
"""

import logging
import os
import sys
from typing import Dict, Optional

# 添加项目根目录到路径，确保能导入modules.config
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class ConfigAdapter:
    """配置适配器 - 统一配置访问接口"""
    
    _config_cache = {}  # 配置缓存
    
    @classmethod
    def get_reward_config(cls, config_key: str) -> Dict:
        """获取奖励配置"""
        if config_key in cls._config_cache:
            return cls._config_cache[config_key]
        
        try:
            # 尝试导入现有配置
            from modules.config import REWARD_CONFIGS
            config = REWARD_CONFIGS.get(config_key, {})
            
            if not config:
                logging.warning(f"No reward config found for {config_key}, using default")
                config = cls._get_default_config(config_key)
            
            # 缓存配置
            cls._config_cache[config_key] = config
            logging.info(f"Loaded reward config for {config_key}")
            return config
            
        except ImportError as e:
            logging.error(f"Failed to import REWARD_CONFIGS: {e}")
            # 返回默认配置
            config = cls._get_default_config(config_key)
            cls._config_cache[config_key] = config
            return config
    
    @classmethod
    def _get_default_config(cls, config_key: str) -> Dict:
        """获取默认配置（用于测试和开发）"""
        # 根据config_key推断基本配置
        if "BJ" in config_key:
            return cls._get_beijing_default_config()
        elif "SH" in config_key:
            return cls._get_shanghai_default_config()
        else:
            return cls._get_generic_default_config()
    
    @classmethod
    def _get_beijing_default_config(cls) -> Dict:
        """北京默认配置"""
        return {
            "lucky_number": "8",
            "lucky_rewards": {
                "base": {"name": "接好运", "threshold": 0},
                "high": {"name": "接好运万元以上", "threshold": 10000}
            },
            "performance_limits": {
                "single_project_limit": 500000,
                "enable_cap": True,
                "single_contract_cap": 500000
            },
            "tiered_rewards": {
                "min_contracts": 6,
                "tiers": [
                    {"name": "达标奖", "threshold": 80000},
                    {"name": "优秀奖", "threshold": 120000},
                    {"name": "精英奖", "threshold": 180000}
                ]
            },
            "awards_mapping": {
                "接好运": "36",
                "接好运万元以上": "66",
                "达标奖": "200",
                "优秀奖": "400",
                "精英奖": "600"
            },
            "enable_rising_star_badge": True
        }
    
    @classmethod
    def _get_shanghai_default_config(cls) -> Dict:
        """上海默认配置"""
        return {
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
            },
            "awards_mapping": {
                "接好运": "36",
                "接好运万元以上": "66",
                "达标奖": "200",
                "优秀奖": "400",
                "红包": "50"  # 自引单奖励
            },
            "enable_self_referral": True,
            "self_referral_rewards": {
                "enable": True,
                "reward_type": "自引单",
                "reward_name": "红包",
                "reward_amount": 50,
                "deduplication_field": "projectAddress"
            },
            "enable_rising_star_badge": False  # 上海技师不参与徽章系统
        }
    
    @classmethod
    def _get_generic_default_config(cls) -> Dict:
        """通用默认配置"""
        return {
            "lucky_number": "8",
            "lucky_rewards": {
                "base": {"name": "接好运", "threshold": 0},
                "high": {"name": "接好运万元以上", "threshold": 10000}
            },
            "tiered_rewards": {
                "min_contracts": 6,
                "tiers": [
                    {"name": "达标奖", "threshold": 80000}
                ]
            },
            "awards_mapping": {
                "接好运": "36",
                "接好运万元以上": "66",
                "达标奖": "200"
            }
        }
    
    @classmethod
    def get_bonus_pool_ratio(cls) -> float:
        """获取奖金池比例"""
        try:
            from modules.config import BONUS_POOL_RATIO
            return BONUS_POOL_RATIO
        except ImportError:
            return 0.002  # 默认0.2%
    
    @classmethod
    def validate_config(cls, config: Dict, config_key: str) -> bool:
        """验证配置完整性"""
        required_keys = ["lucky_number", "lucky_rewards", "tiered_rewards", "awards_mapping"]
        
        for key in required_keys:
            if key not in config:
                logging.warning(f"Missing required config key '{key}' in {config_key}")
                return False
        
        # 验证lucky_rewards结构
        lucky_rewards = config.get("lucky_rewards", {})
        if not isinstance(lucky_rewards, dict) or "base" not in lucky_rewards:
            logging.warning(f"Invalid lucky_rewards structure in {config_key}")
            return False
        
        # 验证tiered_rewards结构
        tiered_rewards = config.get("tiered_rewards", {})
        if not isinstance(tiered_rewards, dict) or "tiers" not in tiered_rewards:
            logging.warning(f"Invalid tiered_rewards structure in {config_key}")
            return False
        
        logging.info(f"Config validation passed for {config_key}")
        return True
    
    @classmethod
    def clear_cache(cls):
        """清除配置缓存"""
        cls._config_cache.clear()
        logging.info("Config cache cleared")


# 便捷函数
def get_reward_config(config_key: str) -> Dict:
    """获取奖励配置的便捷函数"""
    return ConfigAdapter.get_reward_config(config_key)


def get_bonus_pool_ratio() -> float:
    """获取奖金池比例的便捷函数"""
    return ConfigAdapter.get_bonus_pool_ratio()


# 配置验证函数
def validate_all_configs():
    """验证所有配置"""
    try:
        from modules.config import REWARD_CONFIGS
        
        validation_results = {}
        for config_key, config in REWARD_CONFIGS.items():
            is_valid = ConfigAdapter.validate_config(config, config_key)
            validation_results[config_key] = is_valid
            
        return validation_results
    except ImportError:
        logging.error("Cannot validate configs: REWARD_CONFIGS not available")
        return {}


if __name__ == "__main__":
    # 测试配置适配器
    logging.basicConfig(level=logging.INFO)
    
    # 测试北京配置
    bj_config = get_reward_config("BJ-2025-06")
    print(f"北京配置: {bj_config.get('lucky_number')}")
    
    # 测试上海配置
    sh_config = get_reward_config("SH-2025-09")
    print(f"上海配置: {sh_config.get('lucky_number')}")
    
    # 验证所有配置
    validation_results = validate_all_configs()
    print(f"配置验证结果: {validation_results}")
