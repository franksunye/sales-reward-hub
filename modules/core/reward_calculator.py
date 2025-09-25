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

    def calculate(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats,
                  global_sequence: int = None, personal_sequence: int = None) -> tuple:
        """计算奖励 - 完全按照旧架构逻辑

        Args:
            contract_data: 合同数据
            housekeeper_stats: 管家统计数据
            global_sequence: 全局合同签署序号
            personal_sequence: 管家个人合同签署序号

        Returns:
            tuple: (rewards, next_reward_gap)
        """
        try:
            # 计算奖励
            reward_types, reward_names, next_reward_gap = self._calculate_rewards(
                contract_data, housekeeper_stats, global_sequence, personal_sequence
            )

            # 解析组合奖励
            rewards = []
            if reward_types and reward_names:
                type_list = [t.strip() for t in reward_types.split(',') if t.strip()]
                name_list = [n.strip() for n in reward_names.split(',') if n.strip()]

                # 确保类型和名称数量匹配
                for i in range(min(len(type_list), len(name_list))):
                    rewards.append(RewardInfo(
                        reward_type=type_list[i],
                        reward_name=name_list[i],
                        description=f"{type_list[i]}奖励"
                    ))

            logging.debug(f"Calculated {len(rewards)} rewards for contract {contract_data.contract_id}")
            return rewards, next_reward_gap

        except Exception as e:
            logging.error(f"Error calculating rewards: {e}")
            return [], ""



    def _calculate_rewards(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats,
                          global_sequence: int = None, personal_sequence: int = None) -> tuple:
        """计算奖励 - 按照业务逻辑计算各种奖励

        Args:
            contract_data: 合同数据
            housekeeper_stats: 管家统计数据
            global_sequence: 全局合同签署序号
            personal_sequence: 管家个人合同签署序号
        """
        reward_types = []
        reward_names = []
        next_reward_gap = ""

        # 1. 幸运数字奖励逻辑（传递序号信息）
        lucky_reward_type, lucky_reward_name = self._determine_lucky_number_reward(
            contract_data, housekeeper_stats, global_sequence, personal_sequence
        )

        if lucky_reward_type:
            reward_types.append(lucky_reward_type)
            reward_names.append(lucky_reward_name)

        # 2. 节节高奖励逻辑（根据配置和工单类型计算）
        tiered_reward_types, tiered_reward_names, tiered_next_gap = self._calculate_tiered_rewards(
            contract_data, housekeeper_stats
        )

        if tiered_reward_types:
            reward_types.extend(tiered_reward_types)
            reward_names.extend(tiered_reward_names)

        if tiered_next_gap:
            next_reward_gap = tiered_next_gap

        # 3. 自引单奖励逻辑（上海9月特有）
        self_referral_reward_type, self_referral_reward_name = self._determine_self_referral_reward(
            contract_data, housekeeper_stats
        )

        if self_referral_reward_type:
            reward_types.append(self_referral_reward_type)
            reward_names.append(self_referral_reward_name)

        return ', '.join(reward_types), ', '.join(reward_names), next_reward_gap

    def _determine_lucky_number_reward(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats,
                                      global_sequence: int = None, personal_sequence: int = None) -> tuple:
        """计算幸运数字奖励

        Args:
            contract_data: 合同数据
            housekeeper_stats: 管家统计数据
            global_sequence: 全局合同签署序号
            personal_sequence: 管家个人合同签署序号
        """
        lucky_number_str = self.config.get("lucky_number", "5")

        # 🔧 修复：如果lucky_number为空字符串，则禁用幸运奖励（上海9月的情况）
        if not lucky_number_str or lucky_number_str == "":
            return "", ""

        try:
            lucky_number = int(lucky_number_str)
        except (ValueError, TypeError):
            # 如果无法转换为整数，禁用幸运奖励
            return "", ""

        lucky_number_mode = self.config.get("lucky_number_mode", "personal_sequence")
        lucky_number_sequence_type = self.config.get("lucky_number_sequence_type", "personal")
        lucky_rewards = self.config.get("lucky_rewards", {})

        # 根据配置选择使用哪种序号进行幸运数字判定
        if lucky_number_sequence_type == "global" and global_sequence is not None:
            sequence_to_check = global_sequence
        elif lucky_number_sequence_type == "personal" and personal_sequence is not None:
            sequence_to_check = personal_sequence
        else:
            # 兜底：使用管家统计中的个人序号
            sequence_to_check = housekeeper_stats.contract_count

        # 北京9月使用个人顺序模式
        if lucky_number_mode == "personal_sequence":
            # 检查是否是幸运数字的倍数
            if sequence_to_check % lucky_number == 0:
                # 根据合同金额确定奖励等级
                base_reward = lucky_rewards.get("base", {})
                high_reward = lucky_rewards.get("high", {})

                # 北京9月统一奖励，不区分金额
                reward_name = base_reward.get("name", "接好运")
                return "幸运数字", reward_name

        return "", ""

    def _determine_self_referral_reward(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats) -> tuple:
        """计算自引单奖励"""
        self_referral_config = self.config.get("self_referral_rewards", {})

        # 检查是否启用自引单奖励
        if not self_referral_config.get("enable", False):
            return "", ""

        # 检查是否是自引单
        if contract_data.order_type.value != 'self_referral':
            return "", ""

        # 获取项目地址
        project_address = contract_data.raw_data.get('项目地址(projectAddress)', '')
        if not project_address:
            return "", ""

        # 简化的去重逻辑（在实际系统中，处理管道会处理更复杂的去重）
        # 这里假设每个自引单都能获得奖励，去重逻辑由处理管道处理

        reward_type = self_referral_config.get("reward_type", "自引单")
        reward_name = self_referral_config.get("reward_name", "红包")

        return reward_type, reward_name

    def _calculate_tiered_rewards(self, contract_data: ContractData, housekeeper_stats: HousekeeperStats) -> tuple:
        """计算节节高奖励（根据配置和工单类型）"""
        # 获取奖励计算策略配置
        strategy_config = self.config.get("reward_calculation_strategy", {})
        strategy_type = strategy_config.get("type", "single_track")
        rules = strategy_config.get("rules", {})

        # 根据工单类型确定使用的规则
        if strategy_type == "dual_track":
            # 双轨激励：根据工单类型选择规则
            if contract_data.order_type.value == 'platform':
                rule_key = "platform"
            elif contract_data.order_type.value == 'self_referral':
                rule_key = "self_referral"
            else:
                rule_key = "platform"  # 默认使用平台单规则
        else:
            # 单轨激励：使用默认规则
            rule_key = "default"

        # 获取具体规则
        rule = rules.get(rule_key, {"enable_tiered_rewards": True, "stats_source": "total"})

        # 如果该工单类型不启用节节高奖励，直接返回
        if not rule.get("enable_tiered_rewards", True):
            return [], [], ""

        # 根据规则选择统计数据
        stats_source = rule.get("stats_source", "total")
        contract_count, amount = self._get_stats_by_source(housekeeper_stats, stats_source)

        # 获取节节高奖励配置
        tiered_rewards = self.config.get("tiered_rewards", {})
        min_contracts = tiered_rewards.get("min_contracts", 10)
        tiers = tiered_rewards.get("tiers", [])

        reward_types = []
        reward_names = []
        next_reward_gap = ""

        # 记录所有奖励名称，用于后续检查
        all_tier_names = [tier["name"] for tier in tiers]

        # 如果管家合同数量达到要求
        if contract_count >= min_contracts:
            next_reward = None

            # 按照阈值从高到低排序奖励等级（与旧系统保持一致）
            # 旧系统的奖励顺序是从高到低：卓越奖→精英奖→优秀奖→达标奖→基础奖
            sorted_tiers = sorted(tiers, key=lambda x: x["threshold"], reverse=True)

            # 复制旧系统的两阶段奖励发放逻辑
            has_rewards = False

            # 第一阶段：按照阈值从高到低排序，找到第一个符合条件的奖励并发放
            for i, tier in enumerate(sorted_tiers):
                tier_name = tier["name"]
                tier_threshold = tier["threshold"]

                if amount >= tier_threshold and tier_name not in housekeeper_stats.awarded:
                    reward_types.append("节节高")
                    reward_names.append(tier_name)
                    housekeeper_stats.awarded.append(tier_name)
                    has_rewards = True

                    # 如果不是最高级别的奖励，设置下一个奖励
                    if i > 0:
                        next_reward = sorted_tiers[i-1]["name"]
                    break

            # 第二阶段：自动发放所有低级别奖项（如果之前未获得）
            # 按照阈值从低到高排序
            low_to_high_tiers = sorted(tiers, key=lambda x: x["threshold"])
            for tier in low_to_high_tiers:
                tier_name = tier["name"]
                tier_threshold = tier["threshold"]

                if tier_name not in housekeeper_stats.awarded and amount >= tier_threshold:
                    reward_types.append("节节高")
                    reward_names.append(tier_name)
                    housekeeper_stats.awarded.append(tier_name)
                    has_rewards = True

            # 🔧 修复：如果未达到任何奖励阈值，设置下一个奖励为最低等级
            if not set(all_tier_names).intersection(housekeeper_stats.awarded):
                next_reward = sorted_tiers[-1]["name"]

            # 第三阶段：确定下一个奖励（与旧架构逻辑完全一致）
            if not next_reward:
                for i in range(len(sorted_tiers) - 1):
                    current_tier = sorted_tiers[i+1]
                    next_tier = sorted_tiers[i]

                    if (current_tier["name"] in housekeeper_stats.awarded and
                        amount < next_tier["threshold"] and
                        next_tier["name"] not in housekeeper_stats.awarded):
                        next_reward = next_tier["name"]
                        break

            # 计算距离下一级奖励所需的金额差
            if next_reward:
                next_reward_threshold = next(
                    (tier["threshold"] for tier in tiers if tier["name"] == next_reward),
                    0
                )
                if next_reward_threshold > 0:
                    next_reward_gap = f"距离 {next_reward} 还需 {round(next_reward_threshold - amount, 2):,} 元"
        else:
            # 如果未达到最低合同数量要求
            if not set(all_tier_names).intersection(housekeeper_stats.awarded):
                next_reward_gap = f"距离达成节节高奖励条件还需 {min_contracts - contract_count} 单"

        return reward_types, reward_names, next_reward_gap

    def _get_stats_by_source(self, housekeeper_stats: HousekeeperStats, stats_source: str) -> tuple:
        """根据统计数据源获取合同数量和金额

        Args:
            housekeeper_stats: 管家统计数据
            stats_source: 统计数据源类型

        Returns:
            tuple: (合同数量, 金额)
        """
        # 确定使用哪个金额字段（业绩上限逻辑）
        performance_limits = self.config.get("performance_limits", {})
        enable_cap = performance_limits.get("enable_cap", False)

        if stats_source == "platform_only":
            # 使用平台单统计数据
            contract_count = housekeeper_stats.platform_count
            if enable_cap:
                amount = housekeeper_stats.performance_amount  # 平台单的业绩金额
            else:
                amount = housekeeper_stats.platform_amount
        elif stats_source == "self_referral_only":
            # 使用自引单统计数据
            contract_count = housekeeper_stats.self_referral_count
            if enable_cap:
                amount = housekeeper_stats.performance_amount  # 自引单的业绩金额
            else:
                amount = housekeeper_stats.self_referral_amount
        else:
            # 使用总统计数据（默认）
            contract_count = housekeeper_stats.contract_count
            if enable_cap:
                amount = housekeeper_stats.performance_amount
            else:
                amount = housekeeper_stats.total_amount

        return contract_count, amount



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

        # 🔧 修复：如果lucky_number为空字符串，返回False
        if not lucky_number or lucky_number == "":
            return False

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
        """计算距离下一个奖励的差距 - 修复为与旧架构一致的逻辑"""
        tiered_config = self.config.get("tiered_rewards")
        if not tiered_config:
            return None

        tiers = tiered_config.get("tiers", [])
        current_amount = housekeeper_stats.performance_amount

        # 🔧 修复：按照旧架构逻辑，按阈值从低到高排序
        sorted_tiers = sorted(tiers, key=lambda x: x["threshold"])

        # 找到下一个未获得的奖励等级
        for tier in sorted_tiers:
            threshold = tier.get("threshold", 0)
            reward_name = tier.get("name", "")

            # 如果当前金额小于阈值且未获得该奖励
            if current_amount < threshold and reward_name not in housekeeper_stats.awarded:
                gap = threshold - current_amount
                return {
                    'next_reward': reward_name,
                    'threshold': threshold,
                    'gap': gap,
                    'progress_percentage': (current_amount / threshold) * 100
                }

        # 如果所有奖励都已达成，返回None（对应旧架构的空白显示）
        return None


def create_reward_calculator(config_key: str) -> RewardCalculator:
    """工厂函数：创建奖励计算器实例"""
    return RewardCalculator(config_key)
