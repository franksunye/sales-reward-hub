"""
销售激励系统重构 - 核心数据模型
版本: v1.0
创建日期: 2025-01-08
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
import json
import os
import sqlite3


def _query_cumulative_performance_amount(contract_id: str) -> float:
    """按当前 DB_SOURCE 读取累计业绩金额，查询失败时返回 0。"""
    db_source = os.getenv("DB_SOURCE", "").strip().lower()

    if db_source == "cloud":
        db_url = os.getenv("TURSO_DB_URL", "").strip()
        auth_token = os.getenv("TURSO_AUTH_TOKEN", "").strip()
        if db_url and auth_token:
            try:
                import requests
                base = db_url.replace("libsql://", "https://").replace("wss://", "https://").rstrip("/")
                payload = {
                    "requests": [
                        {
                            "type": "execute",
                            "stmt": {
                                "sql": "SELECT cumulative_performance_amount FROM performance_data WHERE contract_id = ? LIMIT 1",
                                "args": [{"type": "text", "value": contract_id}],
                            },
                        },
                        {"type": "close"},
                    ]
                }
                response = requests.post(
                    f"{base}/v2/pipeline",
                    headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
                result = response.json().get("results", [{}])[0]
                if result.get("type") == "ok":
                    rows = result.get("response", {}).get("result", {}).get("rows", [])
                    if rows and rows[0]:
                        cell = rows[0][0]
                        value = cell.get("value")
                        if value is None:
                            return 0.0
                        return float(value)
            except Exception:
                return 0.0
        return 0.0

    db_path = os.getenv("LOCAL_DB_PATH", "performance_data.db")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT cumulative_performance_amount FROM performance_data WHERE contract_id = ? LIMIT 1",
                (contract_id,),
            )
            result = cursor.fetchone()
            if result and result[0] is not None:
                return float(result[0])
    except Exception:
        return 0.0
    return 0.0


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
    storage_type: str = "sqlite"       # 支持 "sqlite" 或 "turso"
    enable_dual_track: bool = False    # 是否启用双轨统计
    enable_historical_contracts: bool = False  # 是否支持历史合同
    enable_project_limit: bool = False # 是否启用工单金额上限
    enable_csv_output: bool = False    # 是否生成CSV文件（默认关闭）
    
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
    cumulative_performance_amount: float = 0.0  # 🔧 修复：累计业绩金额（用于消息显示）

    # 原始数据字段（保持兼容性）
    raw_data: Dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContractData':
        """从字典创建合同数据"""
        contract_id = str(data['合同ID(_id)'])
        cumulative_performance_amount = _query_cumulative_performance_amount(contract_id)

        return cls(
            contract_id=contract_id,
            housekeeper=data['管家(serviceHousekeeper)'],
            service_provider=data.get('服务商(orgName)', ''),
            contract_amount=float(data['合同金额(adjustRefundMoney)']),
            paid_amount=float(data.get('支付金额(paidAmount)', 0)),
            project_id=data.get('工单编号(serviceAppointmentNum)'),
            order_type=OrderType.SELF_REFERRAL if str(data.get('工单类型(sourceType)', '2')) == '1' else OrderType.PLATFORM,
            is_historical=bool(data.get('is_historical', data.get('是否历史合同', False))),  # 优先使用is_historical字段，兼容是否历史合同字段
            cumulative_performance_amount=cumulative_performance_amount,
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
            '计入业绩金额': self.performance_amount,  # 新架构设计：单个合同的业绩金额
            '管家累计业绩金额': getattr(self.contract_data, 'cumulative_performance_amount', self.housekeeper_stats.performance_amount),  # 🔧 修复：优先使用合同的累计业绩
            '活动期内第几个合同': self.contract_sequence,
            '管家累计单数': self.housekeeper_stats.contract_count,
            '管家累计金额': self.housekeeper_stats.total_amount,
            '激活奖励状态': self.active_status,
            '奖励类型': ','.join([r.reward_type for r in self.rewards]),
            '奖励名称': ','.join([r.reward_name for r in self.rewards]),
            '是否发送通知': 'Y' if self.notification_sent else 'N',
            '备注': self.remarks
        }
        
        # 添加原始数据字段
        base_dict.update(self.contract_data.raw_data)
        
        # 添加双轨统计字段（总是添加，确保通知消息能获取到这些字段）
        # 🔧 修复：移除条件判断，确保双轨统计字段总是被添加到extensions中
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
