# jobs.py
import logging
from modules.request_module import send_request_with_managed_session
from modules.data_processing_module import *
from modules.data_utils import *
from modules.notification_module import *
from modules.config import *
from modules.service_provider_sla_monitor import process_sla_violations

# 2025年8月，北京. 
# 幸运数字8，单合同金额1万以上和以下幸运奖励不同；节节高三档；
# 单个项目（工单）签约合同金额大于5万时，参与累计合同金额计算时均按5万计入。
def signing_and_sales_incentive_aug_beijing():
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_BJ_AUG
    performance_data_filename = PERFORMANCE_DATA_FILENAME_BJ_AUG
    status_filename = STATUS_FILENAME_BJ_AUG
    api_url = API_URL_BJ_AUG

    logging.info('BEIJING 2025 8月, Job started ...')

    response = send_request_with_managed_session(api_url)
 
    logging.info('BEIJING 2025 8月, Request sent')

    rows = response['data']['rows']

    columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)", "平均客单价(average)"]
    save_to_csv_with_headers(rows,contract_data_filename,columns)

    logging.info(f'BEIJING 2025 8月, Data saved to {contract_data_filename}')

    contract_data = read_contract_data(contract_data_filename)

    existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)

    housekeeper_award_lists = get_housekeeper_award_list(performance_data_filename)

    # 当月的数据处理逻辑
    processed_data = process_data_jun_beijing(contract_data, existing_contract_ids,housekeeper_award_lists)
    logging.info('BEIJING 2025 8月, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池','计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    # 当月的数据处理逻辑
    notify_awards_jun_beijing(performance_data_filename, status_filename)

    archive_file(contract_data_filename)
    logging.info('BEIJING 2025 8月, Data archived')

    logging.info('BEIJING 2025 8月, Job ended')

# 2025年8月，上海. 签约和奖励播报，规则与7月相同
def signing_and_sales_incentive_aug_shanghai():
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_SH_AUG
    performance_data_filename = PERFORMANCE_DATA_FILENAME_SH_AUG
    status_filename = STATUS_FILENAME_SH_AUG
    api_url = API_URL_SH_AUG

    logging.info('SHANGHAI 2025 8月 Conq & triumph, take 1 more city, Job started ...')
    response = send_request_with_managed_session(api_url)
    logging.info('SHANGHAI 2025 8月 Conq & triumph, take 1 more city, Request sent')

    rows = response['data']['rows']

    columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)", "平均客单价(average)"]
    save_to_csv_with_headers(rows,contract_data_filename,columns)

    logging.info(f'SHANGHAI 2025 8月 Conq & triumph, take 1 more city, Data saved to {contract_data_filename}')

    contract_data = read_contract_data(contract_data_filename)

    existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)

    # 获取管家奖励列表，升级唯一奖励列表
    housekeeper_award_lists = get_unique_housekeeper_award_list(performance_data_filename)

    # 当月的数据处理逻辑，奖励规则与4月保持一致
    processed_data = process_data_shanghai_apr(contract_data, existing_contract_ids, housekeeper_award_lists)

    logging.info('SHANGHAI 2025 8月 Conq & triumph, take 1 more city, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池', '计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    # 当月的通知数据处理逻辑（与三月一致），与4月保持一致
    notify_awards_shanghai_generate_message_march(performance_data_filename, status_filename, contract_data)

    archive_file(contract_data_filename)
    logging.info('SHANGHAI 2025 8月 Conq & triumph, take 1 more city, Data archived')

    logging.info('SHANGHAI 2025 8月 Conq & triumph, take 1 more city, Job ended')


# 2025年9月，上海. 签约和奖励播报，支持平台单和自引单双轨处理
def signing_and_sales_incentive_sep_shanghai():
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_SH_SEP
    performance_data_filename = PERFORMANCE_DATA_FILENAME_SH_SEP
    status_filename = STATUS_FILENAME_SH_SEP
    api_url = API_URL_SH_SEP

    logging.info('SHANGHAI 2025 9月 双轨激励, Job started ...')

    # 1. 获取API数据
    response = send_request_with_managed_session(api_url)
    logging.info('SHANGHAI 2025 9月 双轨激励, Request sent')

    # 检查API响应
    if not response or 'data' not in response:
        logging.error('SHANGHAI 2025 9月 双轨激励, API request failed or returned invalid data')
        return

    rows = response['data']['rows']

    # 2. 字段映射：API字段名 -> CSV字段名
    contract_data = []
    for row in rows:
        mapped_row = {
            '合同ID(_id)': row[0],
            '活动城市(province)': row[1],
            '工单编号(serviceAppointmentNum)': row[2],
            'Status': row[3],
            '管家(serviceHousekeeper)': row[4],
            '合同编号(contractdocNum)': row[5],
            '合同金额(adjustRefundMoney)': row[6],
            '支付金额(paidAmount)': row[7],
            '差额(difference)': row[8],
            'State': row[9],
            '创建时间(createTime)': row[10],
            '服务商(orgName)': row[11],
            '签约时间(signedDate)': row[12],
            'Doorsill': row[13],
            '款项来源类型(tradeIn)': row[14],
            '转化率(conversion)': row[15],
            '平均客单价(average)': row[16],
            # 新增字段
            '管家ID(serviceHousekeeperId)': row[17],
            '工单类型(sourceType)': row[18],
            '客户联系地址(contactsAddress)': row[19],
            '项目地址(projectAddress)': row[20]
        }
        contract_data.append(mapped_row)

    # 3. 保存原始数据到CSV文件（包含新增字段）
    # 修复：使用与数据结构匹配的列名
    columns = [
        "合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)",
        "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State",
        "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)",
        "平均客单价(average)", "管家ID(serviceHousekeeperId)", "工单类型(sourceType)", "客户联系地址(contactsAddress)", "项目地址(projectAddress)"
    ]
    save_to_csv_with_headers(contract_data, contract_data_filename, columns)
    logging.info('SHANGHAI 2025 9月 双轨激励, Raw data saved')

    # 4. 获取已存在的合同ID
    existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)
    logging.info(f'SHANGHAI 2025 9月 双轨激励, Found {len(existing_contract_ids)} existing contracts')

    # 5. 获取管家历史奖励列表
    housekeeper_award_lists = get_unique_housekeeper_award_list(performance_data_filename)

    # 6. 数据处理（双轨处理逻辑）
    processed_data = process_data_shanghai_sep(contract_data, existing_contract_ids, housekeeper_award_lists)
    logging.info('SHANGHAI 2025 9月 双轨激励, Data processed')

    # 7. 写入业绩数据文件（包含新增字段）
    performance_data_headers = [
        '活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status',
        '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)',
        '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)',
        '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)',
        '转化率(conversion)', '平均客单价(average)', '活动期内第几个合同', '管家累计金额',
        '管家累计单数', '奖金池', '计入业绩金额', '激活奖励状态', '奖励类型', '奖励名称',
        '是否发送通知', '备注', '登记时间',
        # 新增字段
        '管家ID(serviceHousekeeperId)', '工单类型', '客户联系地址(contactsAddress)',
        '项目地址(projectAddress)', '平台单累计数量', '平台单累计金额',
        '自引单累计数量', '自引单累计金额'
    ]

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    logging.info('SHANGHAI 2025 9月 双轨激励, Performance data written')

    # 8. 通知处理（使用通用函数）
    notify_awards_shanghai_generic(performance_data_filename, status_filename, "SH-2025-09")
    logging.info('SHANGHAI 2025 9月 双轨激励, Notifications processed')

    # 9. 归档原始数据文件
    archive_file(contract_data_filename)
    logging.info('SHANGHAI 2025 9月 双轨激励, Data archived')

    logging.info('SHANGHAI 2025 9月 双轨激励, Job ended')

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


# 2025年9月，北京.
# 幸运数字改为个人签约顺序（5的倍数），统一58元奖励；节节高10个合同解锁，奖励翻倍；禁用徽章机制
def signing_and_sales_incentive_sep_beijing():
    """北京2025年9月签约激励Job"""
    from modules.config import (
        API_URL_BJ_SEP, TEMP_CONTRACT_DATA_FILE_BJ_SEP,
        PERFORMANCE_DATA_FILENAME_BJ_SEP, STATUS_FILENAME_BJ_SEP
    )
    from modules.data_processing_module import process_data_sep_beijing
    from modules.notification_module import notify_awards_sep_beijing

    logging.info('BEIJING 2025 9月, Job started ...')

    response = send_request_with_managed_session(API_URL_BJ_SEP)
    logging.info('BEIJING 2025 9月, Request sent')

    rows = response['data']['rows']
    columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)", "平均客单价(average)"]
    save_to_csv_with_headers(rows, TEMP_CONTRACT_DATA_FILE_BJ_SEP, columns)

    logging.info(f'BEIJING 2025 9月, Data saved to {TEMP_CONTRACT_DATA_FILE_BJ_SEP}')

    contract_data = read_contract_data(TEMP_CONTRACT_DATA_FILE_BJ_SEP)
    existing_contract_ids = collect_unique_contract_ids_from_file(PERFORMANCE_DATA_FILENAME_BJ_SEP)
    housekeeper_award_lists = get_housekeeper_award_list(PERFORMANCE_DATA_FILENAME_BJ_SEP)

    # 使用9月专用数据处理逻辑
    processed_data = process_data_sep_beijing(contract_data, existing_contract_ids, housekeeper_award_lists)
    logging.info('BEIJING 2025 9月, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池','计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(PERFORMANCE_DATA_FILENAME_BJ_SEP, processed_data, performance_data_headers)

    # 使用9月专用通知逻辑
    notify_awards_sep_beijing(PERFORMANCE_DATA_FILENAME_BJ_SEP, STATUS_FILENAME_BJ_SEP)

    archive_file(TEMP_CONTRACT_DATA_FILE_BJ_SEP)
    logging.info('BEIJING 2025 9月, Data archived')
    logging.info('BEIJING 2025 9月, Job ended')