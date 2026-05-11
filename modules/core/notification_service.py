"""
销售激励系统重构 - 通知服务
版本: v1.0
创建日期: 2025-01-08

新架构的通知服务，直接从数据库操作，避免CSV中间步骤。
保持与旧架构完全相同的消息内容和业务逻辑。
"""

import logging
import time
import json
import hashlib
import os
from typing import List, Dict, Optional
from datetime import datetime
import requests

from .storage import PerformanceDataStore
from .data_models import ProcessingConfig
from .webhook_router import (
    CHANNEL_BJ_PERFORMANCE_BROADCAST,
    CHANNEL_SIGN_BROADCAST,
    format_safe_webhook_target,
    resolve_wecom_webhook,
)
from ..config import *


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
        stats = {
            "records": 0,
            "enqueued": 0,
            "sent": 0,
            "failed": 0,
            "dead_letter": 0,
        }

        records = self._get_notification_records()
        stats["records"] = len(records)
        self.logger.info(f"找到 {len(records)} 条待通知记录（notification_sent=false）")

        for record in records:
            try:
                if self._should_send_group_notification(record):
                    msg = self._build_group_notification_message(record)
                    outbox_id = self._enqueue_text_outbox(record, msg, "group_broadcast")
                    if outbox_id:
                        stats["enqueued"] += 1
            except Exception as e:
                self.logger.error(f"Outbox enqueue failed - 合同ID: {record.get('合同ID(_id)')}, 错误: {e}")

        retry_limit = int(os.getenv("NOTIFICATION_OUTBOX_BATCH_LIMIT", "200"))
        max_attempts = int(os.getenv("NOTIFICATION_OUTBOX_MAX_ATTEMPTS", "5"))
        outbox_items = self.storage.get_retryable_outbox_messages(
            activity_code=self.config.activity_code,
            max_attempts=max_attempts,
            limit=retry_limit,
        )

        self.logger.info(f"本轮待发送 outbox 数量: {len(outbox_items)}")
        for item in outbox_items:
            try:
                payload = json.loads(item.get("payload_json") or "{}")
                self.logger.info(
                    "发送 webhook: activity=%s, outbox_id=%s, type=%s, contract=%s, %s",
                    item.get("activity_code"),
                    item.get("id"),
                    item.get("message_type"),
                    item.get("contract_id"),
                    format_safe_webhook_target(item.get("webhook_url", "")),
                )
                response = requests.post(
                    item["webhook_url"],
                    json=payload,
                    timeout=20,
                )
                body_text = (response.text or "")[:2000]
                if 200 <= response.status_code < 300:
                    self.storage.mark_outbox_sent(item["id"], response.status_code, body_text)
                    self.storage.update_notification_status(
                        contract_id=item["contract_id"],
                        activity_code=item["activity_code"],
                        notification_sent=True,
                    )
                    stats["sent"] += 1
                else:
                    self.storage.mark_outbox_failed(
                        outbox_id=item["id"],
                        last_error=f"HTTP {response.status_code}",
                        response_code=response.status_code,
                        response_body=body_text,
                        max_attempts=max_attempts,
                    )
                    if int(item.get("attempt_count", 0)) + 1 >= max_attempts:
                        stats["dead_letter"] += 1
                    else:
                        stats["failed"] += 1
            except Exception as e:
                self.storage.mark_outbox_failed(
                    outbox_id=item["id"],
                    last_error=str(e),
                    max_attempts=max_attempts,
                )
                if int(item.get("attempt_count", 0)) + 1 >= max_attempts:
                    stats["dead_letter"] += 1
                else:
                    stats["failed"] += 1
            time.sleep(0.3)

        self.logger.info(
            "通知发送完成 - records=%s, enqueued=%s, sent=%s, failed=%s, dead_letter=%s",
            stats["records"],
            stats["enqueued"],
            stats["sent"],
            stats["failed"],
            stats["dead_letter"],
        )
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

        # 解析奖励信息（JSON格式）
        reward_types = ''
        reward_names = ''
        if record.get('reward_types'):
            import json
            try:
                reward_types_list = json.loads(record['reward_types'])
                reward_types = ', '.join(reward_types_list) if isinstance(reward_types_list, list) else str(reward_types_list)
            except:
                reward_types = str(record.get('reward_types', ''))

        if record.get('reward_names'):
            import json
            try:
                reward_names_list = json.loads(record['reward_names'])
                reward_names = ', '.join(reward_names_list) if isinstance(reward_names_list, list) else str(reward_names_list)
            except:
                reward_names = str(record.get('reward_names', ''))

        # 转换订单类型
        order_type_display = "自引单" if record.get('order_type') == 'self_referral' else "平台单"

        # 提取纯管家名称（去掉服务商后缀）
        housekeeper_name = record['housekeeper']
        if '_' in housekeeper_name:
            housekeeper_name = housekeeper_name.split('_')[0]

        return {
            '合同ID(_id)': record['contract_id'],
            '管家(serviceHousekeeper)': housekeeper_name,
            '合同编号(contractdocNum)': extensions.get('合同编号(contractdocNum)', ''),
            '合同金额(adjustRefundMoney)': record['contract_amount'],
            '活动期内第几个合同': record.get('contract_sequence', 0),
            '管家累计单数': extensions.get('管家累计单数', 0),
            '管家累计金额': extensions.get('管家累计金额', 0),
            '管家累计业绩金额': extensions.get('管家累计业绩金额', 0),  # 🔧 修复：使用预计算的累计业绩金额
            '激活奖励状态': '1' if reward_names else '0',
            '奖励类型': reward_types,
            '奖励名称': reward_names,
            '备注': extensions.get('备注', '无'),  # 🔧 修复：默认值改为'无'，与旧架构保持一致
            '是否发送通知': 'Y' if record.get('notification_sent') else 'N',
            '工单类型': order_type_display,  # 🔧 新增：添加工单类型字段，用于消息模板
            # 添加平台单和自引单的累计统计字段（从extensions中获取）
            '平台单累计数量': extensions.get('平台单累计数量', 0),
            '自引单累计数量': extensions.get('自引单累计数量', 0),
            '平台单累计金额': extensions.get('平台单累计金额', 0),
            '自引单累计金额': extensions.get('自引单累计金额', 0),
            '转化率(conversion)': extensions.get('转化率(conversion)', ''),
            # 添加其他必要字段
            '支付金额(paidAmount)': extensions.get('支付金额(paidAmount)', 0),
            '服务商(orgName)': record.get('service_provider', ''),
        }
    
    def _should_send_group_notification(self, record: Dict) -> bool:
        """判断是否应该发送群通知"""
        return record.get('是否发送通知') == 'N'
    
    def _build_group_notification_message(self, record: Dict) -> str:
        """构建群通知文本（发送由 outbox 负责）。"""
        # 复用现有的消息生成逻辑
        service_housekeeper = record['管家(serviceHousekeeper)']
        
        # 处理徽章逻辑（与旧架构保持一致）
        if self.config.city.value == "BJ":
            service_housekeeper = self._apply_badge_logic(service_housekeeper)
        
        # 格式化金额显示
        accumulated_amount = self._format_amount(record.get('管家累计金额', 0))
        performance_amount = self._format_amount(record.get('管家累计业绩金额', 0))
        
        # 生成群通知消息 - 根据城市和活动配置使用不同的模板
        order_type = record.get("工单类型", "平台单")

        # 根据配置决定备注逻辑
        if self.config.config_key == "BJ-PERFORMANCE-BROADCAST":
            contract_num = record.get("合同编号(contractdocNum)", "")
            accumulated_performance = self._format_amount(record.get("管家累计业绩金额", 0))
            conversion_rate = self._format_rate(record.get("转化率(conversion)", ""))

            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同 {contract_num} 并完成首付款支付条件🎉🎉🎉


🌻 本月个人累计签约业绩 {accumulated_performance} 元，当前全年平台转化率为{conversion_rate}

👊 继续加油，再接再厉！🎉🎉🎉
'''
            return msg

        if self.config.config_key == "BJ-2025-11":
            # 🔧 新增：北京11月专用消息模板（仅播报模式）
            contract_num = record.get("合同编号(contractdocNum)", "")
            global_sequence = record.get("活动期内第几个合同", 0)
            personal_count = record.get("管家累计单数", 0)
            accumulated_amount = self._format_amount(record.get('管家累计金额', 0))

            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同 {contract_num} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_sequence} 单

🌻 个人累计签约第 {personal_count} 单，累计签约 {accumulated_amount} 元

👊 继续加油，再接再厉！🎉🎉🎉
'''
            return msg

        # 其他活动的备注逻辑
        if self.config.config_key == "BJ-2025-10":
            # 北京10月：自引单和平台单都使用节节高奖励进度
            remarks = record.get("备注", "")
            if '无' in remarks:
                next_msg = '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩'
            else:
                next_msg = remarks  # 统一显示节节高进度
        elif order_type == "自引单" and self.config.city.value == "SH":
            # 上海自引单：显示独立奖励信息
            next_msg = '继续加油，争取更多奖励'
        else:
            # 其他情况：按照备注字段动态生成
            if '无' in record.get("备注", ""):
                next_msg = ''  # 空白显示
            else:
                next_msg = f'{record.get("备注", "")}'

        if self.config.config_key in ["SH-2025-10", "SH-2025-11"]:
            # 上海10月和11月专用消息模板 - 不显示自引单信息，不显示业绩信息
            order_type = record.get("工单类型", "平台单")
            platform_count = record.get("平台单累计数量", 0)
            platform_amount = self._format_amount(record.get("平台单累计金额", 0))
            conversion_rate = self._format_rate(record.get("转化率(conversion)", ""))

            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {record["管家(serviceHousekeeper)"]} 签约合同（{order_type}） {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {record.get("活动期内第几个合同", 0)} 单，

🌻 个人平台单累计签约第 {platform_count} 单。
🌻 个人平台单金额累计签约 {platform_amount} 元

🌻 个人平台单转化率 {conversion_rate}，

👊 {next_msg} 🎉🎉🎉。
'''
        elif self.config.city.value == "SH":
            # 上海群通知模板（与旧架构保持一致）- 其他上海活动使用
            order_type = record.get("工单类型", "平台单")
            platform_count = record.get("平台单累计数量", 0)
            self_referral_count = record.get("自引单累计数量", 0)
            platform_amount = self._format_amount(record.get("平台单累计金额", 0))
            self_referral_amount = self._format_amount(record.get("自引单累计金额", 0))
            conversion_rate = self._format_rate(record.get("转化率(conversion)", ""))

            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {record["管家(serviceHousekeeper)"]} 签约合同（{order_type}） {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {record.get("活动期内第几个合同", 0)} 单，

🌻 个人平台单累计签约第 {platform_count} 单， 自引单累计签约第 {self_referral_count} 单。
🌻 个人平台单金额累计签约 {platform_amount} 元，自引单金额累计签约 {self_referral_amount}元

🌻 个人平台单转化率 {conversion_rate}，

👊 {next_msg} 🎉🎉🎉。
'''
        elif self.config.config_key == "BJ-2025-10":
            # 北京10月专用消息模板 - 支持双轨统计显示
            platform_count = record.get("平台单累计数量", 0)
            self_referral_count = record.get("自引单累计数量", 0)
            platform_amount = self._format_amount(record.get("平台单累计金额", 0))
            self_referral_amount = self._format_amount(record.get("自引单累计金额", 0))
            # 新增：业绩金额显示
            performance_amount = self._format_amount(record.get("管家累计业绩金额", 0))

            # 🔧 修复：使用全局合同序号，而不是个人总数
            global_contract_sequence = record.get("活动期内第几个合同", 0)

            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同（{order_type}） {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_contract_sequence} 单

🌻 个人平台单累计签约第 {platform_count} 单，累计签约 {platform_amount} 元
🌻 个人自引单累计签约第 {self_referral_count} 单，累计签约 {self_referral_amount}元
🌻 个人累计业绩金额 {performance_amount} 元

👊 {next_msg} 🎉🎉🎉
'''
        else:
            # 其他北京活动的群通知模板
            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨
恭喜 {service_housekeeper} 签约合同 {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为活动期间平台累计签约第 {record.get("活动期内第几个合同", 0)} 单，个人累计签约第 {record.get("管家累计单数", 0)} 单。

🌻 {record["管家(serviceHousekeeper)"]}累计签约 {accumulated_amount} 元{f', 累计计入业绩 {performance_amount} 元' if ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB else ''}

👊 {next_msg}。
'''
        return msg

    def _enqueue_text_outbox(self, record: Dict, text_message: str, message_type: str) -> int:
        payload = {
            "msgtype": "text",
            "text": {"content": text_message},
        }
        dedupe_key = f"{record['合同ID(_id)']}::{message_type}"
        payload_json = json.dumps(payload, ensure_ascii=False)
        hash_value = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()[:16]
        channel = CHANNEL_SIGN_BROADCAST
        if self.config.config_key == "BJ-PERFORMANCE-BROADCAST":
            channel = CHANNEL_BJ_PERFORMANCE_BROADCAST

        return self.storage.enqueue_outbox_message(
            activity_code=self.config.activity_code,
            contract_id=record["合同ID(_id)"],
            message_type=message_type,
            webhook_url=resolve_wecom_webhook(channel),
            payload_json=payload_json,
            dedupe_key=f"{dedupe_key}::{hash_value}",
        )
    
    def _apply_badge_logic(self, housekeeper_name: str) -> str:
        """应用徽章逻辑（与旧架构保持一致）"""
        # 复用现有的徽章逻辑；可选依赖缺失时降级为“无徽章”而非阻断发送
        try:
            from modules.data_utils import should_enable_badge
            if ENABLE_BADGE_MANAGEMENT:
                elite_badge_enabled = should_enable_badge(self.config.config_key, "elite")
                if elite_badge_enabled and housekeeper_name in ELITE_HOUSEKEEPER:
                    return f'{ELITE_BADGE_NAME}{housekeeper_name}'
        except Exception as e:
            self.logger.warning(f"徽章逻辑降级（不影响发送）: {e}")
        return housekeeper_name
    
    def _format_amount(self, amount) -> str:
        """格式化金额显示"""
        try:
            return f"{int(float(amount)):,d}"
        except (ValueError, TypeError):
            return "0"

    def _format_rate(self, rate) -> str:
        """格式化转化率显示"""
        from modules.data_utils import preprocess_rate
        return preprocess_rate(str(rate))
    
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
