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
        
        logging.info(f"Initialized processing pipeline for {config.activity_code}")

    def process(self, contract_data_list: List[Dict]) -> List[PerformanceRecord]:
        """主处理流程 - 消除复杂的内存状态维护"""
        logging.info(f"Starting to process {len(contract_data_list)} contracts for {self.config.activity_code}")
        
        performance_records = []
        processed_count = 0
        skipped_count = 0
        
        for contract_dict in contract_data_list:
            try:
                # 1. 转换为标准数据结构
                contract_data = ContractData.from_dict(contract_dict)
                
                # 2. 数据库去重查询 - 替代复杂的CSV读取
                if self.store.contract_exists(contract_data.contract_id, self.config.activity_code):
                    logging.debug(f"Skipping existing contract: {contract_data.contract_id}")
                    skipped_count += 1
                    continue
                
                # 3. 数据库聚合查询 - 替代复杂的内存累计计算
                housekeeper_key = self._build_housekeeper_key(contract_data)
                hk_stats = self.store.get_housekeeper_stats(housekeeper_key, self.config.activity_code)
                hk_awards = self.store.get_housekeeper_awards(housekeeper_key, self.config.activity_code)
                hk_stats.awarded = hk_awards
                
                # 4. 处理工单金额上限（北京特有）
                performance_amount = self._calculate_performance_amount(contract_data)
                
                # 5. 计算奖励
                rewards = self.reward_calculator.calculate(contract_data, hk_stats)
                
                # 6. 构建业绩记录
                record = self.record_builder.build(
                    contract_data=contract_data,
                    housekeeper_stats=hk_stats,
                    rewards=rewards,
                    performance_amount=performance_amount,
                    contract_sequence=processed_count + 1
                )
                
                # 7. 保存记录
                self.store.save_performance_record(record)
                performance_records.append(record)
                processed_count += 1
                
                logging.debug(f"Processed contract {contract_data.contract_id}")
                
            except Exception as e:
                logging.error(f"Error processing contract {contract_dict.get('合同ID(_id)', 'unknown')}: {e}")
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
            from modules.config import REWARD_CONFIGS
            config_data = REWARD_CONFIGS.get(self.config.config_key, {})
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
