# data_utils.py - 数据处理工具模块
import csv
import logging
import pandas as pd
import os
import shutil
import json
from datetime import datetime, timezone
import pandas as pd
import pytz
import re
from modules.log_config import setup_logging

# 设置日志
setup_logging()

def save_to_csv_with_headers(data, filename='ContractData.csv', columns=None):
    if columns is None:
        columns = ["合同ID(_id)", "活动城市(province)", "工单编号(serviceAppointmentNum)", "Status", "管家(serviceHousekeeper)", "合同编号(contractdocNum)", "合同金额(adjustRefundMoney)", "支付金额(paidAmount)", "差额(difference)", "State", "创建时间(createTime)", "服务商(orgName)", "签约时间(signedDate)", "Doorsill", "款项来源类型(tradeIn)"]
    
    df = pd.DataFrame(data, columns=columns)   
    df.to_csv(filename, index=False)

def archive_file(filename, archive_dir='archive', days_to_keep=1):
    # Get current timestamp in China timezone
    china_tz = pytz.timezone('Asia/Shanghai')
    timestamp = datetime.now(china_tz).strftime('%Y%m%d%H%M')

    # Define archive file name
    base_name = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    archive_file_name = f'{base_name}_{timestamp}{ext}'

    # Create archive directory if it doesn't exist
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    # If the filename includes a path, ensure the directory structure exists in the archive
    dir_path = os.path.dirname(filename)
    if dir_path:
        archive_subdir = os.path.join(archive_dir, dir_path)
        if not os.path.exists(archive_subdir):
            os.makedirs(archive_subdir)

    # Move file to archive directory
    shutil.move(filename, os.path.join(archive_dir, archive_file_name))
    
    # Check and delete files in the archive directory that are older than the specified number of days
    for root, _, files in os.walk(archive_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if (datetime.now() - file_modified_time).days > days_to_keep:
                    os.remove(file_path)
                    logging.debug(f"Deleted old file: {file_path}")
                    
def read_contract_data(filename):
    with open(filename, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        return list(reader)
    
def read_daily_service_report(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return list(reader)

def get_all_records_from_csv(filename):
    """读取性能数据文件并返回记录列表"""
    with open(filename, mode='r', encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        return list(reader)
    
def collect_unique_contract_ids_from_file(filename):
    try:
        existing_contract_ids = set()
        with open(filename, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_contract_ids.add(row['合同ID(_id)'].strip())
        return existing_contract_ids
    except FileNotFoundError:
        return set()
    

def write_performance_data(filename, data, headers):
    with open(filename, 'a', newline='', encoding='utf-8-sig') as file:  # 注意这里改为追加模式 'a'
        writer = csv.DictWriter(file, fieldnames=headers)
        if file.tell() == 0:  # 如果文件是空的，写入头部
            writer.writeheader()
        writer.writerows(data)
        
def write_performance_data_to_csv(filename, data, fieldnames):
    """写入性能数据到文件"""
    with open(filename, mode='w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
def get_housekeeper_award_list(file_path):

    try:
        # Load the CSV file
        data = pd.read_csv(file_path)
        
        # Group by '管家(serviceHousekeeper)' and aggregate '奖励名称' into a list
        grouped_rewards = data.groupby('管家(serviceHousekeeper)')['奖励名称'].apply(list).to_dict()
        
        # Clean: Remove NaN values, duplicates, and split combined rewards
        cleaned_grouped_rewards = {}
        for housekeeper, rewards in grouped_rewards.items():
            cleaned_rewards = []
            for reward in filter(pd.notna, rewards):
                # Split combined rewards and extend the list
                cleaned_rewards.extend(reward.split(", "))
            # Remove duplicates
            cleaned_grouped_rewards[housekeeper] = list(dict.fromkeys(cleaned_rewards))
        
        return cleaned_grouped_rewards
    except FileNotFoundError:
        return []

# 重写，获取唯一的管家奖励列表
def get_unique_housekeeper_award_list(file_path):

    try:
        # Load the CSV file
        data = pd.read_csv(file_path)

        if data.empty:
            return {}  # 处理空 DataFrame 的情况
        
        # Construct a new column that combines '管家(serviceHousekeeper)' and '服务商(orgName)'
        data['unique_key'] = data.apply(lambda row: f"{row['管家(serviceHousekeeper)']}_{row['服务商(orgName)']}", axis=1)
        
        # Group by the constructed key and aggregate '奖励名称' into a list
        grouped_rewards = data.groupby('unique_key')['奖励名称'].apply(list).to_dict()

        # Clean: Remove NaN values, duplicates, and split combined rewards
        cleaned_grouped_rewards = {}
        for housekeeper, rewards in grouped_rewards.items():
            cleaned_rewards = []
            for reward in filter(pd.notna, rewards):
                # Split combined rewards and extend the list
                cleaned_rewards.extend(reward.split(", "))
            # Remove duplicates
            cleaned_grouped_rewards[housekeeper] = list(dict.fromkeys(cleaned_rewards))
        
        return cleaned_grouped_rewards
    except FileNotFoundError:
        return {}
    except pd.errors.EmptyDataError:
        return {}  # 处理空文件的情况
    
def load_send_status(filename):
    """加载发送状态文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}  # 处理空文件
            return json.loads(content)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}  # 处理无效JSON文件

def save_send_status(filename, status):
    """保存发送状态到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=4)

def update_send_status(filename, _id, status):
    """更新指定合同ID的发送状态"""
    logging.info(f"Starting update_send_status for _id: {_id}, status: {status}")

    send_status = load_send_status(filename)
    send_status[_id] = status

    logging.info(f"Updating send_status for _id: {_id} to status: {status}")

    save_send_status(filename, send_status)
    logging.info(f"Successfully updated send_status for _id: {_id} to status: {status}")


# ==================== 时间处理相关函数 ====================

def format_create_time(iso_time_str):
    """将ISO时间格式转换为易读格式"""
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

def format_simple_date(create_time_str):
    """格式化创建时间为简单的月-日格式"""
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


# ==================== 数据处理相关函数 ====================

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

def simplify_order_number(order_num):
    """简化工单号，只保留后5位数字"""
    if not order_num:
        return "-"

    # 提取数字部分
    numbers = re.findall(r'\d+', order_num)
    if numbers:
        # 取最后一个数字串的后5位
        last_number = numbers[-1]
        if len(last_number) >= 5:
            return last_number[-5:]
        else:
            return last_number
    return order_num


# ==================== 消息格式化相关函数 ====================

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