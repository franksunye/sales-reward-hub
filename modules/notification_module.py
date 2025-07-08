# notification_module.py
import logging
import pyautogui
import pyperclip
import time
import pygetwindow as gw
import re
from modules.log_config import setup_logging
import requests
from modules.config import *
from modules.file_utils import load_send_status, update_send_status, get_all_records_from_csv, write_performance_data_to_csv
from datetime import datetime, timezone
from task_manager import create_task

# 配置日志
setup_logging()
# 使用专门的发送消息日志记录器
send_logger = logging.getLogger('sendLogger')

def generate_award_message(record, awards_mapping, city="BJ"):
    service_housekeeper = record["管家(serviceHousekeeper)"]
    contract_number = record["合同编号(contractdocNum)"]
    award_messages = []

    # 只有北京的精英管家才能获得奖励翻倍和显示徽章，上海的管家不参与奖励翻倍也不显示徽章
    if ENABLE_BADGE_MANAGEMENT and (service_housekeeper in ELITE_HOUSEKEEPER) and city == "BJ":
        # 如果是北京的精英管家，添加徽章
        service_housekeeper = f'{ELITE_BADGE_NAME}{service_housekeeper}'

        # 获取奖励类型和名称列表
        reward_types = record["奖励类型"].split(', ') if record["奖励类型"] else []
        reward_names = record["奖励名称"].split(', ') if record["奖励名称"] else []

        # 创建奖励类型到奖励名称的映射
        reward_type_map = {}
        if len(reward_types) == len(reward_names):
            for i in range(len(reward_types)):
                if i < len(reward_names):
                    reward_type_map[reward_names[i]] = reward_types[i]

        for award in reward_names:
            if award in awards_mapping:
                award_info = awards_mapping[award]
                # 检查奖励类型，只有节节高奖励才翻倍
                reward_type = reward_type_map.get(award, "")

                if reward_type == "节节高":
                    # 节节高奖励翻倍
                    try:
                        award_info_double = str(int(award_info) * 2)
                        award_messages.append(f'达成 {award} 奖励条件，奖励金额 {award_info} 元，同时触发"精英连击双倍奖励"，奖励金额\U0001F680直升至 {award_info_double} 元！\U0001F9E7\U0001F9E7\U0001F9E7')
                    except ValueError:
                        award_messages.append(f'达成{award}奖励条件，获得签约奖励{award_info}元 \U0001F9E7\U0001F9E7\U0001F9E7')
                else:
                    # 幸运数字奖励不翻倍
                    award_messages.append(f'达成{award}奖励条件，获得签约奖励{award_info}元 \U0001F9E7\U0001F9E7\U0001F9E7')
    else:
        # 不启用徽章功能或非北京管家
        # 上海的管家不添加徽章，北京的普通管家也不添加徽章
        for award in record["奖励名称"].split(', '):
            if award in awards_mapping:
                award_info = awards_mapping[award]
                award_messages.append(f'达成{award}奖励条件，获得签约奖励{award_info}元 \U0001F9E7\U0001F9E7\U0001F9E7')

    return f'{service_housekeeper}签约合同{contract_number}\n\n' + '\n'.join(award_messages)

def preprocess_rate(rate):
    # 检查比率数据是否为空或不是有效的浮点数
    if rate.strip() and rate.replace('.', '', 1).isdigit():
        # 将比率数据转换为浮点数
        rate_float = float(rate)
        # 如果rate大于等于1，返回"100%"
        if rate_float >= 1:
            return "100%"
        else:
            # 将比率数据转换为浮点数，然后乘以100得到百分比
            return f"{int(rate_float * 100)}%"
    else:
        # 处理无效或空数据（例如，返回"N/A"或其他占位符）
        return "-"

def preprocess_amount(amount):
    # 检查金额数据是否为空或不是有效的浮点数
    if amount.strip() and amount.replace('.', '', 1).isdigit():
        # 将金额数据转换为浮点数，然后格式化为带有千位符号的整数字符串
        return f"{int(float(amount)):,d}"
    else:
        # 处理无效或空数据（例如，返回0或其他占位符）
        return "0"

# 2025年6月，北京. 幸运数字8，单合同金额1万以上和以下幸运奖励不同；节节高三档；合同累计考虑工单合同金额5万封顶
def notify_awards_jun_beijing(performance_data_filename, status_filename):
    """通知奖励并更新性能数据文件，同时跟踪发送状态"""
    records = get_all_records_from_csv(performance_data_filename)
    send_status = load_send_status(status_filename)
    updated = False

    awards_mapping = {
        '接好运': '36',
        '接好运万元以上': '66',
        '达标奖': '200',
        '优秀奖': '400',
        '精英奖': '600'
    }

    for record in records:
        contract_id = record['合同ID(_id)']

        processed_accumulated_amount = preprocess_amount(record["管家累计金额"])
        processed_enter_performance_amount = preprocess_amount(record["计入业绩金额"])
        service_housekeeper = record["管家(serviceHousekeeper)"]

        # 添加是否启用徽章管理的判断，如果启用则在管家名称前添加对应的徽章
        if ENABLE_BADGE_MANAGEMENT:
            if service_housekeeper in ELITE_HOUSEKEEPER:
                service_housekeeper = f'{ELITE_BADGE_NAME}{service_housekeeper}'
            elif service_housekeeper in RISING_STAR_HOUSEKEEPER:
                service_housekeeper = f'{RISING_STAR_BADGE_NAME}{service_housekeeper}'

        if record['是否发送通知'] == 'N' and send_status.get(contract_id) != '发送成功':
            next_msg = '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩 \U0001F389\U0001F389\U0001F389' if '无' in record["备注"] else f'{record["备注"]}'
            msg = f'''\U0001F9E8\U0001F9E8\U0001F9E8 签约喜报 \U0001F9E8\U0001F9E8\U0001F9E8
恭喜 {service_housekeeper} 签约合同 {record["合同编号(contractdocNum)"]} 并完成线上收款\U0001F389\U0001F389\U0001F389

\U0001F33B 本单为活动期间平台累计签约第 {record["活动期内第几个合同"]} 单，个人累计签约第 {record["管家累计单数"]} 单。

\U0001F33B {record["管家(serviceHousekeeper)"]}累计签约 {processed_accumulated_amount} 元{f', 累计计入业绩 {processed_enter_performance_amount} 元' if ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB else ''}

\U0001F44A {next_msg}。
'''
            create_task('send_wecom_message', WECOM_GROUP_NAME_BJ_MAY, msg)
            time.sleep(3)

            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "BJ")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_BJ_MAY, jiangli_msg)

            update_send_status(status_filename, contract_id, '发送成功')

            record['是否发送通知'] = 'Y'
            updated = True
            logging.info(f"Notification sent for contract INFO: {record['管家(serviceHousekeeper)']}, {record['合同ID(_id)']}")

    if updated:
        write_performance_data_to_csv(performance_data_filename, records, list(records[0].keys()))
        logging.info("PerformanceData.csv updated with notification status.")

# 2025年5月，北京. 幸运数字6，单合同金额1万以上和以下幸运奖励不同；节节高三档；合同累计考虑工单合同金额10万封顶
def notify_awards_may_beijing(performance_data_filename, status_filename):
    """通知奖励并更新性能数据文件，同时跟踪发送状态"""
    records = get_all_records_from_csv(performance_data_filename)
    send_status = load_send_status(status_filename)
    updated = False

    awards_mapping = {
        '接好运': '28',
        '接好运万元以上': '58',
        '达标奖': '200',
        '优秀奖': '400',
        '精英奖': '600'
    }

    for record in records:
        contract_id = record['合同ID(_id)']

        processed_accumulated_amount = preprocess_amount(record["管家累计金额"])
        processed_enter_performance_amount = preprocess_amount(record["计入业绩金额"])
        service_housekeeper = record["管家(serviceHousekeeper)"]

        # 添加是否启用徽章管理的判断，如果启用则在北京的精英管家名称前添加徽章名称
        if ENABLE_BADGE_MANAGEMENT and service_housekeeper in ELITE_HOUSEKEEPER:
            service_housekeeper = f'{ELITE_BADGE_NAME}{service_housekeeper}'

        if record['是否发送通知'] == 'N' and send_status.get(contract_id) != '发送成功':
            next_msg = '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩 \U0001F389\U0001F389\U0001F389' if '无' in record["备注"] else f'{record["备注"]}'
            msg = f'''\U0001F9E8\U0001F9E8\U0001F9E8 签约喜报 \U0001F9E8\U0001F9E8\U0001F9E8
恭喜 {service_housekeeper} 签约合同 {record["合同编号(contractdocNum)"]} 并完成线上收款\U0001F389\U0001F389\U0001F389

\U0001F33B 本单为活动期间平台累计签约第 {record["活动期内第几个合同"]} 单，个人累计签约第 {record["管家累计单数"]} 单。

\U0001F33B {record["管家(serviceHousekeeper)"]}累计签约 {processed_accumulated_amount} 元{f', 累计计入业绩 {processed_enter_performance_amount} 元' if ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB else ''}

\U0001F44A {next_msg}。
'''
            create_task('send_wecom_message', WECOM_GROUP_NAME_BJ_MAY, msg)
            time.sleep(3)

            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "BJ")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_BJ_MAY, jiangli_msg)

            update_send_status(status_filename, contract_id, '发送成功')

            record['是否发送通知'] = 'Y'
            updated = True
            logging.info(f"Notification sent for contract INFO: {record['管家(serviceHousekeeper)']}, {record['合同ID(_id)']}")

    if updated:
        write_performance_data_to_csv(performance_data_filename, records, list(records[0].keys()))
        logging.info("PerformanceData.csv updated with notification status.")

def notify_awards_shanghai_generate_message_march(performance_data_filename, status_filename,contract_data):
    """通知奖励并更新性能数据文件，同时跟踪发送状态"""
    records = get_all_records_from_csv(performance_data_filename)
    send_status = load_send_status(status_filename)
    updated = False

    awards_mapping = {
        '接好运': '36',
        '接好运万元以上': '66',
        '基础奖': '200',
        '达标奖': '300',
        '优秀奖': '400',
        '精英奖': '800',
        # '卓越奖': '1200',
    }

    for record in records:
        contract_id = record['合同ID(_id)']

        processed_accumulated_amount = preprocess_amount(record["管家累计金额"])

        processed_conversion_rate = preprocess_rate(record["转化率(conversion)"])

        if record['是否发送通知'] == 'N' and send_status.get(contract_id) != '发送成功':
            next_msg = '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩 \U0001F389\U0001F389\U0001F389' if '无' in record["备注"] else f'{record["备注"]}'
            msg = f'''\U0001F9E8\U0001F9E8\U0001F9E8 签约喜报 \U0001F9E8\U0001F9E8\U0001F9E8

恭喜 {record["管家(serviceHousekeeper)"]} 签约合同 {record["合同编号(contractdocNum)"]} 并完成线上收款\U0001F389\U0001F389\U0001F389

\U0001F33B 本单为本月平台累计签约第 {record["活动期内第几个合同"]} 单，

\U0001F33B 个人累计签约第 {record["管家累计单数"]} 单，

\U0001F33B 个人累计签约 {processed_accumulated_amount} 元，

\U0001F33B 个人转化率 {processed_conversion_rate}，

\U0001F44A {next_msg}。
'''
            create_task('send_wecom_message', WECOM_GROUP_NAME_SH_MAY, msg)

            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "SH")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_SH_MAY, jiangli_msg)

            update_send_status(status_filename, contract_id, '发送成功')
            time.sleep(2)

            record['是否发送通知'] = 'Y'
            updated = True
            logging.info(f"Notification sent for contract INFO: {record['管家(serviceHousekeeper)']}, {record['合同ID(_id)']}")

    if updated:
        write_performance_data_to_csv(performance_data_filename, records, list(records[0].keys()))
        logging.info("PerformanceData.csv updated with notification status.")
def notify_technician_status_changes(status_changes, status_filename):
    """
    通知技师的状态变更信息，并更新状态记录文件。

    :param status_changes: 状态变更数组
    :param status_filename: 状态记录文件的路径
    """
    # 加载状态记录文件
    send_status = load_send_status(status_filename)

    for change in status_changes:
        change_id = change[0]
        change_time = change[1]
        technician_name = change[2]
        company_name = change[3]
        update_content = change[5]

        parsed_time = datetime.strptime(change_time, "%Y-%m-%dT%H:%M:%S.%f%z")
        simplified_time = parsed_time.strftime("%Y-%m-%d %H:%M")

        online_icon = "🟢"
        offline_icon = "🔴"

        status = update_content[0] if update_content else ""

        # 根据提取的状态决定使用哪个 Emoji
        if status == "上线":
            status_icon = online_icon
        elif status == "下线":
            status_icon = offline_icon
        else:
            status_icon = ""  # 如果状态不是上线或下线，不使用图标

        # message = f"技师状态变更：\n技师姓名：{technician_name}\n公司名称：{company_name}\n更新时间：{change_time}\n更新内容：{update_content}"
        message = f"您好，公司的管家：{technician_name}，在{simplified_time} {status_icon} {update_content} 了。"

        if change_id not in send_status:

            create_task('send_wechat_message', company_name, message)
            # send_wechat_message('文件传输助手', message)

            post_text_to_webhook(message)

            update_send_status(status_filename, change_id, '通知成功')

            logging.info(f"Notification sent for technician status change: {change_id}")


def notify_daily_service_report(report_data, status_filename):
    """通知日报并跟踪发送状态"""
    logging.info("开始通知日报服务")
    send_status = load_send_status(status_filename)  # 加载发送状态
    logging.info("状态加载完成")

    # 根据 orgName 分组
    grouped_data = {}
    for record in report_data:
        org_name = record['orgName']  # 使用字典的键来获取 orgName
        if org_name not in grouped_data:
            grouped_data[org_name] = []
        grouped_data[org_name].append(record)

    logging.info(f"分组完成，共有 {len(grouped_data)} 个组织")

    # 记录已发送通知的服务商
    notified_service_providers = set()

    # 遍历每个组织，构建并发送消息
    for org_name, records in grouped_data.items():
        logging.info(f"处理组织: {org_name}, 记录数: {len(records)}")

        # 获取接收人名称，如果服务商名称不在SERVICE_PROVIDER_MAPPING中，则使用sunye
        receiver_name = SERVICE_PROVIDER_MAPPING.get(org_name, "sunye")
        if receiver_name == "sunye":
            logging.error(f"No mapping found for org_name: {org_name}")

        # 构建消息内容
        msg_lines = []
        for record in records:
            try:
                # 解析建单时间并格式化
                create_time = datetime.fromisoformat(record['saCreateTime'].replace("Z", ""))  # 处理时区
                # formatted_time = create_time.strftime("%Y年%m月%d日 %H:%M")  # 格式化为 YYYY年MM月DD日 HH:MM

                # 使用 str.format() 构建消息行
                msg_line = '工单编号：{}\n建单时间：{}\n管家：{}\n违规类型：{}\n违规描述：{}\n'.format(
                    record['orderNum'],
                    create_time,
                    record['supervisorName'],
                    record['msg'],
                    record['memo']
                )
                msg_lines.append(msg_line)  # 直接添加字符串
            except Exception as e:
                logging.error(f"Error processing record {record}: {e}")

        logging.info(f"构建消息行完成，当前消息行数: {len(msg_lines)}")

        # 将所有消息行合并为一个完整的消息
        try:
            msg = f'\U0001F4E2 超时情况通报\n\n' + '\n'.join(msg_lines) + '\n说明：以上数据为服务商昨日工单超时统计，如有异议请于下周一十二点前联系运营人员王金申诉。'
            logging.info(f"消息构建完成，消息内容长度: {len(msg)}")
        except Exception as e:
            logging.error(f"Error constructing message for {org_name}: {e}")
            continue  # Skip this organization if message construction fails

        # 检查是否已发送通知
        if records[0]['_id'] not in send_status:  # 使用第一个记录的_id进行检查
            try:
                create_task('send_wecom_message', receiver_name, msg)  # 使用接收人名称发送消息
                update_send_status(status_filename, records[0]['_id'], '通知成功')  # 使用第一个记录的_id更新状态
                notified_service_providers.add(org_name)  # 记录已发送通知的服务商
                logging.info(f"Notification sent for orders to {org_name}")
            except Exception as e:
                logging.error(f"Error sending message to {receiver_name}: {e}")

    # 遍历 SERVICE_PROVIDER_MAPPING，发送默认消息给未发送通知的服务商
    for org_name in SERVICE_PROVIDER_MAPPING.keys():
        if org_name not in notified_service_providers:
            default_msg = "昨日无超时工单，请继续保持。👍"
            receiver_name = SERVICE_PROVIDER_MAPPING[org_name]
            try:
                create_task('send_wecom_message', receiver_name, default_msg)  # 发送默认消息
                logging.info(f"Default message sent to {receiver_name} for {org_name}")
            except Exception as e:
                logging.error(f"Error sending default message to {receiver_name}: {e}")

    logging.info("日报通知服务结束")

def notify_contact_timeout_changes(contact_timeout_data):
    """
    通知工单联络超时的信息。

    :param contact_timeout_data: 工单联络超时数据
    """
    messages = []
    message_count = 1  # 初始化消息计数器

    for data in contact_timeout_data:
        order_number = data[0]
        housekeeper = data[2]
        assign_time = data[3]

        # 解析分单时间
        parsed_time = datetime.strptime(assign_time, "%Y-%m-%dT%H:%M:%S%z")
        # 将分单时间转换为本地时间
        local_assign_time = parsed_time.astimezone()

        # 计算时间差
        time_difference = datetime.now(timezone.utc) - local_assign_time
        days = time_difference.days
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # 构建消息
        simplified_time = parsed_time.strftime("%Y-%m-%d %H:%M")
        time_difference_str = f"{days}天 {hours}小时 {minutes}分钟"
        message_number = f"{message_count:02d}"  # 格式化编号，始终为两位数
        message = f"{message_number}. 工单编号：{order_number}，管家：{housekeeper}，分单时间：{simplified_time}，已超时：{time_difference_str}"
        messages.append(message)
        message_count += 1  # 消息计数器增加

    if messages:
        full_message = "\n".join(messages)
        # print(full_message)  # 打印完整的消息

        post_text_to_webhook(full_message, WEBHOOK_URL_CONTACT_TIMEOUT)
def notify_contact_timeout_changes_markdown(contact_timeout_data):
    """
    通知工单联络超时的信息。

    :param contact_timeout_data: 工单联络超时数据
    """
    messages = []
    message_count = 0  # 初始化消息计数器
    days_colors = ["info", "comment", "warning"]  # 每天的超时信息对应的颜色

    # 构建消息标题
    total_messages = len(contact_timeout_data)
    title = f"联系超时汇总（上周）共计 {total_messages} 条"
    title_message = f"# {title}"
    messages.append(title_message)

    for data in contact_timeout_data:
        message_count += 1
        order_number = data[0]
        housekeeper = data[2]
        assign_time = data[3]

        # 解析分单时间
        parsed_time = datetime.strptime(assign_time, "%Y-%m-%dT%H:%M:%S%z")
        # 将分单时间转换为本地时间
        local_assign_time = parsed_time.astimezone()

        # 计算时间差
        time_difference = datetime.now(timezone.utc) - local_assign_time
        days = time_difference.days
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # 构建消息
        simplified_time = parsed_time.strftime("%Y-%m-%d %H:%M")
        time_difference_str = f"{days}天 {hours}小时 {minutes}分钟"
        message_number = f"{message_count:02d}"  # 格式化编号，始终为两位数

        # 选择颜色
        color_index = days % len(days_colors)
        color = days_colors[color_index]

        # 消息内容
        message = f"{message_number}. 工单编号：{order_number}，管家：{housekeeper}，分单时间：{simplified_time}，已超时：{time_difference_str}"
        message = f"<font color=\"{color}\">{message}</font>"
        messages.append(message)

    if messages:
        full_message = "\n".join(messages)
        # print(full_message)  # 打印完整的消息

        post_markdown_to_webhook(full_message, WEBHOOK_URL_CONTACT_TIMEOUT)

def post_text_to_webhook(message, webhook_url=WEBHOOK_URL_DEFAULT):  # WEBHOOK_URL_DEFAULT 是默认的 Webhook URL
    post_data = {
        'msgtype': "text",
        'text': {
            'content': message,
            # 'mentioned_mobile_list': [PHONE_NUMBER],
        },
    }

    try:
        # 发送POST请求
        response = requests.post(webhook_url, json=post_data)
        response.raise_for_status() # 如果响应状态码不是200，则引发异常
        logging.info(f"sendToWebhook: Response status: {response.status_code}")
        # logging.info(f"sendToWebhook: Response headers: {response.headers}")
        # logging.info(f"sendToWebhook: Response data: {response.json()}")
    except requests.exceptions.RequestException as e:
        logging.error(f"sendToWebhook: 发送到Webhook时发生错误: {e}")

def post_markdown_to_webhook(message, webhook_url):
    """
    发送Markdown格式的消息到企业微信的Webhook（旧版markdown格式，保留兼容性）。

    :param message: 要发送的Markdown格式的消息
    :param webhook_url: Webhook的URL
    """
    post_data = {
        'msgtype': 'markdown',
        'markdown': {
            'content': message
        }
    }

    try:
        # 发送POST请求
        response = requests.post(webhook_url, json=post_data)
        response.raise_for_status()  # 如果响应状态码不是200，则引发异常
        logging.info(f"PostMarkdownToWebhook: Response status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"PostMarkdownToWebhook: 发送到Webhook时发生错误: {e}")

def post_markdown_v2_to_webhook(message, webhook_url):
    """
    发送Markdown_v2格式的消息到企业微信的Webhook（支持表格等高级格式）。

    :param message: 要发送的Markdown_v2格式的消息
    :param webhook_url: Webhook的URL
    """
    post_data = {
        'msgtype': 'markdown_v2',
        'markdown_v2': {
            'content': message
        }
    }

    try:
        # 发送POST请求
        response = requests.post(webhook_url, json=post_data)
        response.raise_for_status()  # 如果响应状态码不是200，则引发异常
        logging.info(f"PostMarkdownV2ToWebhook: Response status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"PostMarkdownV2ToWebhook: 发送到Webhook时发生错误: {e}")

def notify_contact_timeout_changes_template_card(contact_timeout_data):
    """
    通知工单联络超时的信息，使用企业微信的template_card格式。

    :param contact_timeout_data: 工单联络超时数据
    """
    message_count = 0  # 初始化消息计数器
    horizontal_content_list = []

    # 构建消息标题
    total_messages = len(contact_timeout_data)
    title = "联系超时汇总（上周）共计 {} 条".format(total_messages)

    for data in contact_timeout_data[:6]:  # 只处理前6条数据
        message_count += 1
        order_number = data[0][-6:]  # 仅保留工单编号的后6位
        housekeeper = data[2]
        assign_time = data[3]

        # 解析分单时间
        parsed_time = datetime.strptime(assign_time, "%Y-%m-%dT%H:%M:%S%z")
        # 将分单时间转换为本地时间
        local_assign_time = parsed_time.astimezone()

        # 计算时间差
        time_difference = datetime.now(timezone.utc) - local_assign_time
        days = time_difference.days
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # 构建消息
        simplified_time = parsed_time.strftime("%Y-%m-%d %H")
        time_difference_str = "{}天 {}小时".format(days, hours)
        message_number = "{:02d}".format(message_count)  # 格式化编号，始终为两位数

        # 消息内容
        horizontal_content_list.append({
            "keyname": "{}. 单号".format(message_number),
            "value": "{}，{}，{}，超：{}".format(order_number, housekeeper, simplified_time, time_difference_str)
        })

    if horizontal_content_list:
        post_template_card_to_webhook(title, total_messages, horizontal_content_list, WEBHOOK_URL_CONTACT_TIMEOUT)

def post_template_card_to_webhook(title, total_messages, horizontal_content_list, webhook_url):
    """
    发送template_card格式的消息到企业微信的Webhook。

    :param title: 消息标题
    :param total_messages: 总消息数
    :param horizontal_content_list: 二级标题+文本列表
    :param webhook_url: Webhook的URL
    """
    post_data = {
        "msgtype": "template_card",
        "template_card": {
            "card_type": "text_notice",
            "source": {
                "icon_url": "http://metabase.fsgo365.cn:3000/app/assets/img/favicon.ico",
                "desc": "修链Metabase",
                "desc_color": 0
            },
            "main_title": {
                "title": "联系超时汇总（上周）报告",
                "desc": "超时时间的规则为1小时以内，晚上10点后的工单，第二天上午8点前需要联系..."
            },
            "emphasis_content": {
                "title": "{}".format(total_messages),
                "desc": "联系超时汇总（上周）共计"
            },
            "horizontal_content_list": horizontal_content_list,
            "jump_list": [
                {
                    "type": 1,
                    "url": "http://metabase.fsgo365.cn:3000/question/980",
                    "title": "超时工单列表"
                }
            ],
            "card_action": {
                "type": 1,
                "url": "http://metabase.fsgo365.cn:3000/question/980"
            }
        }
    }

    try:
        # 发送POST请求
        response = requests.post(webhook_url, json=post_data)
        response.raise_for_status()  # 如果响应状态码不是200，则引发异常
        logging.info(f"PostTemplateCardToWebhook: Response status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"PostTemplateCardToWebhook: 发送到Webhook时发生错误: {e}")
