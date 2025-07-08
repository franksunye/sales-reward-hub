# jobs.py
import logging
from modules.request_module import send_request_with_managed_session
from modules.data_processing_module import *
from modules.file_utils import *
from modules.notification_module import *
from modules.config import *
from modules.service_provider_sla_monitor import process_sla_violations

# 2025年7月，北京. 
# 幸运数字8，单合同金额1万以上和以下幸运奖励不同；节节高三档；
# 单个项目（工单）签约合同金额大于5万时，参与累计合同金额计算时均按5万计入。
def signing_and_sales_incentive_july_beijing():
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_BJ_JULY
    performance_data_filename = PERFORMANCE_DATA_FILENAME_BJ_JULY
    status_filename = STATUS_FILENAME_BJ_JULY
    api_url = API_URL_BJ_JULY

    logging.info('BEIJING 2025 7月, Job started ...')

    response = send_request_with_managed_session(api_url)
 
    logging.info('BEIJING 2025 7月, Request sent')

    rows = response['data']['rows']

    columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)", "平均客单价(average)"]
    save_to_csv_with_headers(rows,contract_data_filename,columns)

    logging.info(f'BEIJING 2025 7月, Data saved to {contract_data_filename}')

    contract_data = read_contract_data(contract_data_filename)

    existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)

    housekeeper_award_lists = get_housekeeper_award_list(performance_data_filename)

    # 当月的数据处理逻辑
    processed_data = process_data_jun_beijing(contract_data, existing_contract_ids,housekeeper_award_lists)
    logging.info('BEIJING 2025 7月, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池','计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    # 当月的数据处理逻辑
    notify_awards_jun_beijing(performance_data_filename, status_filename)

    archive_file(contract_data_filename)
    logging.info('BEIJING 2025 7月, Data archived')

    logging.info('BEIJING 2025 7月, Job ended')
    
# 2025年6月，北京. 
# 幸运数字8，单合同金额1万以上和以下幸运奖励不同；节节高三档；
# 单个项目（工单）签约合同金额大于5万时，参与累计合同金额计算时均按5万计入。
def signing_and_sales_incentive_jun_beijing():
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_BJ_JUN
    performance_data_filename = PERFORMANCE_DATA_FILENAME_BJ_JUN
    status_filename = STATUS_FILENAME_BJ_JUN
    api_url = API_URL_BJ_JUN

    logging.info('BEIJING 2025 6月, Job started ...')

    response = send_request_with_managed_session(api_url)
 
    logging.info('BEIJING 2025 6月, Request sent')

    rows = response['data']['rows']

    columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)", "平均客单价(average)"]
    save_to_csv_with_headers(rows,contract_data_filename,columns)

    logging.info(f'BEIJING 2025 6月, Data saved to {contract_data_filename}')

    contract_data = read_contract_data(contract_data_filename)

    existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)

    housekeeper_award_lists = get_housekeeper_award_list(performance_data_filename)

    # 当月的数据处理逻辑
    processed_data = process_data_jun_beijing(contract_data, existing_contract_ids,housekeeper_award_lists)
    logging.info('BEIJING 2025 6月, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池','计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    # 当月的数据处理逻辑
    notify_awards_jun_beijing(performance_data_filename, status_filename)

    archive_file(contract_data_filename)
    logging.info('BEIJING 2025 6月, Data archived')

    logging.info('BEIJING 2025 6月, Job ended')

# 2025年7月，上海. 签约和奖励播报，规则与4月相同
def signing_and_sales_incentive_july_shanghai():
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_SH_JULY
    performance_data_filename = PERFORMANCE_DATA_FILENAME_SH_JULY
    status_filename = STATUS_FILENAME_SH_JULY
    api_url = API_URL_SH_JULY

    logging.info('SHANGHAI 2025 7月 Conq & triumph, take 1 more city, Job started ...')
    response = send_request_with_managed_session(api_url)
    logging.info('SHANGHAI 2025 7月 Conq & triumph, take 1 more city, Request sent')

    rows = response['data']['rows']

    columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)", "平均客单价(average)"]
    save_to_csv_with_headers(rows,contract_data_filename,columns)

    logging.info(f'SHANGHAI 2025 7月 Conq & triumph, take 1 more city, Data saved to {contract_data_filename}')

    contract_data = read_contract_data(contract_data_filename)

    existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)

    # 获取管家奖励列表，升级唯一奖励列表
    housekeeper_award_lists = get_unique_housekeeper_award_list(performance_data_filename)

    # 当月的数据处理逻辑，奖励规则与4月保持一致
    processed_data = process_data_shanghai_apr(contract_data, existing_contract_ids, housekeeper_award_lists)

    logging.info('SHANGHAI 2025 7月 Conq & triumph, take 1 more city, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池', '计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    # 当月的通知数据处理逻辑（与三月一致），与4月保持一致
    notify_awards_shanghai_generate_message_march(performance_data_filename, status_filename, contract_data)

    archive_file(contract_data_filename)
    logging.info('SHANGHAI 2025 7月 Conq & triumph, take 1 more city, Data archived')

    logging.info('SHANGHAI 2025 7月 Conq & triumph, take 1 more city, Job ended')   

# 2025年6月，上海. 签约和奖励播报，规则与4月相同
def signing_and_sales_incentive_jun_shanghai():
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_SH_JUN
    performance_data_filename = PERFORMANCE_DATA_FILENAME_SH_JUN
    status_filename = STATUS_FILENAME_SH_JUN
    api_url = API_URL_SH_JUN

    logging.info('SHANGHAI 2025 6月 Conq & triumph, take 1 more city, Job started ...')
    response = send_request_with_managed_session(api_url)
    logging.info('SHANGHAI 2025 6月 Conq & triumph, take 1 more city, Request sent')

    rows = response['data']['rows']

    columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)", "转化率(conversion)", "平均客单价(average)"]
    save_to_csv_with_headers(rows,contract_data_filename,columns)

    logging.info(f'SHANGHAI 2025 6月 Conq & triumph, take 1 more city, Data saved to {contract_data_filename}')

    contract_data = read_contract_data(contract_data_filename)

    existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)

    # 获取管家奖励列表，升级唯一奖励列表
    housekeeper_award_lists = get_unique_housekeeper_award_list(performance_data_filename)

    # 当月的数据处理逻辑，奖励规则与4月保持一致
    processed_data = process_data_shanghai_apr(contract_data, existing_contract_ids, housekeeper_award_lists)

    logging.info('SHANGHAI 2025 6月 Conq & triumph, take 1 more city, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池', '计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    # 当月的通知数据处理逻辑（与三月一致），与4月保持一致
    notify_awards_shanghai_generate_message_march(performance_data_filename, status_filename, contract_data)

    archive_file(contract_data_filename)
    logging.info('SHANGHAI 2025 6月 Conq & triumph, take 1 more city, Data archived')

    logging.info('SHANGHAI 2025 6月 Conq & triumph, take 1 more city, Job ended')   

def check_technician_status():
    api_url = API_URL_TS
    status_filename = STATUS_FILENAME_TS

    logging.info('BEIJING, Technician Status Check Job started')

    response = send_request_with_managed_session(api_url)    
    status_changes = response['data']['rows']

    notify_technician_status_changes(status_changes, status_filename)

    logging.info('BEIJING, Technician Status Check Job ended') 

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

def check_contact_timeout():
    api_url = API_URL_CONTACT_TIMEOUT
    # notify_status_filename = STATUS_FILENAME_CONTACT_TIMEOUT

    logging.info('Contact Timeout Check, Job started ...')

    response = send_request_with_managed_session(api_url)

    if response is None:
        logging.error('Failed to get response for contact timeout check')
        return

    contact_timeout_data = response['data']['rows']
    print(contact_timeout_data)  # 打印 status_changes

    notify_contact_timeout_changes_template_card(contact_timeout_data)

    logging.info('Contact Timeout Check, Job ended')

def format_create_time(iso_time_str):
    """将ISO时间格式转换为易读格式"""
    from datetime import datetime
    try:
        # 处理带时区的ISO格式
        if '+' in iso_time_str:
            dt = datetime.fromisoformat(iso_time_str)
        else:
            dt = datetime.fromisoformat(iso_time_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        logging.warning(f'时间格式转换失败: {iso_time_str}, 错误: {e}')
        return iso_time_str

def filter_orders_by_time_threshold(orders_data):
    """
    过滤工单数据，排除：
    - 待预约状态，48小时之内的需要排除
    - 暂不上门状态，48小时之内的需要排除

    Args:
        orders_data: 原始工单数据列表

    Returns:
        filtered_orders: 过滤后的工单数据列表
    """
    from datetime import datetime, timezone

    filtered_orders = []
    current_time = datetime.now(timezone.utc)

    for order in orders_data:
        try:
            # 解析工单数据
            order_info = {
                'orderNum': order[0],
                'name': order[1],
                'address': order[2],
                'supervisorName': order[3],
                'createTime': order[4],
                'orgName': order[5],
                'orderstatus': order[6]
            }

            # 解析创建时间
            create_time_str = order_info['createTime']
            if '+' in create_time_str:
                create_time = datetime.fromisoformat(create_time_str)
            else:
                create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))

            # 确保创建时间有时区信息
            if create_time.tzinfo is None:
                create_time = create_time.replace(tzinfo=timezone.utc)

            # 计算时间差（小时）
            time_diff = current_time - create_time
            hours_elapsed = time_diff.total_seconds() / 3600

            # 获取工单状态
            order_status = order_info['orderstatus']

            # 过滤逻辑：待预约和暂不上门状态，48小时之内的需要排除
            should_include = True

            if ('待预约' in order_status or '暂不上门' in order_status) and hours_elapsed < 48:
                should_include = False
                logging.info(f"过滤掉工单 {order_info['orderNum']} (状态: {order_status}, 创建时间: {hours_elapsed:.1f}小时前)")

            if should_include:
                filtered_orders.append(order)

        except Exception as e:
            logging.warning(f"处理工单数据时出错，跳过: {order}, 错误: {e}")
            continue

    return filtered_orders

def group_orders_by_org(orders_data):
    """按服务商分组工单数据"""
    grouped = {}

    for order in orders_data:
        try:
            # 根据API测试结果，字段索引映射
            order_info = {
                'orderNum': order[0],
                'name': order[1],
                'address': order[2],
                'supervisorName': order[3],
                'createTime': order[4],
                'orgName': order[5],
                'orderstatus': order[6]
            }

            org_name = order_info['orgName']
            if org_name not in grouped:
                grouped[org_name] = []
            grouped[org_name].append(order_info)

        except (IndexError, KeyError) as e:
            logging.warning(f'工单数据格式异常，跳过: {order}, 错误: {e}')
            continue

    return grouped

def format_pending_orders_message_text(org_name, orders):
    """格式化工单提醒消息（文本格式，保留作为备用）"""
    count = len(orders)

    message_lines = [
        f"📋 待预约工单提醒 ({org_name})",
        "",
        f"共有 {count} 个工单待预约：",
        ""
    ]

    for i, order in enumerate(orders, 1):
        # 使用新的简化格式
        simple_date = format_simple_date(order['createTime'])
        retention_duration = calculate_retention_duration(order['createTime'])
        simple_order_num = simplify_order_number(order['orderNum'])

        order_text = f"""{i:02d}. 工单号：{simple_order_num}
     客户：{order['name']}
     地址：{order['address']}
     负责人：{order['supervisorName']}
     创建时间：{simple_date}（{retention_duration}）
     状态：{order['orderstatus']}"""

        message_lines.append(order_text)
        if i < count:  # 不是最后一个，添加空行
            message_lines.append("")

    message_lines.extend([
        "",
        "请及时跟进处理，如有疑问请联系运营人员。"
    ])

    return "\n".join(message_lines)

def simplify_order_number(order_num):
    """简化工单号，只保留后5位数字"""
    if not order_num:
        return "-"

    # 提取数字部分
    import re
    numbers = re.findall(r'\d+', order_num)
    if numbers:
        # 取最后一个数字串的后5位
        last_number = numbers[-1]
        if len(last_number) >= 5:
            return last_number[-5:]
        else:
            return last_number
    return order_num

def format_simple_date(create_time_str):
    """格式化创建时间为简单的月-日格式"""
    from datetime import datetime

    try:
        # 解析创建时间
        if '+' in create_time_str:
            create_time = datetime.fromisoformat(create_time_str)
        else:
            create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))

        # 格式化为MM-DD
        return f"{create_time.month:02d}-{create_time.day:02d}"

    except Exception as e:
        logging.warning(f"时间格式化失败: {create_time_str}, 错误: {e}")
        return "未知"

def calculate_retention_duration(create_time_str):
    """计算工单滞留时长"""
    from datetime import datetime, timezone

    try:
        # 解析创建时间
        if '+' in create_time_str:
            create_time = datetime.fromisoformat(create_time_str)
        else:
            create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))

        # 获取当前时间（带时区）
        current_time = datetime.now(timezone.utc)

        # 确保创建时间也有时区信息
        if create_time.tzinfo is None:
            create_time = create_time.replace(tzinfo=timezone.utc)

        # 计算时间差
        duration = current_time - create_time

        # 格式化显示（简化为天数颗粒度）
        days = int(duration.total_seconds() // (24 * 3600))
        return f"{days}天"

    except Exception as e:
        logging.warning(f"滞留时长计算失败: {create_time_str}, 错误: {e}")
        return "未知"

def format_pending_orders_message(org_name, orders):
    """格式化工单提醒消息（表格格式）"""
    count = len(orders)

    # 消息头部
    header = f"📋 **待预约工单提醒** ({org_name})\n\n共有 **{count}** 个工单待预约：\n"

    # 表格头部（增加滞留时长列）
    table_header = """
| 序号 | 工单号 | 滞留时长 | 客户 | 地址 | 管家 | 创建时间 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |"""

    # 表格内容
    table_rows = []
    for i, order in enumerate(orders, 1):
        # 使用新的简化格式
        simple_date = format_simple_date(order['createTime'])
        retention_duration = calculate_retention_duration(order['createTime'])
        simple_order_num = simplify_order_number(order['orderNum'])

        # 处理可能包含特殊字符的字段
        customer = order['name'].replace('|', '\\|') if order['name'] else '-'
        address = order['address'].replace('|', '\\|') if order['address'] else '-'
        supervisor = order['supervisorName'].replace('|', '\\|') if order['supervisorName'] else '-'
        status = order['orderstatus'].replace('|', '\\|') if order['orderstatus'] else '-'

        row = f"| {i:02d} | {simple_order_num} | {retention_duration} | {customer} | {address} | {supervisor} | {simple_date} | {status} |"
        table_rows.append(row)

    # 消息底部
    footer = "\n\n请及时跟进处理，如有疑问请联系运营人员。"

    # 组合完整消息
    message = header + table_header + "\n" + "\n".join(table_rows) + footer

    return message

def send_pending_orders_reminder():
    """待预约工单提醒任务"""
    from datetime import datetime

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
    