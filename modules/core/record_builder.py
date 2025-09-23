"""
销售激励系统重构 - 记录构建器
版本: v1.0
创建日期: 2025-01-08

负责构建标准的业绩记录，支持不同城市的字段差异。
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .data_models import (
    ProcessingConfig, ContractData, HousekeeperStats, 
    PerformanceRecord, RewardInfo, OrderType
)


class RecordBuilder:
    """记录构建器 - 支持不同城市的字段差异"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        logging.info(f"Initialized record builder for {config.activity_code}")

    def build(self, 
              contract_data: ContractData,
              housekeeper_stats: HousekeeperStats,
              rewards: List[RewardInfo],
              performance_amount: float,
              contract_sequence: int = 0) -> PerformanceRecord:
        """构建业绩记录"""
        
        # 创建基础记录
        # 历史合同的激活状态始终为0
        active_status = 0 if contract_data.is_historical else (1 if rewards else 0)

        # 历史合同需要特殊处理累计统计字段
        if contract_data.is_historical:
            # 历史合同：累计统计字段设为0，与旧系统保持一致
            historical_stats = HousekeeperStats(
                housekeeper=housekeeper_stats.housekeeper,
                activity_code=housekeeper_stats.activity_code,
                contract_count=0,  # 历史合同不计入累计单数
                total_amount=0,    # 历史合同不计入累计金额
                performance_amount=housekeeper_stats.performance_amount,  # 业绩金额保持不变
                awarded=housekeeper_stats.awarded,
                platform_count=housekeeper_stats.platform_count,
                platform_amount=housekeeper_stats.platform_amount,
                self_referral_count=housekeeper_stats.self_referral_count,
                self_referral_amount=housekeeper_stats.self_referral_amount,
                historical_count=housekeeper_stats.historical_count,
                new_count=housekeeper_stats.new_count
            )
            final_stats = historical_stats
        else:
            final_stats = housekeeper_stats

        record = PerformanceRecord(
            activity_code=self.config.activity_code,
            contract_data=contract_data,
            housekeeper_stats=final_stats,
            rewards=rewards,
            performance_amount=performance_amount,
            contract_sequence=contract_sequence,
            active_status=active_status,
            notification_sent=False,
            remarks=self._build_remarks(contract_data, rewards, performance_amount)
        )
        
        logging.debug(f"Built record for contract {contract_data.contract_id}")
        return record

    def _build_remarks(self, contract_data: ContractData, rewards: List[RewardInfo], performance_amount: float) -> str:
        """构建备注信息"""
        remarks = []
        
        # 添加奖励相关备注
        if rewards:
            reward_names = [r.reward_name for r in rewards]
            remarks.append(f"获得奖励: {', '.join(reward_names)}")
        
        # 添加订单类型备注（双轨统计）
        if self.config.enable_dual_track:
            order_type_text = "自引单" if contract_data.order_type == OrderType.SELF_REFERRAL else "平台单"
            remarks.append(f"订单类型: {order_type_text}")
        
        # 添加历史合同备注
        if contract_data.is_historical:
            # 历史合同使用固定格式，与旧系统保持一致
            if rewards:
                # 如果有奖励信息，先清空（历史合同不应该有奖励）
                remarks = []
            remarks.append("历史合同-仅计入业绩金额")
        
        # 添加工单上限备注（北京特有）
        if self.config.enable_project_limit and contract_data.project_id:
            if contract_data.contract_amount != performance_amount:
                remarks.append(f"工单上限调整: {contract_data.contract_amount} -> {performance_amount}")
        
        return "; ".join(remarks) if remarks else ""

    def build_csv_headers(self) -> List[str]:
        """构建CSV表头"""
        base_headers = [
            '活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 
            'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', 
            '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 
            'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 
            'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)',
            '活动期内第几个合同', '管家累计金额', '管家累计单数', '奖金池', '计入业绩金额',
            '管家累计业绩金额', '激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间'
        ]
        
        # 添加双轨统计字段（上海特有）
        if self.config.enable_dual_track:
            dual_track_headers = [
                '管家ID(serviceHousekeeperId)', '工单类型', '客户联系地址(contactsAddress)',
                '项目地址(projectAddress)', '平台单累计数量', '平台单累计金额',
                '自引单累计数量', '自引单累计金额'
            ]
            base_headers.extend(dual_track_headers)
        
        # 添加历史合同字段（北京9月特有）
        if self.config.enable_historical_contracts:
            historical_headers = [
                '是否历史合同', '合同类型说明', '历史合同编号(pcContractdocNum)'
            ]
            base_headers.extend(historical_headers)
        
        return base_headers

    def build_extended_record_dict(self, record: PerformanceRecord) -> Dict:
        """构建扩展的记录字典，包含所有字段"""
        # 获取基础字典
        record_dict = record.to_dict()
        
        # 添加时间戳
        record_dict['登记时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 添加奖金池计算（如果需要）
        record_dict['奖金池'] = self._calculate_bonus_pool(record)
        
        # 添加差额计算
        record_dict['差额(difference)'] = (
            record.contract_data.contract_amount - record.contract_data.paid_amount
        )
        
        # 添加转化率和平均客单价（如果原始数据中有）
        raw_data = record.contract_data.raw_data
        record_dict['转化率(conversion)'] = raw_data.get('转化率(conversion)', '')
        record_dict['平均客单价(average)'] = raw_data.get('平均客单价(average)', '')
        
        return record_dict

    def _calculate_bonus_pool(self, record: PerformanceRecord) -> float:
        """计算奖金池"""
        from .config_adapter import get_bonus_pool_ratio
        return record.performance_amount * get_bonus_pool_ratio()


class BatchRecordBuilder:
    """批量记录构建器 - 用于批量处理"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.record_builder = RecordBuilder(config)
        self.batch_stats = {
            'total_processed': 0,
            'total_amount': 0.0,
            'total_performance_amount': 0.0,
            'rewards_count': 0
        }
    
    def build_batch(self, 
                   contracts_data: List[ContractData],
                   housekeeper_stats_map: Dict[str, HousekeeperStats],
                   rewards_map: Dict[str, List[RewardInfo]],
                   performance_amounts: List[float]) -> List[PerformanceRecord]:
        """批量构建记录"""
        records = []
        
        for i, contract_data in enumerate(contracts_data):
            housekeeper_key = self._build_housekeeper_key(contract_data)
            hk_stats = housekeeper_stats_map.get(housekeeper_key, 
                                               HousekeeperStats(housekeeper=housekeeper_key, 
                                                              activity_code=self.config.activity_code))
            rewards = rewards_map.get(contract_data.contract_id, [])
            performance_amount = performance_amounts[i] if i < len(performance_amounts) else contract_data.contract_amount
            
            record = self.record_builder.build(
                contract_data=contract_data,
                housekeeper_stats=hk_stats,
                rewards=rewards,
                performance_amount=performance_amount,
                contract_sequence=i + 1
            )
            
            records.append(record)
            
            # 更新批量统计
            self.batch_stats['total_processed'] += 1
            self.batch_stats['total_amount'] += contract_data.contract_amount
            self.batch_stats['total_performance_amount'] += performance_amount
            self.batch_stats['rewards_count'] += len(rewards)
        
        logging.info(f"Batch built {len(records)} records")
        return records
    
    def _build_housekeeper_key(self, contract_data: ContractData) -> str:
        """构建管家键"""
        if self.config.housekeeper_key_format == "管家_服务商":
            return f"{contract_data.housekeeper}_{contract_data.service_provider}"
        else:
            return contract_data.housekeeper
    
    def get_batch_summary(self) -> Dict:
        """获取批量处理摘要"""
        return {
            'config': {
                'activity_code': self.config.activity_code,
                'city': self.config.city.value,
                'enable_dual_track': self.config.enable_dual_track,
                'enable_historical_contracts': self.config.enable_historical_contracts
            },
            'statistics': self.batch_stats.copy(),
            'processing_time': datetime.now().isoformat()
        }


def create_record_builder(config: ProcessingConfig) -> RecordBuilder:
    """工厂函数：创建记录构建器实例"""
    return RecordBuilder(config)


def create_batch_record_builder(config: ProcessingConfig) -> BatchRecordBuilder:
    """工厂函数：创建批量记录构建器实例"""
    return BatchRecordBuilder(config)
