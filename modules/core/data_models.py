"""
销售激励系统重构 - 核心数据模型
版本: v1.0
创建日期: 2025-01-08
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import json


class OrderType(Enum):
    """订单类型枚举"""
    PLATFORM = "platform"          # 平台单
    SELF_REFERRAL = "self_referral" # 自引单


class City(Enum):
    """城市枚举"""
    BEIJING = "BJ"
    SHANGHAI = "SH"


@dataclass
class HousekeeperStats:
    """标准管家统计数据结构 - 直接从数据库查询获得"""
    housekeeper: str
    activity_code: str
    
    # 基础统计
    contract_count: int = 0
    total_amount: float = 0.0
    performance_amount: float = 0.0
    awarded: List[str] = field(default_factory=list)
    
    # 双轨统计字段（上海特有）
    platform_count: int = 0
    platform_amount: float = 0.0
    self_referral_count: int = 0
    self_referral_amount: float = 0.0
    
    # 历史合同统计（北京9月特有）
    historical_count: int = 0
    new_count: int = 0
    
    def to_dict(self) -> Dict:
        """转换为字典格式，兼容现有代码"""
        return {
            'count': self.contract_count,
            'total_amount': self.total_amount,
            'performance_amount': self.performance_amount,
            'awarded': self.awarded,
            'platform_count': self.platform_count,
            'platform_amount': self.platform_amount,
            'self_referral_count': self.self_referral_count,
            'self_referral_amount': self.self_referral_amount,
            'historical_count': self.historical_count,
            'new_count': self.new_count
        }


@dataclass
class ProcessingConfig:
    """处理配置数据结构"""
    config_key: str                    # REWARD_CONFIGS中的键
    activity_code: str                 # 活动编码，如 'BJ-JUN', 'SH-SEP'
    city: City                         # 城市
    housekeeper_key_format: str        # "管家" 或 "管家_服务商"
    
    # 功能开关
    storage_type: str = "sqlite"       # "sqlite" 或 "csv"
    enable_dual_track: bool = False    # 是否启用双轨统计
    enable_historical_contracts: bool = False  # 是否支持历史合同
    enable_project_limit: bool = False # 是否启用工单金额上限
    
    # 文件路径配置
    temp_contract_file: Optional[str] = None
    performance_file: Optional[str] = None
    status_file: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.city, str):
            self.city = City(self.city)


@dataclass
class ContractData:
    """合同数据结构"""
    contract_id: str
    housekeeper: str
    service_provider: str
    contract_amount: float
    paid_amount: float = 0.0
    project_id: Optional[str] = None
    order_type: OrderType = OrderType.PLATFORM
    is_historical: bool = False
    
    # 原始数据字段（保持兼容性）
    raw_data: Dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContractData':
        """从字典创建合同数据"""
        return cls(
            contract_id=str(data['合同ID(_id)']),
            housekeeper=data['管家(serviceHousekeeper)'],
            service_provider=data.get('服务商(orgName)', ''),
            contract_amount=float(data['合同金额(adjustRefundMoney)']),
            paid_amount=float(data.get('支付金额(paidAmount)', 0)),
            project_id=data.get('工单编号(serviceAppointmentNum)'),
            order_type=OrderType.SELF_REFERRAL if data.get('款项来源类型(tradeIn)') == 1 else OrderType.PLATFORM,
            is_historical=bool(data.get('pcContractdocNum') and str(data.get('pcContractdocNum')).strip()),  # 如果历史合同字段有值则为历史合同
            raw_data=data
        )


@dataclass
class RewardInfo:
    """奖励信息结构"""
    reward_type: str
    reward_name: str
    amount: Optional[float] = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'type': self.reward_type,
            'name': self.reward_name,
            'amount': self.amount,
            'description': self.description
        }


@dataclass
class PerformanceRecord:
    """业绩记录结构"""
    activity_code: str
    contract_data: ContractData
    housekeeper_stats: HousekeeperStats
    rewards: List[RewardInfo]
    performance_amount: float
    
    # 元数据
    contract_sequence: int = 0  # 活动期内第几个合同
    active_status: int = 0      # 激活奖励状态
    notification_sent: bool = False
    remarks: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典格式，兼容现有CSV输出"""
        base_dict = {
            '活动编号': self.activity_code,
            '合同ID(_id)': self.contract_data.contract_id,
            '管家(serviceHousekeeper)': self.contract_data.housekeeper,
            '服务商(orgName)': self.contract_data.service_provider,
            '合同金额(adjustRefundMoney)': self.contract_data.contract_amount,
            '支付金额(paidAmount)': self.contract_data.paid_amount,
            '计入业绩金额': self.performance_amount,
            '活动期内第几个合同': self.contract_sequence,
            '管家累计单数': self.housekeeper_stats.contract_count,
            '管家累计金额': self.housekeeper_stats.total_amount,
            '激活奖励状态': self.active_status,
            '奖励类型': ','.join([r.reward_type for r in self.rewards]),
            '奖励名称': ','.join([r.reward_name for r in self.rewards]),
            '是否发送通知': 1 if self.notification_sent else 0,
            '备注': self.remarks
        }
        
        # 添加原始数据字段
        base_dict.update(self.contract_data.raw_data)
        
        # 添加双轨统计字段（如果启用）
        if self.housekeeper_stats.platform_count > 0 or self.housekeeper_stats.self_referral_count > 0:
            base_dict.update({
                '工单类型': '自引单' if self.contract_data.order_type == OrderType.SELF_REFERRAL else '平台单',
                '平台单累计数量': self.housekeeper_stats.platform_count,
                '平台单累计金额': self.housekeeper_stats.platform_amount,
                '自引单累计数量': self.housekeeper_stats.self_referral_count,
                '自引单累计金额': self.housekeeper_stats.self_referral_amount
            })
        
        return base_dict


@dataclass
class JobConfig:
    """Job配置结构"""
    processing_config: ProcessingConfig
    api_url: str
    temp_file: str
    performance_file: str
    status_file: str
    columns: List[str]
    headers: List[str]
    
    def __post_init__(self):
        """设置处理配置的文件路径"""
        self.processing_config.temp_contract_file = self.temp_file
        self.processing_config.performance_file = self.performance_file
        self.processing_config.status_file = self.status_file
