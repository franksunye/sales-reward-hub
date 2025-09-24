"""
销售激励系统重构 - 通知服务
版本: v1.0
创建日期: 2025-01-08

新架构的通知服务，直接从数据库操作，避免CSV中间步骤。
保持与旧架构完全相同的消息内容和业务逻辑。
"""

import logging
import time
from typing import List, Dict, Optional
from datetime import datetime

from .storage import PerformanceDataStore
from .data_models import ProcessingConfig
from ..config import *
from task_manager import create_task


class NotificationService:
    """新架构通知服务 - 直接从数据库操作"""
    
    def __init__(self, storage: PerformanceDataStore, config: ProcessingConfig):
        self.storage = storage
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def send_notifications(self) -> Dict[str, int]:
        """
        发送通知 - 主入口函数
        
        Returns:
            Dict: 包含发送统计信息
        """
        self.logger.info(f"开始发送通知: {self.config.activity_code}")
        
        # 获取需要发送通知的记录
        records = self._get_notification_records()
        self.logger.info(f"找到 {len(records)} 条需要发送通知的记录")
        
        if not records:
            return {"total": 0, "group_notifications": 0, "award_notifications": 0}
        
        # 获取奖励映射配置
        awards_mapping = self._get_awards_mapping()
        
        # 发送通知
        stats = {"total": len(records), "group_notifications": 0, "award_notifications": 0}
        
        for record in records:
            try:
                # 发送群通知
                if self._should_send_group_notification(record):
                    self._send_group_notification(record)
                    stats["group_notifications"] += 1
                
                # 发送个人奖励通知
                if self._should_send_award_notification(record):
                    self._send_award_notification(record, awards_mapping)
                    stats["award_notifications"] += 1
                
                # 更新通知状态
                self._update_notification_status(record)
                
                # 添加延迟避免频繁请求
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"发送通知失败 - 合同ID: {record.get('contract_id')}, 错误: {e}")
                continue
        
        self.logger.info(f"通知发送完成 - 总计: {stats['total']}, 群通知: {stats['group_notifications']}, 奖励通知: {stats['award_notifications']}")
        return stats
    
    def _get_notification_records(self) -> List[Dict]:
        """从数据库获取需要发送通知的记录"""
        # 查询需要发送通知的记录（未发送 + 非历史合同）
        query_conditions = {
            'activity_code': self.config.activity_code,
            'notification_sent': False,
            'is_historical': False
        }
        
        # 从存储层获取记录
        records = self.storage.query_performance_records(query_conditions)
        
        # 转换为字典格式，兼容现有消息生成逻辑
        notification_records = []
        for record in records:
            record_dict = self._convert_record_to_dict(record)
            notification_records.append(record_dict)
        
        return notification_records
    
    def _convert_record_to_dict(self, record) -> Dict:
        """将数据库记录转换为字典格式，兼容现有消息模板"""
        # 数据库记录是字典格式，直接处理
        extensions = {}
        if record.get('extensions'):
            import json
            try:
                extensions = json.loads(record['extensions'])
            except:
                extensions = {}

        return {
            '合同ID(_id)': record['contract_id'],
            '管家(serviceHousekeeper)': record['housekeeper'],
            '合同编号(contractdocNum)': extensions.get('合同编号(contractdocNum)', ''),
            '合同金额(adjustRefundMoney)': record['contract_amount'],
            '活动期内第几个合同': record.get('contract_sequence', 0),
            '管家累计单数': extensions.get('管家累计单数', 0),
            '管家累计金额': extensions.get('管家累计金额', 0),
            '管家累计业绩金额': extensions.get('管家累计业绩金额', record['performance_amount']),
            '激活奖励状态': '1' if record.get('reward_names') else '0',
            '奖励类型': record.get('reward_types', ''),
            '奖励名称': record.get('reward_names', ''),
            '备注': extensions.get('备注', '无'),  # 🔧 修复：默认值改为'无'，与旧架构保持一致
            '是否发送通知': 'Y' if record.get('notification_sent') else 'N',
            # 添加其他必要字段
            '支付金额(paidAmount)': extensions.get('支付金额(paidAmount)', 0),
            '服务商(orgName)': record.get('service_provider', ''),
        }
    
    def _get_awards_mapping(self) -> Dict[str, str]:
        """获取奖励金额映射配置"""
        from modules.notification_module import get_awards_mapping
        return get_awards_mapping(self.config.config_key)
    
    def _should_send_group_notification(self, record: Dict) -> bool:
        """判断是否应该发送群通知"""
        return record.get('是否发送通知') == 'N'
    
    def _should_send_award_notification(self, record: Dict) -> bool:
        """判断是否应该发送奖励通知"""
        return (record.get('激活奖励状态') == '1' and 
                record.get('是否发送通知') == 'N')
    
    def _send_group_notification(self, record: Dict):
        """发送群通知 - 使用与旧架构相同的消息模板"""
        # 复用现有的消息生成逻辑
        service_housekeeper = record['管家(serviceHousekeeper)']
        
        # 处理徽章逻辑（与旧架构保持一致）
        if self.config.city.value == "BJ":
            service_housekeeper = self._apply_badge_logic(service_housekeeper)
        
        # 格式化金额显示
        accumulated_amount = self._format_amount(record.get('管家累计金额', 0))
        performance_amount = self._format_amount(record.get('管家累计业绩金额', 0))
        
        # 生成消息内容（与旧架构完全相同的模板）
        next_msg = ('恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩 🎉🎉🎉' 
                   if '无' in record.get("备注", "") 
                   else f'{record.get("备注", "")}')
        
        msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨
恭喜 {service_housekeeper} 签约合同 {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为活动期间平台累计签约第 {record.get("活动期内第几个合同", 0)} 单，个人累计签约第 {record.get("管家累计单数", 0)} 单。

🌻 {record["管家(serviceHousekeeper)"]}累计签约 {accumulated_amount} 元{f', 累计计入业绩 {performance_amount} 元' if ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB else ''}

👊 {next_msg}。
'''
        
        # 创建群通知任务
        group_name = WECOM_GROUP_NAME_BJ if self.config.city.value == "BJ" else WECOM_GROUP_NAME_SH
        create_task('send_wecom_message', group_name, msg)
        
        self.logger.info(f"群通知已创建: {record['管家(serviceHousekeeper)']}")
    
    def _send_award_notification(self, record: Dict, awards_mapping: Dict[str, str]):
        """发送奖励通知 - 使用与旧架构相同的逻辑"""
        from modules.notification_module import generate_award_message
        
        # 使用现有的奖励消息生成函数
        city_code = self.config.city.value
        jiangli_msg = generate_award_message(record, awards_mapping, city_code, self.config.config_key)
        
        # 创建奖励通知任务
        contact = CAMPAIGN_CONTACT_BJ if city_code == "BJ" else CAMPAIGN_CONTACT_SH
        create_task('send_wechat_message', contact, jiangli_msg)
        
        self.logger.info(f"奖励通知已创建: {record['管家(serviceHousekeeper)']} - {record.get('奖励名称', '')}")
    
    def _apply_badge_logic(self, housekeeper_name: str) -> str:
        """应用徽章逻辑（与旧架构保持一致）"""
        # 复用现有的徽章逻辑
        from modules.data_processing_module import should_enable_badge
        
        if ENABLE_BADGE_MANAGEMENT:
            elite_badge_enabled = should_enable_badge(self.config.config_key, "elite")
            if elite_badge_enabled and housekeeper_name in ELITE_HOUSEKEEPER:
                return f'{ELITE_BADGE_NAME}{housekeeper_name}'
        
        return housekeeper_name
    
    def _format_amount(self, amount) -> str:
        """格式化金额显示"""
        try:
            return f"{int(float(amount)):,d}"
        except (ValueError, TypeError):
            return "0"
    
    def _update_notification_status(self, record: Dict):
        """更新通知发送状态"""
        contract_id = record['合同ID(_id)']
        
        # 更新数据库中的通知状态
        self.storage.update_notification_status(
            contract_id=contract_id,
            activity_code=self.config.activity_code,
            notification_sent=True
        )
        
        self.logger.debug(f"通知状态已更新: {contract_id}")


def create_notification_service(storage: PerformanceDataStore, config: ProcessingConfig) -> NotificationService:
    """创建通知服务实例"""
    return NotificationService(storage, config)
