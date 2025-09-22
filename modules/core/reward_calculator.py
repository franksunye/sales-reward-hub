"""
销售激励系统重构 - 奖励计算器
版本: v1.0
创建日期: 2025-01-08

配置驱动的奖励计算器，替代现有的重复奖励计算函数。
支持：
1. 幸运数字奖励
2. 节节高奖励
3. 自引单奖励
4. 徽章系统
"""

import logging
from typing import List, Dict, Optional, Tuple
import re

from .data_models import ContractData, HousekeeperStats, RewardInfo, OrderType


class RewardCalculator:
    """配置驱动的奖励计算器"""

    def __init__(self, config_key: str):
        self.config_key = config_key
        self.config = self._load_config(config_key)
        logging.info(f"Initialized reward calculator for {config_key}")

    def _load_config(self, config_key: str) -> Dict:
        """加载奖励配置"""
        from .config_adapter import ConfigAdapter
        return ConfigAdapter.get_reward_config(config_key)

    def calculate(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats) -> List[RewardInfo]:
        """计算所有类型的奖励"""
        rewards = []
        
        try:
            # 1. 幸运数字奖励
            lucky_reward = self._calculate_lucky_reward(contract_data, housekeeper_stats)
            if lucky_reward:
                rewards.append(lucky_reward)
            
            # 2. 节节高奖励（独立奖励）
            jiejiegao_reward = self._calculate_jiejiegao_reward(housekeeper_stats)
            if jiejiegao_reward:
                rewards.append(jiejiegao_reward)

            # 3. 阶梯奖励（达标奖、优秀奖、精英奖）
            tiered_rewards = self._calculate_tiered_reward(housekeeper_stats)
            if tiered_rewards:
                rewards.extend(tiered_rewards)
            
            # 4. 自引单奖励（如果启用）
            self_referral_config = self.config.get("self_referral_rewards", {})
            if (self_referral_config.get("enable", False) and
                contract_data.order_type == OrderType.SELF_REFERRAL):
                self_referral_reward = self._calculate_self_referral_reward(contract_data, housekeeper_stats)
                if self_referral_reward:
                    rewards.append(self_referral_reward)
            
            logging.debug(f"Calculated {len(rewards)} rewards for contract {contract_data.contract_id}")
            
        except Exception as e:
            logging.error(f"Error calculating rewards: {e}")
        
        return rewards

    def _calculate_lucky_reward(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats) -> Optional[RewardInfo]:
        """计算幸运数字奖励"""
        lucky_config = self.config.get("lucky_rewards")
        if not lucky_config:
            return None

        lucky_number = self.config.get("lucky_number", "8")
        contract_amount = contract_data.contract_amount

        # 检查是否符合幸运数字条件
        if not self._is_lucky_contract(contract_data, housekeeper_stats, lucky_number):
            return None
        
        # 根据合同金额确定奖励类型
        if contract_amount >= lucky_config.get("high", {}).get("threshold", 10000):
            reward_name = lucky_config["high"]["name"]
        else:
            reward_name = lucky_config["base"]["name"]
        
        # 检查是否已经获得过此类奖励
        if reward_name in housekeeper_stats.awarded:
            logging.debug(f"Housekeeper {contract_data.housekeeper} already has {reward_name}")
            return None
        
        return RewardInfo(
            reward_type="幸运数字",
            reward_name=reward_name,
            description=f"合同编号包含幸运数字{lucky_number}"
        )

    def _calculate_jiejiegao_reward(self, housekeeper_stats: HousekeeperStats) -> Optional[RewardInfo]:
        """计算节节高奖励（独立奖励）"""
        jiejiegao_config = self.config.get("jiejiegao_reward", {})
        if not jiejiegao_config:
            return None

        reward_name = jiejiegao_config["name"]
        min_contracts = jiejiegao_config["min_contracts"]
        threshold = jiejiegao_config["threshold"]

        # 检查是否已经获得过节节高奖励
        if reward_name in housekeeper_stats.awarded:
            logging.debug(f"Housekeeper {housekeeper_stats.housekeeper} already has {reward_name}")
            return None

        # 检查合同数量和业绩阈值
        if (housekeeper_stats.contract_count >= min_contracts and
            housekeeper_stats.total_performance >= threshold):

            return RewardInfo(
                reward_type="节节高",
                reward_name=reward_name,
                description=f"达到{min_contracts}个合同且业绩超过{threshold}元"
            )

        return None

    def _calculate_tiered_reward(self, housekeeper_stats: HousekeeperStats) -> List[RewardInfo]:
        """计算节节高奖励 - 返回所有符合条件的奖励"""
        tiered_config = self.config.get("tiered_rewards")
        if not tiered_config:
            return []

        min_contracts = tiered_config.get("min_contracts", 6)
        if housekeeper_stats.contract_count < min_contracts:
            return []

        rewards = []
        tiers = tiered_config.get("tiers", [])

        # 按照阈值从低到高排序，确保按顺序发放奖励
        sorted_tiers = sorted(tiers, key=lambda x: x["threshold"])

        for tier in sorted_tiers:
            threshold = tier.get("threshold", 0)
            reward_name = tier.get("name", "")

            if (housekeeper_stats.performance_amount >= threshold and
                reward_name not in housekeeper_stats.awarded):

                rewards.append(RewardInfo(
                    reward_type="节节高",
                    reward_name=reward_name,
                    description=f"累计业绩达到{threshold}元"
                ))

                # 将奖励添加到已获得列表中，防止重复发放
                housekeeper_stats.awarded.append(reward_name)

        return rewards

    def _calculate_self_referral_reward(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats) -> Optional[RewardInfo]:
        """计算自引单奖励"""
        self_referral_config = self.config.get("self_referral_rewards")
        if not self_referral_config or not self_referral_config.get("enable", False):
            return None

        # 检查项目地址去重逻辑（上海特有）
        project_address = contract_data.raw_data.get('项目地址(projectAddress)', '')
        if not project_address:
            return None

        # 项目地址去重逻辑
        # 注意：这里简化处理，实际应该查询数据库检查该项目地址是否已经被该管家使用过
        # 在处理管道中会有更完整的去重逻辑

        reward_type = self_referral_config.get("reward_type", "自引单")
        reward_name = self_referral_config.get("reward_name", "红包")

        return RewardInfo(
            reward_type=reward_type,
            reward_name=reward_name,
            description=f"自引单项目地址: {project_address}"
        )

    def _is_lucky_contract(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats, lucky_number: str) -> bool:
        """检查是否是幸运合同"""
        # 支持不同的幸运数字检查策略（兼容两种字段名）
        lucky_strategy = self.config.get("lucky_strategy") or self.config.get("lucky_number_mode", "last_digit")

        if lucky_strategy == "last_digit":
            # 只检查末位数字（北京6月）
            return contract_data.contract_id.endswith(lucky_number)
        elif lucky_strategy == "contains":
            return lucky_number in contract_data.contract_id
        elif lucky_strategy == "personal_sequence":
            # 个人顺序幸运数字（北京9月特有）
            return self._check_personal_sequence_lucky(housekeeper_stats, lucky_number)
        else:
            return contract_data.contract_id.endswith(lucky_number)  # 默认检查末位

    def _check_personal_sequence_lucky(self, housekeeper_stats: HousekeeperStats, lucky_number: str) -> bool:
        """检查个人序列幸运数字（北京9月特有）"""
        # 北京9月的个人序列幸运数字逻辑
        # 管家的第5个、第10个、第15个...合同有幸运奖励
        # lucky_number应该是"5"，表示5的倍数
        try:
            lucky_interval = int(lucky_number)
            return housekeeper_stats.contract_count % lucky_interval == 0
        except (ValueError, ZeroDivisionError):
            return False

    def get_reward_amount(self, reward_name: str) -> Optional[float]:
        """获取奖励金额"""
        awards_mapping = self.config.get("awards_mapping", {})
        amount_str = awards_mapping.get(reward_name)
        
        if amount_str:
            try:
                return float(amount_str)
            except ValueError:
                logging.warning(f"Invalid reward amount for {reward_name}: {amount_str}")
        
        return None

    def is_badge_enabled(self) -> bool:
        """检查是否启用徽章系统"""
        return self.config.get("enable_rising_star_badge", True)

    def calculate_reward_multiplier(self, housekeeper_stats: HousekeeperStats) -> float:
        """计算奖励倍数（徽章系统）"""
        if not self.is_badge_enabled():
            return 1.0
        
        # 检查是否达到精英标准
        elite_threshold = self.config.get("tiered_rewards", {}).get("tiers", [])
        if elite_threshold:
            elite_amount = max(tier.get("threshold", 0) for tier in elite_threshold)
            if housekeeper_stats.performance_amount >= elite_amount:
                return 2.0  # 精英奖励翻倍
        
        return 1.0

    def get_next_reward_gap(self, housekeeper_stats: HousekeeperStats) -> Optional[Dict]:
        """计算距离下一个奖励的差距"""
        tiered_config = self.config.get("tiered_rewards")
        if not tiered_config:
            return None
        
        tiers = tiered_config.get("tiers", [])
        current_amount = housekeeper_stats.performance_amount
        
        for tier in tiers:
            threshold = tier.get("threshold", 0)
            reward_name = tier.get("name", "")
            
            if current_amount < threshold and reward_name not in housekeeper_stats.awarded:
                gap = threshold - current_amount
                return {
                    'next_reward': reward_name,
                    'threshold': threshold,
                    'gap': gap,
                    'progress_percentage': (current_amount / threshold) * 100
                }
        
        return None


def create_reward_calculator(config_key: str) -> RewardCalculator:
    """工厂函数：创建奖励计算器实例"""
    return RewardCalculator(config_key)
