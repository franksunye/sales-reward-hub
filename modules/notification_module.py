# notification_module.py
import logging
import time
from modules.log_config import setup_logging
import requests
from modules.config import *
from modules.data_utils import load_send_status, update_send_status, get_all_records_from_csv, update_performance_data
from task_manager import create_task

# 配置日志
setup_logging()
# 使用专门的发送消息日志记录器
send_logger = logging.getLogger('sendLogger')

def get_awards_mapping(config_key):
    """
    从配置中获取奖励金额映射

    Args:
        config_key: 配置键，如 "SH-2025-04", "BJ-2025-08"

    Returns:
        dict: 奖励名称到金额的映射
    """
    if config_key in REWARD_CONFIGS:
        return REWARD_CONFIGS[config_key].get("awards_mapping", {})
    else:
        # 如果配置不存在，返回默认映射（向后兼容）
        return {
            '接好运': '36',
            '接好运万元以上': '66',
            '基础奖': '200',
            '达标奖': '300',
            '优秀奖': '400',
            '精英奖': '800',
            '卓越奖': '1200',
        }

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

    # 获取订单类型，默认为平台单
    order_type = record.get("工单类型", "平台单")
    return f'{service_housekeeper}签约合同（{order_type}）{contract_number}\n\n' + '\n'.join(award_messages)

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

# 通用北京通知函数
def notify_awards_beijing_generic(performance_data_filename, status_filename, config_key, enable_rising_star_badge=False):
    """
    通用的北京奖励通知函数

    Args:
        performance_data_filename: 业绩数据文件名
        status_filename: 状态文件名
        config_key: 配置键，如 "BJ-2025-06", "BJ-2025-05"
        enable_rising_star_badge: 是否启用新星徽章（默认False，只有部分月份启用）
    """
    records = get_all_records_from_csv(performance_data_filename)
    send_status = load_send_status(status_filename)
    updated = False

    # 使用配置化的奖励映射
    awards_mapping = get_awards_mapping(config_key)

    for record in records:
        contract_id = record['合同ID(_id)']

        processed_accumulated_amount = preprocess_amount(record["管家累计金额"])
        processed_enter_performance_amount = preprocess_amount(record["计入业绩金额"])
        service_housekeeper = record["管家(serviceHousekeeper)"]

        # 添加是否启用徽章管理的判断，如果启用则在管家名称前添加对应的徽章
        if ENABLE_BADGE_MANAGEMENT:
            if service_housekeeper in ELITE_HOUSEKEEPER:
                service_housekeeper = f'{ELITE_BADGE_NAME}{service_housekeeper}'
            elif enable_rising_star_badge and service_housekeeper in RISING_STAR_HOUSEKEEPER:
                service_housekeeper = f'{RISING_STAR_BADGE_NAME}{service_housekeeper}'

        if record['是否发送通知'] == 'N' and send_status.get(contract_id) != '发送成功':
            next_msg = '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩 \U0001F389\U0001F389\U0001F389' if '无' in record["备注"] else f'{record["备注"]}'
            msg = f'''\U0001F9E8\U0001F9E8\U0001F9E8 签约喜报 \U0001F9E8\U0001F9E8\U0001F9E8
恭喜 {service_housekeeper} 签约合同 {record["合同编号(contractdocNum)"]} 并完成线上收款\U0001F389\U0001F389\U0001F389

\U0001F33B 本单为活动期间平台累计签约第 {record["活动期内第几个合同"]} 单，个人累计签约第 {record["管家累计单数"]} 单。

\U0001F33B {record["管家(serviceHousekeeper)"]}累计签约 {processed_accumulated_amount} 元{f', 累计计入业绩 {processed_enter_performance_amount} 元' if ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB else ''}

\U0001F44A {next_msg}。
'''
            create_task('send_wecom_message', WECOM_GROUP_NAME_BJ, msg)
            time.sleep(3)

            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "BJ")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_BJ, jiangli_msg)

            update_send_status(status_filename, contract_id, '发送成功')

            record['是否发送通知'] = 'Y'
            updated = True
            logging.info(f"Notification sent for contract INFO: {record['管家(serviceHousekeeper)']}, {record['合同ID(_id)']}")

    if updated:
        update_performance_data(performance_data_filename, records, list(records[0].keys()))
        logging.info("PerformanceData.csv updated with notification status.")

# 包装函数：保持向后兼容
def notify_awards_jun_beijing(performance_data_filename, status_filename):
    """2025年6月北京通知函数（包装函数）"""
    return notify_awards_beijing_generic(
        performance_data_filename,
        status_filename,
        "BJ-2025-06",
        enable_rising_star_badge=True  # 6月份启用新星徽章
    )

def notify_awards_may_beijing(performance_data_filename, status_filename):
    """2025年5月北京通知函数（包装函数）"""
    return notify_awards_beijing_generic(
        performance_data_filename,
        status_filename,
        "BJ-2025-05",
        enable_rising_star_badge=False  # 5月份不启用新星徽章
    )

def notify_awards_shanghai_generate_message_march(performance_data_filename, status_filename,contract_data):
    """通知奖励并更新性能数据文件，同时跟踪发送状态"""
    records = get_all_records_from_csv(performance_data_filename)
    send_status = load_send_status(status_filename)
    updated = False

    # 使用配置化的奖励映射（上海4月配置）
    awards_mapping = get_awards_mapping("SH-2025-04")

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
            create_task('send_wecom_message', WECOM_GROUP_NAME_SH, msg)

            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "SH")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_SH, jiangli_msg)

            update_send_status(status_filename, contract_id, '发送成功')
            time.sleep(2)

            record['是否发送通知'] = 'Y'
            updated = True
            logging.info(f"Notification sent for contract INFO: {record['管家(serviceHousekeeper)']}, {record['合同ID(_id)']}")

    if updated:
        update_performance_data(performance_data_filename, records, list(records[0].keys()))
        logging.info("PerformanceData.csv updated with notification status.")

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


def notify_awards_shanghai_generic(performance_data_filename, status_filename, config_key):
    """
    通用的上海通知任务生成函数，参考北京模式

    Args:
        performance_data_filename: 业绩数据文件名
        status_filename: 状态文件名
        config_key: 配置键，如 "SH-2025-09"
    """
    records = get_all_records_from_csv(performance_data_filename)
    send_status = load_send_status(status_filename)
    awards_mapping = get_awards_mapping(config_key)
    updated = False

    for record in records:
        contract_id = record['合同ID(_id)']
        if record['是否发送通知'] == 'N' and send_status.get(contract_id) != '发送成功':
            # 生成群通知任务（使用现有消息构建方式）
            processed_conversion_rate = preprocess_rate(record["转化率(conversion)"])
            # 根据订单类型决定结尾消息逻辑
            order_type = record.get("工单类型", "平台单")
            if order_type == "自引单":
                # 自引单统一显示固定消息
                next_msg = '继续加油，争取更多奖励'
            else:
                # 平台单按照8月份逻辑处理：根据备注字段动态生成
                next_msg = '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩' if '无' in record["备注"] else f'{record["备注"]}'

            # 新增：显示订单类型和分类统计
            order_type = record.get("工单类型", "平台单")  # 默认为平台单
            platform_count = record.get("平台单累计数量", 0)
            self_referral_count = record.get("自引单累计数量", 0)
            platform_amount = preprocess_amount(record.get("平台单累计金额", "0"))
            self_referral_amount = preprocess_amount(record.get("自引单累计金额", "0"))

            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {record["管家(serviceHousekeeper)"]} 签约合同（{order_type}） {record["合同编号(contractdocNum)"]} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {record["活动期内第几个合同"]} 单，

🌻 个人平台单累计签约第 {platform_count} 单， 自引单累计签约第 {self_referral_count} 单。
🌻 个人平台单金额累计签约 {platform_amount} 元，自引单金额累计签约 {self_referral_amount}元

🌻 个人平台单转化率 {processed_conversion_rate}，

👊 {next_msg} 🎉🎉🎉。
'''
            create_task('send_wecom_message', '（上海）运营群', msg)

            # 生成个人奖励通知任务
            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "SH")
                # 使用配置中的活动管理人
                from modules.config import CAMPAIGN_CONTACT_SH_SEP
                create_task('send_wechat_message', CAMPAIGN_CONTACT_SH_SEP, jiangli_msg)

            # 更新发送状态（保持与现有系统一致）
            update_send_status(status_filename, contract_id, '发送成功')
            record['是否发送通知'] = 'Y'
            updated = True

    if updated:
        update_performance_data(performance_data_filename, records, list(records[0].keys()))


# 包装函数：上海9月
def notify_awards_sep_shanghai(performance_data_filename, status_filename):
    return notify_awards_shanghai_generic(
        performance_data_filename, status_filename, "SH-2025-09"
    )