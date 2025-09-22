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

        logging.info(f"Initialized processing pipeline for {config.activity_code}")

    def process(self, contract_data_list: List[Dict], housekeeper_award_lists: Dict[str, List[str]] = None) -> List[PerformanceRecord]:
        """
        主处理流程 - 消除复杂的内存状态维护

        Args:
            contract_data_list: 合同数据列表
            housekeeper_award_lists: 管家历史奖励列表（关键修复：防止重复发放奖励）
        """
        logging.info(f"Starting to process {len(contract_data_list)} contracts for {self.config.activity_code}")

        # 🔧 关键修复：保存历史奖励信息
        self.housekeeper_award_lists = housekeeper_award_lists or {}
        logging.info(f"Loaded historical awards for {len(self.housekeeper_award_lists)} housekeepers")

        performance_records = []
        processed_count = 0
        skipped_count = 0

        # 全局合同序号计数器（所有活动都需要用于"活动期内第几个合同"字段显示）
        # 从已存在的合同ID数量开始计数
        global_contract_sequence = len(self.store.get_existing_contract_ids(self.config.activity_code)) + 1
        
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
                performance_amount = self._calculate_performance_amount(contract_data)

                # 5. 历史合同特殊处理
                if contract_data.is_historical and self.config.enable_historical_contracts:
                    # 历史合同：不计入累计统计，不参与奖励计算
                    updated_hk_stats = hk_stats  # 不更新统计数据
                    rewards = []  # 不计算奖励
                    contract_sequence = 0  # 不计入活动期内合同序号

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

                    # 6. 处理自引单项目地址去重（上海特有）
                    if (self.config.enable_dual_track and
                        contract_data.order_type.value == 'self_referral'):
                        project_address = contract_data.raw_data.get('项目地址(projectAddress)', '')
                        if project_address and self._is_project_address_duplicate(
                            housekeeper_key, project_address, self.config.activity_code):
                            logging.debug(f"跳过重复项目地址: {project_address}")
                            skipped_count += 1
                            continue

                    # 7. 计算奖励（使用更新后的统计数据，传递序号信息）
                    rewards = self.reward_calculator.calculate(
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

                # 9. 构建业绩记录
                record = self.record_builder.build(
                    contract_data=contract_data,
                    housekeeper_stats=updated_hk_stats,  # 使用更新后的统计数据
                    rewards=rewards,
                    performance_amount=performance_amount,
                    contract_sequence=contract_sequence
                )
                
                # 10. 保存记录
                self.store.save_performance_record(record)
                performance_records.append(record)

                # 只有新增合同才计入processed_count（用于合同序号计算）
                if not (contract_data.is_historical and self.config.enable_historical_contracts):
                    processed_count += 1

                # 增加全局合同序号计数器（所有合同都计入）
                global_contract_sequence += 1

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
        """计算计入业绩的金额"""
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
            project_limit = config_data.get('performance_limits', {}).get('single_project_limit', 500000)
            
            # 计算剩余可用额度
            remaining_limit = max(0, project_limit - project_usage)
            performance_amount = min(base_amount, remaining_limit)
            
            logging.debug(f"Project {contract_data.project_id}: usage={project_usage}, "
                         f"limit={project_limit}, remaining={remaining_limit}, "
                         f"performance_amount={performance_amount}")
            
            return performance_amount
        
        # 其他情况直接返回合同金额
        return base_amount

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
