# jobs.py
import logging
from modules.request_module import send_request_with_managed_session
from modules.data_processing_module import *
from modules.data_utils import *
from modules.notification_module import *
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
    """待预约工单提醒任务"""
    from modules.data_utils import (
        filter_orders_by_time_threshold,
        group_orders_by_org,
        format_pending_orders_message_text
    )

    logging.info('待预约工单提醒任务开始...')

    try:
        # 1. 获取数据
        api_url = API_URL_PENDING_ORDERS_REMINDER
        logging.info('正在获取待预约工单数据...')
        response = send_request_with_managed_session(api_url)

        if not response or 'data' not in response:
            logging.error('API请求失败或数据格式异常')
            return

        orders_data = response['data']['rows']
        total_orders = len(orders_data)
        logging.info(f'获取到 {total_orders} 条原始工单数据')

        if total_orders == 0:
            logging.info('没有待预约工单，任务结束')
            return

        # 2. 应用时间过滤
        logging.info('正在应用时间过滤规则...')
        logging.info('- 排除待预约状态48小时之内的工单')
        logging.info('- 排除暂不上门状态48小时之内的工单')
        filtered_orders_data = filter_orders_by_time_threshold(orders_data)
        filtered_count = len(filtered_orders_data)
        logging.info(f'过滤后剩余 {filtered_count} 条工单数据')

        if filtered_count == 0:
            logging.info('过滤后没有符合条件的工单，任务结束')
            return

        # 3. 数据处理和分组
        logging.info('正在按服务商分组工单数据...')
        grouped_orders = group_orders_by_org(filtered_orders_data)
        org_count = len(grouped_orders)
        logging.info(f'共分为 {org_count} 个服务商组')

        # 4. 发送通知
        success_count = 0
        failed_count = 0

        for org_name, orders in grouped_orders.items():
            try:
                logging.info(f'正在为 {org_name} 发送提醒，工单数量: {len(orders)}')

                # 格式化消息（使用文字版格式）
                message = format_pending_orders_message_text(org_name, orders)

                # 获取webhook地址
                webhook_url = ORG_WEBHOOKS.get(org_name, WEBHOOK_URL_DEFAULT)

                # 发送消息（使用文字格式）
                post_text_to_webhook(message, webhook_url)

                success_count += 1
                logging.info(f'✓ {org_name} 提醒发送成功')

            except Exception as e:
                failed_count += 1
                logging.error(f'✗ {org_name} 提醒发送失败: {e}')

        # 5. 任务总结
        logging.info(f'待预约工单提醒任务完成 - 成功: {success_count}, 失败: {failed_count}')

    except Exception as e:
        logging.error(f'待预约工单提醒任务执行失败: {e}')
        import traceback
        logging.error(traceback.format_exc())

# [已移除 - 旧架构代码已备份到 backup/legacy-code 分支]