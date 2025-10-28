"""
销售激励系统重构 - 数据处理管道
版本: v1.0
创建日期: 2025-01-08

这个模块提供了统一的数据处理管道，替代现有的重复处理函数。
核心优势：
1. 消除复杂的内存状态维护
2. 数据库驱动的累计计算
3. 配置驱动的差异处理
4. 统一的处理流程
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .data_models import (
    ProcessingConfig, ContractData, HousekeeperStats, 
    PerformanceRecord, RewardInfo, OrderType
)
from .storage import PerformanceDataStore
from .reward_calculator import RewardCalculator
from .record_builder import RecordBuilder


class DataProcessingPipeline:
    """数据库驱动的统一处理管道 - 大幅简化逻辑"""

    def __init__(self, config: ProcessingConfig, store: PerformanceDataStore):
        self.config = config
        self.store = store
        self.reward_calculator = RewardCalculator(config.config_key)
        self.record_builder = RecordBuilder(config)
        self.runtime_awards = {}  # 运行时奖励状态，防止同一次执行中重复发放

        # 🔧 修复：运行时项目地址去重管理 - 与旧架构保持一致的内存去重
        self.runtime_project_addresses = {}  # {housekeeper_key: set(project_addresses)}

        logging.info(f"Initialized processing pipeline for {config.activity_code}")

    def process(self, contract_data_list: List[Dict], housekeeper_award_lists: Dict[str, List[str]] = None) -> List[PerformanceRecord]:
        """
        主处理流程 - 消除复杂的内存状态维护

        Args:
            contract_data_list: 合同数据列表
            housekeeper_award_lists: 管家历史奖励列表（关键修复：防止重复发放奖励）
        """
        logging.info(f"Starting to process {len(contract_data_list)} contracts for {self.config.activity_code}")

        # 🔧 新增：检查是否仅处理平台单
        # 🐛 修复：从 REWARD_CONFIGS 中获取配置，而不是从 ProcessingConfig 对象中获取
        from .config_adapter import ConfigAdapter
        reward_config = ConfigAdapter.get_reward_config(self.config.config_key)
        processing_config = reward_config.get("processing_config", {})
        process_platform_only = processing_config.get("process_platform_only", False)

        if process_platform_only:
            # 过滤：仅保留平台单
            original_count = len(contract_data_list)
            contract_data_list = [
                c for c in contract_data_list
                if c.get('工单类型(sourceType)', 2) == 2
            ]
            filtered_count = original_count - len(contract_data_list)
            logging.info(f"平台单过滤：原始 {original_count} 个，过滤掉 {filtered_count} 个自引单，保留 {len(contract_data_list)} 个平台单")

        # 🔧 关键修复：保存历史奖励信息
        self.housekeeper_award_lists = housekeeper_award_lists or {}
        logging.info(f"Loaded historical awards for {len(self.housekeeper_award_lists)} housekeepers")

        performance_records = []
        processed_count = 0
        skipped_count = 0

        # 🔧 新增：工单级别业绩金额跟踪器（用于工单上限控制）
        project_performance_tracker = {}

        # 🔧 新增：管家累计业绩金额跟踪器（用于累计业绩金额计算）
        housekeeper_cumulative_performance = {}

        # 全局合同序号计数器（所有活动都需要用于"活动期内第几个合同"字段显示）
        # 🔧 修复：对于有历史合同的活动，只计算非历史合同的数量
        if self.config.enable_historical_contracts:
            # 有历史合同的活动：只计算非历史合同数量
            global_contract_sequence = self.store.get_existing_non_historical_contract_count(self.config.activity_code) + 1
            logging.info(f"历史合同模式：从非历史合同数量 {global_contract_sequence - 1} 开始计算全局序号")
        else:
            # 无历史合同的活动：计算所有合同数量
            global_contract_sequence = len(self.store.get_existing_contract_ids(self.config.activity_code)) + 1
            logging.info(f"常规模式：从所有合同数量 {global_contract_sequence - 1} 开始计算全局序号")
        
        for contract_dict in contract_data_list:
            try:
                # 1. 转换为标准数据结构
                contract_data = ContractData.from_dict(contract_dict)
                
                # 2. 数据库去重查询 - 替代复杂的CSV读取
                if self.store.contract_exists(contract_data.contract_id, self.config.activity_code):
                    skipped_count += 1
                    continue
                
                # 3. 数据库聚合查询 - 替代复杂的内存累计计算
                housekeeper_key = self._build_housekeeper_key(contract_data)
                hk_stats = self.store.get_housekeeper_stats(housekeeper_key, self.config.activity_code)
                hk_awards = self.store.get_housekeeper_awards(housekeeper_key, self.config.activity_code)

                # 🔧 关键修复：优先使用传入的历史奖励信息（参考旧系统逻辑）
                if self.housekeeper_award_lists and housekeeper_key in self.housekeeper_award_lists:
                    historical_awards = self.housekeeper_award_lists[housekeeper_key]
                    logging.debug(f"Using historical awards for {housekeeper_key}: {historical_awards}")
                else:
                    historical_awards = hk_awards

                # 合并运行时奖励状态，防止同一次执行中重复发放
                runtime_awards = self.runtime_awards.get(housekeeper_key, [])
                all_awards = list(set(historical_awards + runtime_awards))
                hk_stats.awarded = all_awards
                
                # 4. 处理工单金额上限（北京特有）
                performance_amount = self._calculate_performance_amount_with_tracking(
                    contract_data, project_performance_tracker)

                # 5. 历史合同特殊处理
                if contract_data.is_historical and self.config.enable_historical_contracts:
                    # 历史合同：不计入累计统计，不参与奖励计算
                    updated_hk_stats = hk_stats  # 不更新统计数据
                    rewards = []  # 不计算奖励
                    contract_sequence = 0  # 🔧 修复：历史合同不计入活动期内合同序号
                    next_reward_gap = ""  # 🔧 修复：历史合同没有下一个奖励差距

                    logging.debug(f"处理历史合同: {contract_data.contract_id}, 不参与累计统计和奖励计算")
                else:
                    # 新增合同：正常处理
                    # 更新管家统计中的业绩金额（用于奖励计算）
                    updated_hk_stats = HousekeeperStats(
                        housekeeper=hk_stats.housekeeper,
                        activity_code=hk_stats.activity_code,
                        contract_count=hk_stats.contract_count + 1,
                        total_amount=hk_stats.total_amount + contract_data.contract_amount,
                        performance_amount=hk_stats.performance_amount + performance_amount,
                        awarded=hk_stats.awarded,
                        platform_count=hk_stats.platform_count + (1 if contract_data.order_type.value == 'platform' else 0),
                        platform_amount=hk_stats.platform_amount + (contract_data.contract_amount if contract_data.order_type.value == 'platform' else 0),
                        self_referral_count=hk_stats.self_referral_count + (1 if contract_data.order_type.value == 'self_referral' else 0),
                        self_referral_amount=hk_stats.self_referral_amount + (contract_data.contract_amount if contract_data.order_type.value == 'self_referral' else 0),
                        historical_count=hk_stats.historical_count + (1 if contract_data.is_historical else 0),
                        new_count=hk_stats.new_count + (0 if contract_data.is_historical else 1)
                    )

                    # 计算两种序号，供业务逻辑选择使用
                    global_sequence = global_contract_sequence  # 全局合同签署序号
                    personal_sequence = updated_hk_stats.contract_count  # 管家个人合同签署序号

                    # 默认显示全局序号（可通过配置调整）
                    contract_sequence = global_sequence

                    # 6. 处理自引单项目地址去重（上海特有）- 🔧 修复：与旧架构保持一致，处理合同但可能不给奖励
                    is_duplicate_address = False
                    if (self.config.enable_dual_track and
                        contract_data.order_type.value == 'self_referral'):
                        project_address = contract_data.raw_data.get('项目地址(projectAddress)', '')
                        if project_address:
                            is_duplicate_address = self._is_project_address_duplicate_runtime(
                                housekeeper_key, project_address)

                            if is_duplicate_address:
                                logging.debug(f"重复项目地址，将处理合同但不给奖励: {project_address}")

                            # 记录项目地址到运行时缓存（无论是否重复都要记录）
                            if housekeeper_key not in self.runtime_project_addresses:
                                self.runtime_project_addresses[housekeeper_key] = set()
                            self.runtime_project_addresses[housekeeper_key].add(project_address)

                    # 7. 计算奖励（使用更新后的统计数据，传递序号信息）
                    # 🔧 修复：重复项目地址的自引单不给奖励，与旧架构保持一致
                    if is_duplicate_address:
                        rewards = []  # 重复项目地址的自引单不给奖励
                        next_reward_gap = ""
                        logging.debug(f"重复项目地址的自引单不给奖励: {contract_data.contract_id}")
                    else:
                        rewards, next_reward_gap = self.reward_calculator.calculate(
                            contract_data,
                            updated_hk_stats,
                            global_sequence=global_sequence,
                            personal_sequence=personal_sequence
                        )

                    # 8. 更新运行时奖励状态
                    if rewards:
                        if housekeeper_key not in self.runtime_awards:
                            self.runtime_awards[housekeeper_key] = []
                        for reward in rewards:
                            self.runtime_awards[housekeeper_key].append(reward.reward_name)

                # 8.5. 🔧 新增：计算并保存累计业绩金额
                cumulative_performance_amount = self._calculate_cumulative_performance_amount(
                    housekeeper_key, performance_amount, contract_data.is_historical,
                    housekeeper_cumulative_performance)

                # 将累计业绩金额保存到 contract_data 中，供通知服务使用
                contract_data.cumulative_performance_amount = cumulative_performance_amount

                # 9. 构建业绩记录
                record = self.record_builder.build(
                    contract_data=contract_data,
                    housekeeper_stats=updated_hk_stats,  # 使用更新后的统计数据
                    rewards=rewards,
                    performance_amount=performance_amount,
                    contract_sequence=contract_sequence,
                    next_reward_gap=next_reward_gap
                )
                
                # 10. 保存记录
                self.store.save_performance_record(record)
                performance_records.append(record)

                # 只有新增合同才计入processed_count（用于合同序号计算）
                if not (contract_data.is_historical and self.config.enable_historical_contracts):
                    processed_count += 1

                # 🔧 修复：只有非历史合同才增加全局序号计数器
                if not (contract_data.is_historical and self.config.enable_historical_contracts):
                    global_contract_sequence += 1
                    logging.debug(f"全局序号递增至: {global_contract_sequence - 1} (合同: {contract_data.contract_id})")

                logging.debug(f"Processed contract {contract_data.contract_id} (historical: {contract_data.is_historical})")
                
            except Exception as e:
                import traceback
                logging.error(f"Error processing contract {contract_dict.get('合同ID(_id)', 'unknown')}: {e}")
                logging.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        logging.info(f"Processing completed: {processed_count} processed, {skipped_count} skipped")
        return performance_records

    def _build_housekeeper_key(self, contract_data: ContractData) -> str:
        """根据城市构建管家键"""
        if self.config.housekeeper_key_format == "管家_服务商":
            return f"{contract_data.housekeeper}_{contract_data.service_provider}"
        else:
            return contract_data.housekeeper

    def _calculate_performance_amount(self, contract_data: ContractData) -> float:
        """计算计入业绩的金额（原有方法，保持兼容性）"""
        base_amount = contract_data.contract_amount

        # 北京特有：工单金额上限处理
        if self.config.enable_project_limit and contract_data.project_id:
            project_usage = self.store.get_project_usage(
                contract_data.project_id,
                self.config.activity_code
            )

            # 从配置中获取工单上限
            from .config_adapter import get_reward_config
            config_data = get_reward_config(self.config.config_key)
            performance_limits = config_data.get('performance_limits', {})

            # 根据合同类型选择不同的工单上限
            if contract_data.order_type.value == 'self_referral':
                # 自引单使用专门的工单上限（如果配置了的话）
                project_limit = performance_limits.get('self_referral_project_limit',
                                                      performance_limits.get('single_project_limit', 500000))
            else:
                # 平台单使用默认工单上限
                project_limit = performance_limits.get('single_project_limit', 500000)

            # 计算剩余可用额度
            remaining_limit = max(0, project_limit - project_usage)
            performance_amount = min(base_amount, remaining_limit)

            logging.debug(f"Project {contract_data.project_id} ({contract_data.order_type.value}): "
                         f"usage={project_usage}, limit={project_limit}, "
                         f"remaining={remaining_limit}, performance_amount={performance_amount}")

            return performance_amount

        # 其他情况直接返回合同金额
        return base_amount

    def _calculate_performance_amount_with_tracking(self, contract_data: ContractData,
                                                   project_performance_tracker: Dict[str, float]) -> float:
        """
        计算计入业绩的金额（带工单级别跟踪）
        参考旧架构的 process_historical_contract_with_project_limit 逻辑
        """
        # 1. 先应用单合同上限（支持差异化上限）
        from .config_adapter import get_reward_config
        config_data = get_reward_config(self.config.config_key)
        performance_limits = config_data.get('performance_limits', {})

        # 根据工单类型选择不同的上限
        if contract_data.order_type.value == 'self_referral':
            # 自引单使用专门的上限（如果配置了的话）
            single_contract_cap = performance_limits.get('self_referral_contract_cap',
                                                       performance_limits.get('single_contract_cap', 50000))
        else:
            # 平台单使用默认上限
            single_contract_cap = performance_limits.get('single_contract_cap', 50000)

        base_amount = min(contract_data.contract_amount, single_contract_cap)

        logging.debug(f"Contract {contract_data.contract_id} ({contract_data.order_type.value}): "
                     f"amount={contract_data.contract_amount}, cap={single_contract_cap}, "
                     f"base_amount={base_amount}")

        # 2. 再考虑工单级别上限（北京特有）
        if self.config.enable_project_limit and contract_data.project_id:
            # 根据合同类型选择不同的工单上限
            if contract_data.order_type.value == 'self_referral':
                # 自引单使用专门的工单上限（如果配置了的话）
                project_limit = performance_limits.get('self_referral_project_limit',
                                                      performance_limits.get('single_project_limit', 50000))
            else:
                # 平台单使用默认工单上限
                project_limit = performance_limits.get('single_project_limit', 50000)

            # 获取当前工单的累计使用金额（包含本批次已处理的合同）
            current_project_total = project_performance_tracker.get(contract_data.project_id, 0)

            # 计算剩余可用额度
            remaining_quota = max(0, project_limit - current_project_total)
            performance_amount = min(base_amount, remaining_quota)

            # 更新工单累计跟踪器
            project_performance_tracker[contract_data.project_id] = current_project_total + performance_amount

            logging.debug(f"Project {contract_data.project_id} ({contract_data.order_type.value}): "
                         f"current_total={current_project_total}, limit={project_limit}, "
                         f"remaining_quota={remaining_quota}, performance_amount={performance_amount}")

            return performance_amount

        # 其他情况直接返回应用单合同上限后的金额
        return base_amount

    def _calculate_cumulative_performance_amount(self, housekeeper_key: str, performance_amount: float,
                                               is_historical: bool, housekeeper_cumulative_performance: Dict[str, float]) -> float:
        """
        计算管家累计业绩金额
        参考旧架构的 add_housekeeper_cumulative_performance_amount 逻辑
        """
        # 历史合同不参与累计业绩金额计算
        if is_historical:
            return 0.0

        # 获取管家当前累计业绩金额（包含数据库中已有的 + 本批次已处理的）
        if housekeeper_key not in housekeeper_cumulative_performance:
            # 首次处理该管家，从数据库获取已有的累计业绩金额
            hk_stats = self.store.get_housekeeper_stats(housekeeper_key, self.config.activity_code)
            housekeeper_cumulative_performance[housekeeper_key] = hk_stats.performance_amount

        # 累加当前合同的业绩金额
        housekeeper_cumulative_performance[housekeeper_key] += performance_amount

        # 返回累计业绩金额
        return housekeeper_cumulative_performance[housekeeper_key]

    def get_processing_summary(self) -> Dict:
        """获取处理摘要信息"""
        all_records = self.store.get_all_records(self.config.activity_code)
        
        summary = {
            'activity_code': self.config.activity_code,
            'total_contracts': len(all_records),
            'total_amount': sum(float(r.get('contract_amount', 0)) for r in all_records),
            'total_performance_amount': sum(float(r.get('performance_amount', 0)) for r in all_records),
            'unique_housekeepers': len(set(r.get('housekeeper', '') for r in all_records)),
            'processing_time': datetime.now().isoformat()
        }
        
        # 双轨统计摘要（上海特有）
        if self.config.enable_dual_track:
            platform_records = [r for r in all_records if r.get('order_type') == 'platform']
            self_referral_records = [r for r in all_records if r.get('order_type') == 'self_referral']
            
            summary.update({
                'platform_contracts': len(platform_records),
                'platform_amount': sum(float(r.get('contract_amount', 0)) for r in platform_records),
                'self_referral_contracts': len(self_referral_records),
                'self_referral_amount': sum(float(r.get('contract_amount', 0)) for r in self_referral_records)
            })
        
        return summary

    def _is_project_address_duplicate_runtime(self, housekeeper_key: str, project_address: str) -> bool:
        """检查项目地址是否重复（运行时内存去重 - 与旧架构保持一致）"""
        if housekeeper_key not in self.runtime_project_addresses:
            return False

        return project_address in self.runtime_project_addresses[housekeeper_key]

    def _is_project_address_duplicate(self, housekeeper: str, project_address: str, activity_code: str) -> bool:
        """检查项目地址是否重复（上海自引单特有逻辑）"""
        try:
            # 查询数据库中是否已存在相同管家和项目地址的记录
            all_records = self.store.get_all_records(activity_code)

            for record in all_records:
                if (record.get('housekeeper') == housekeeper and
                    record.get('order_type') == 'self_referral'):
                    # 从扩展字段中获取项目地址
                    extensions = record.get('extensions', '{}')
                    if extensions:
                        try:
                            import json
                            ext_data = json.loads(extensions)
                            existing_address = ext_data.get('项目地址(projectAddress)', '')
                            if existing_address == project_address:
                                return True
                        except json.JSONDecodeError:
                            continue

            return False
        except Exception as e:
            logging.error(f"检查项目地址重复时出错: {e}")
            return False


class PipelineValidator:
    """管道验证器 - 确保处理结果的正确性"""
    
    def __init__(self, pipeline: DataProcessingPipeline):
        self.pipeline = pipeline
    
    def validate_processing_results(self, records: List[PerformanceRecord]) -> Dict:
        """验证处理结果"""
        validation_report = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # 1. 基础数据验证
        for i, record in enumerate(records):
            if not record.contract_data.contract_id:
                validation_report['errors'].append(f"Record {i}: Missing contract_id")
                validation_report['is_valid'] = False
            
            if record.performance_amount < 0:
                validation_report['errors'].append(f"Record {i}: Negative performance_amount")
                validation_report['is_valid'] = False
            
            if record.contract_data.contract_amount <= 0:
                validation_report['warnings'].append(f"Record {i}: Zero or negative contract_amount")
        
        # 2. 业务逻辑验证
        housekeeper_stats = {}
        for record in records:
            hk = record.contract_data.housekeeper
            if hk not in housekeeper_stats:
                housekeeper_stats[hk] = {'count': 0, 'amount': 0}
            housekeeper_stats[hk]['count'] += 1
            housekeeper_stats[hk]['amount'] += record.contract_data.contract_amount
        
        # 3. 统计信息
        validation_report['statistics'] = {
            'total_records': len(records),
            'unique_housekeepers': len(housekeeper_stats),
            'total_amount': sum(r.contract_data.contract_amount for r in records),
            'total_performance_amount': sum(r.performance_amount for r in records),
            'records_with_rewards': len([r for r in records if r.rewards])
        }
        
        return validation_report


def create_processing_pipeline(config: ProcessingConfig, store: PerformanceDataStore) -> DataProcessingPipeline:
    """工厂函数：创建处理管道实例"""
    return DataProcessingPipeline(config, store)
