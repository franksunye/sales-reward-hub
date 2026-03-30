# jobs.py
import logging
from modules.request_module import send_request_with_managed_session
from modules.data_utils import *
from modules.config import *
from modules.service_provider_sla_monitor import process_sla_violations

# [已移除 - 旧架构代码已备份到 backup/legacy-code 分支]

def generate_daily_service_report():
    """SLA 日报任务（兼容入口，转发到数据库优先版本）。"""
    from modules.core.sla_jobs import generate_daily_service_report_v2

    return generate_daily_service_report_v2()

def send_pending_orders_reminder():
    """待预约工单提醒任务（兼容入口，转发到数据库优先版本）。"""
    from modules.core.pending_orders_jobs import send_pending_orders_reminder_v2

    return send_pending_orders_reminder_v2()

# [已移除 - 旧架构代码已备份到 backup/legacy-code 分支]
