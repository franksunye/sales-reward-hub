# jobs.py
import logging
from modules.request_module import send_request_with_managed_session
from modules.data_utils import *
from modules.config import *
from modules.service_provider_sla_monitor import process_sla_violations

# [已移除 - 旧架构代码已备份到 backup/legacy-code 分支]

def generate_daily_service_report():
    logging.info('Daily service report generation started...')
    api_url = API_URL_DAILY_SERVICE_REPORT
    temp_daily_service_report_file = TEMP_DAILY_SERVICE_REPORT_FILE
    status_code_filename = DAILY_SERVICE_REPORT_RECORD_FILE

    try:
        # 1. 发送请求以获取日报数据
        response = send_request_with_managed_session(api_url)
        logging.info('Daily service report request sent successfully.')

        # 2. 处理响应数据
        report_data = response['data']['rows']
        if not report_data:
            logging.warning('No data found for the daily service report.')
            # return

        # 3. 保存数据到CSV文件
        columns = ["_id", "sid", "saCreateTime", "orderNum", "province", "orgName", "supervisorName", "sourceType", "status", "msg", "memo", "workType", "createTime"]
        save_to_csv_with_headers(report_data, temp_daily_service_report_file, columns)

        # 4. 读取数据
        report_data = read_daily_service_report(temp_daily_service_report_file)
        logging.info(f"Report data: {report_data}")

        # 新的SLA违规检查并发送通知服务
        process_sla_violations(report_data)
        logging.info('SLA violations processed successfully.')

        # # 当前适用的发送日常服务报告
        # notify_daily_service_report(report_data, status_code_filename)
        # logging.info('Daily service report notification sent successfully.')

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    logging.info('Daily service report generation completed.')

def send_pending_orders_reminder():
    """待预约工单提醒任务（兼容入口，转发到数据库优先版本）。"""
    from modules.core.pending_orders_jobs import send_pending_orders_reminder_v2

    return send_pending_orders_reminder_v2()

# [已移除 - 旧架构代码已备份到 backup/legacy-code 分支]
