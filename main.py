import logging
import schedule
import time
import traceback

from modules.log_config import setup_logging
from modules.config import RUN_JOBS_SERIALLY_SCHEDULE
from modules.core.beijing_jobs import signing_broadcast_beijing
from modules.core.pending_orders_jobs import send_pending_orders_reminder_v2
from modules.core.project_settlement_jobs import sync_contract_completion_smartsheet_v2
from modules.core.project_settlement_jobs import sync_payment_records_smartsheet_v2
from modules.core.project_settlement_jobs import sync_project_settlement_smartsheet_v2
from modules.core.sla_jobs import generate_daily_service_report_v2


setup_logging()


def run_beijing_sign_broadcast_task():
    """北京签约播报常驻任务（无月份限制）。"""
    try:
        logging.info("开始执行北京签约播报任务")
        signing_broadcast_beijing()
        logging.info("北京签约播报任务执行完成")
    except Exception as e:
        logging.error(f"执行北京签约播报任务失败: {e}")
        logging.error(traceback.format_exc())


def run_pending_orders_reminder_task():
    """待预约工单提醒常驻任务。"""
    try:
        logging.info("开始执行待预约工单提醒任务")
        send_pending_orders_reminder_v2()
        logging.info("待预约工单提醒任务执行完成")
    except Exception as e:
        logging.error(f"执行待预约工单提醒任务失败: {e}")
        logging.error(traceback.format_exc())


def run_daily_service_report_task():
    """SLA 日报/周报任务。"""
    try:
        logging.info("开始执行 SLA 日报任务")
        generate_daily_service_report_v2()
        logging.info("SLA 日报任务执行完成")
    except Exception as e:
        logging.error(f"执行 SLA 日报任务失败: {e}")
        logging.error(traceback.format_exc())


def run_project_settlement_smartsheet_task():
    """项目结算企业微信电子表格同步任务。"""
    try:
        logging.info("开始执行项目结算电子表格同步任务")
        sync_project_settlement_smartsheet_v2()
        logging.info("项目结算电子表格同步任务执行完成")
    except Exception as e:
        logging.error(f"执行项目结算电子表格同步任务失败: {e}")
        logging.error(traceback.format_exc())


def run_contract_completion_smartsheet_task():
    """合同完工企业微信电子表格同步任务。"""
    try:
        logging.info("开始执行合同完工电子表格同步任务")
        sync_contract_completion_smartsheet_v2()
        logging.info("合同完工电子表格同步任务执行完成")
    except Exception as e:
        logging.error(f"执行合同完工电子表格同步任务失败: {e}")
        logging.error(traceback.format_exc())


def run_payment_records_smartsheet_task():
    """支付记录企业微信电子表格同步任务。"""
    try:
        logging.info("开始执行支付记录电子表格同步任务")
        sync_payment_records_smartsheet_v2()
        logging.info("支付记录电子表格同步任务执行完成")
    except Exception as e:
        logging.error(f"执行支付记录电子表格同步任务失败: {e}")
        logging.error(traceback.format_exc())


# 常驻任务
schedule.every(RUN_JOBS_SERIALLY_SCHEDULE).minutes.do(run_beijing_sign_broadcast_task)
schedule.every(RUN_JOBS_SERIALLY_SCHEDULE).minutes.do(run_pending_orders_reminder_task)
schedule.every(RUN_JOBS_SERIALLY_SCHEDULE).minutes.do(run_project_settlement_smartsheet_task)
schedule.every(RUN_JOBS_SERIALLY_SCHEDULE).minutes.do(run_contract_completion_smartsheet_task)
schedule.every(RUN_JOBS_SERIALLY_SCHEDULE).minutes.do(run_payment_records_smartsheet_task)
schedule.every().day.at("08:10").do(run_daily_service_report_task)


if __name__ == "__main__":
    logging.info("Program started (Beijing sign broadcast + pending orders reminder + project settlement smartsheet + contract completion smartsheet + payment records smartsheet + daily service report)")

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Scheduler loop exception: {e}")
            logging.error(traceback.format_exc())
            time.sleep(5)
