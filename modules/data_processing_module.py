# data_processing_module.py
import logging
from modules.log_config import setup_logging
from datetime import date
from modules.config import (
    PERFORMANCE_AMOUNT_CAP,
    ENABLE_PERFORMANCE_AMOUNT_CAP,
    BONUS_POOL_RATIO,  # Import the configurable bonus pool ratio
)
from modules import config  # Add config import to use config.x consistently

# 设置日志
setup_logging()

def determine_lucky_number_reward(
    contract_number: int,
    current_contract_amount: float,
    lucky_number: str
) -> tuple:
    """
    Determine lucky number reward based on contract number and amount.

    Args:
        contract_number: The contract number to check
        current_contract_amount: The current contract amount
        lucky_number: The lucky number to check against (e.g., "8" or "6")

    Returns:
        tuple: (reward_type, reward_name)
    """
    reward_type = ""
    reward_name = ""

    if lucky_number in str(contract_number % 10):
        reward_type = "幸运数字"
        if current_contract_amount >= 10000:
            reward_name = "接好运万元以上"
        else:
            reward_name = "接好运"

    return reward_type, reward_name

def determine_rewards_generic(
    contract_number,
    housekeeper_data,
    current_contract_amount,
    config_key
):
    """
    通用奖励确定函数，基于配置确定奖励类型和名称。

    Args:
        contract_number: 合同编号
        housekeeper_data: 管家数据，包含count、total_amount和awarded等信息
        current_contract_amount: 当前合同金额
        config_key: 配置键名，用于从REWARD_CONFIGS中获取对应配置

    Returns:
        tuple: (reward_types_str, reward_names_str, next_reward_gap)
    """
    # 输入验证
    if contract_number < 0:
        raise ValueError("合同编号不能为负数")
    if housekeeper_data.get('count', 0) < 0:
        raise ValueError("管家合同数量不能为负数")
    if current_contract_amount < 0:
        raise ValueError("合同金额不能为负数")

    # 获取配置
    if config_key not in config.REWARD_CONFIGS:
        logging.error(f"配置键 {config_key} 不存在于REWARD_CONFIGS中")
        return "", "", ""

    # 其他配置的通用实现
    reward_config = config.REWARD_CONFIGS[config_key]
    reward_types = []
    reward_names = []
    next_reward_gap = ""  # 下一级奖励所需金额差

    # 幸运数字奖励逻辑
    lucky_number = reward_config.get("lucky_number", "")
    if lucky_number:
        lucky_rewards = reward_config.get("lucky_rewards", {})

        # 检查幸运数字
        if lucky_number in str(contract_number % 10):
            reward_types.append("幸运数字")

            # 根据合同金额确定奖励名称
            high_threshold = lucky_rewards.get("high", {}).get("threshold", 10000)
            if current_contract_amount >= high_threshold:
                reward_name = lucky_rewards.get("high", {}).get("name", "接好运万元以上")
                reward_names.append(reward_name)
            else:
                reward_name = lucky_rewards.get("base", {}).get("name", "接好运")
                reward_names.append(reward_name)
    # 节节高奖励逻辑
    tiered_rewards = reward_config.get("tiered_rewards", {})
    min_contracts = tiered_rewards.get("min_contracts", 6)
    tiers = tiered_rewards.get("tiers", [])

    # 记录所有奖励名称，用于后续检查
    all_tier_names = [tier["name"] for tier in tiers]

    # 检查是否启用业绩上限
    performance_limits = reward_config.get("performance_limits", {})
    enable_cap = performance_limits.get("enable_cap", False)

    # 确定使用哪个金额字段
    if enable_cap and 'performance_amount' in housekeeper_data:
        amount = housekeeper_data['performance_amount']
    else:
        amount = housekeeper_data['total_amount']

    # 如果管家合同数量达到要求
    if housekeeper_data['count'] >= min_contracts:
        next_reward = None

        # 按照阈值从高到低排序奖励等级
        sorted_tiers = sorted(tiers, key=lambda x: x["threshold"], reverse=True)

        # 第一阶段：检查是否达到奖励条件，并添加奖励
        for i, tier in enumerate(sorted_tiers):
            tier_name = tier["name"]
            tier_threshold = tier["threshold"]

            if amount >= tier_threshold and tier_name not in housekeeper_data['awarded']:
                reward_types.append("节节高")
                reward_names.append(tier_name)
                housekeeper_data['awarded'].append(tier_name)

                # 如果不是最高级别的奖励，设置下一个奖励
                if i > 0:
                    next_reward = sorted_tiers[i-1]["name"]
                break

        # 如果未达到任何奖励阈值，设置下一个奖励为最低等级
        if not set(all_tier_names).intersection(housekeeper_data['awarded']):
            next_reward = sorted_tiers[-1]["name"]

        # 第二阶段：自动发放所有低级别奖项（如果之前未获得）
        for tier in sorted(tiers, key=lambda x: x["threshold"]):
            tier_name = tier["name"]
            tier_threshold = tier["threshold"]

            if tier_name not in housekeeper_data['awarded'] and amount >= tier_threshold:
                reward_types.append("节节高")
                reward_names.append(tier_name)
                housekeeper_data['awarded'].append(tier_name)

        # 第三阶段：确定下一个奖励
        if not next_reward:
            for i in range(len(sorted_tiers) - 1):
                current_tier = sorted_tiers[i+1]
                next_tier = sorted_tiers[i]

                if (current_tier["name"] in housekeeper_data['awarded'] and
                    amount < next_tier["threshold"] and
                    next_tier["name"] not in housekeeper_data['awarded']):
                    next_reward = next_tier["name"]
                    break

        # 计算距离下一级奖励所需的金额差
        if next_reward:
            next_reward_threshold = next(
                (tier["threshold"] for tier in tiers if tier["name"] == next_reward),
                0
            )
            if next_reward_threshold > 0:
                next_reward_gap = f"距离 {next_reward} 还需 {round(next_reward_threshold - amount, 2):,} 元"
    else:
        # 如果未达到最低合同数量要求
        if not set(all_tier_names).intersection(housekeeper_data['awarded']):
            next_reward_gap = f"距离达成节节高奖励条件还需 {min_contracts - housekeeper_data['count']} 单"

    return ', '.join(reward_types), ', '.join(reward_names), next_reward_gap

# 使用通用奖励确定函数的6月北京奖励计算函数
def determine_rewards_jun_beijing_generic(contract_number, housekeeper_data, current_contract_amount):
    return determine_rewards_generic(
        contract_number,
        housekeeper_data,
        current_contract_amount,
        "BJ-2025-06"
    )

# 2025年6月，北京. 幸运数字8，单合同金额1万以上和以下幸运奖励不同；节节高三档；合同金额5万以上按5万计算
def process_data_jun_beijing(contract_data, existing_contract_ids, housekeeper_award_lists):

    logging.info(f"Starting data processing with {len(existing_contract_ids)} existing contract IDs.")

    logging.debug(f"Existing contract IDs: {existing_contract_ids}")

    # 初始化性能数据列表
    performance_data = []
    # 初始化合同计数器，从已存在的合同ID数量开始
    contract_count_in_activity = len(existing_contract_ids) + 1
    # 初始化管家合同数据字典
    housekeeper_contracts = {}

    # 初始化已处理的合同ID集合
    processed_contract_ids = set()

    # 初始化工单编号累计金额字典
    service_appointment_amounts = {}

    # 遍历合同数据
    logging.info("Starting to process contract data...")

    for contract in contract_data:
        # 获取合同ID并转换为字符串
        contract_id = str(contract['合同ID(_id)'])
        # 检查合同ID是否已处理过，如果已经处理过，则跳过当前循环的剩余部分，进入下一次循环
        if contract_id in processed_contract_ids:
            logging.debug(f"Skipping duplicate contract ID: {contract_id}")
            continue

        # 获取管家信息
        housekeeper = contract['管家(serviceHousekeeper)']
        # 如果管家信息不存在，则初始化管家数据
        if housekeeper not in housekeeper_contracts:
            housekeeper_award = []
            if housekeeper in housekeeper_award_lists:
                housekeeper_award = housekeeper_award_lists[housekeeper]
            housekeeper_contracts[housekeeper] = {'count': 0, 'total_amount': 0, 'awarded': housekeeper_award, 'performance_amount': 0}

        # 更新管家合同数量和当前合同的金额
        housekeeper_contracts[housekeeper]['count'] += 1
        current_contract_amount = float(contract['合同金额(adjustRefundMoney)'])

        # 单项目合同金额上限
        performance_amount = min(current_contract_amount, config.PERFORMANCE_AMOUNT_CAP_BJ_FEB)

        # 获取工单编号(serviceAppointmentNum)
        service_appointment_num = contract['工单编号(serviceAppointmentNum)']

        # 初始化工单编号累计金额
        if service_appointment_num not in service_appointment_amounts:
            service_appointment_amounts[service_appointment_num] = 0

        # 获取当前工单编号的累计金额
        current_total_amount = service_appointment_amounts[service_appointment_num]

        # 设置工单金额上限，有一个工单对应多个合同的情况，所以这里的限制是工单金额上限为5万
        max_limit = config.SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB

        # 计算当前同一工单所对应的所有合同应计入的金额
        # 如果当前累计金额未达到上限，则计算当前合同应计入的金额
        # 如果当前累计金额已达到上限，则不计入
        if current_total_amount < max_limit:
            remaining_quota = max_limit - current_total_amount
            amount_to_add = min(current_contract_amount, remaining_quota)
        else:
            amount_to_add = 0

        # 更新工单编号的累计金额
        service_appointment_amounts[service_appointment_num] += current_contract_amount

        # 更新管家合同总金额与计入的金额，保持为浮点数
        housekeeper_contracts[housekeeper]['total_amount'] += amount_to_add  # 保持为浮点数，不转换为整数
        housekeeper_contracts[housekeeper]['performance_amount'] += performance_amount

        # 记录计算过程日志
        logging.debug(f"Housekeeper {housekeeper} count: {housekeeper_contracts[housekeeper]['count']}")
        logging.debug(f"Housekeeper {housekeeper} total amount: {housekeeper_contracts[housekeeper]['total_amount']}")

        # 添加合同ID到已处理集合
        processed_contract_ids.add(contract_id)

        reward_types, reward_names, next_reward_gap = determine_rewards_jun_beijing_generic(contract_count_in_activity, housekeeper_contracts[housekeeper], current_contract_amount)

        if contract_id in existing_contract_ids:
            # 如果合同ID已经存在于已处理的合同ID集合中，则跳过此合同的处理
            logging.debug(f"Skipping existing contract ID: {contract_id}")
            continue

        # Debug log for rewards calculation result
        logging.info(f"Reward types for contract {contract_id}: {reward_types}")
        logging.info(f"Reward names for contract {contract_id}: {reward_names}")

        active_status = 1 if reward_types else 0  # 激活状态基于是否有奖励类型

        # 构建性能数据记录
        performance_entry = {
            '活动编号': 'BJ-2025-06',
            '合同ID(_id)': contract_id,
            '活动城市(province)': contract['活动城市(province)'],
            '工单编号(serviceAppointmentNum)': contract['工单编号(serviceAppointmentNum)'],
            'Status': contract['Status'],
            '管家(serviceHousekeeper)': housekeeper,
            '合同编号(contractdocNum)': contract['合同编号(contractdocNum)'],
            '合同金额(adjustRefundMoney)': contract['合同金额(adjustRefundMoney)'],
            '支付金额(paidAmount)': contract['支付金额(paidAmount)'],
            '差额(difference)': contract['差额(difference)'],
            'State': contract['State'],
            '创建时间(createTime)': contract['创建时间(createTime)'],
            '服务商(orgName)': contract['服务商(orgName)'],
            '签约时间(signedDate)': contract['签约时间(signedDate)'],
            'Doorsill': contract['Doorsill'],
            '款项来源类型(tradeIn)': contract['款项来源类型(tradeIn)'],
            '活动期内第几个合同': contract_count_in_activity,
            '管家累计单数': housekeeper_contracts[housekeeper]['count'],
            '管家累计金额': housekeeper_contracts[housekeeper]['total_amount'] ,
            '计入业绩金额': housekeeper_contracts[housekeeper]['performance_amount'],
            '激活奖励状态': active_status,
            '奖励类型': reward_types,
            '奖励名称': reward_names,
            '是否发送通知': 'N',
            '备注': next_reward_gap if next_reward_gap else '无',  # 添加下一级奖项所需金额差信息
            '登记时间': date.today().strftime("%Y-%m-%d"),  # 新增字段
        }

        # After processing a contract, add its ID to the existing_contract_ids set
        existing_contract_ids.add(contract_id)
        logging.info(f"Added contract ID {contract_id} to existing_contract_ids.")

        logging.info(f"Processing contract ID: {contract_id}, Rewards: {reward_types}")
        # 添加性能数据记录到列表中
        performance_data.append(performance_entry)
        logging.info(f"Added performance entry for contract ID {contract_id}.")

        # 更新合同计数器
        contract_count_in_activity += 1

    # 返回处理后的性能数据列表
    return performance_data

# 4月份的数据处理（当前，仅变化了奖励规则）
def process_data_shanghai_apr(contract_data, existing_contract_ids, housekeeper_award_lists):

    logging.info(f"Starting data processing with {len(existing_contract_ids)} existing contract IDs.")

    logging.debug(f"Existing contract IDs: {existing_contract_ids}")

    performance_data = []
    contract_count_in_activity = len(existing_contract_ids) + 1

    # 用于跟踪每个管家的合同数据
    housekeeper_contracts = {}

    # 用于跟踪已经处理过的合同，也避免有重复的合同，重复的合同不进行重复处理
    processed_contract_ids = set()

    logging.info("Starting to process contract data...")

    for contract in contract_data:
        contract_id = str(contract['合同ID(_id)'])
        if contract_id in processed_contract_ids:
            logging.debug(f"Skipping duplicate contract ID: {contract_id}")
            continue

        housekeeper = contract['管家(serviceHousekeeper)']
        service_provider = contract['服务商(orgName)']
        unique_housekeeper_key = f"{housekeeper}_{service_provider}"

        if unique_housekeeper_key not in housekeeper_contracts:
            housekeeper_award = []
            if unique_housekeeper_key in housekeeper_award_lists:
                housekeeper_award = housekeeper_award_lists[unique_housekeeper_key]

            # 初始化管家的合同相关数据，包括合同数量、总金额、绩效金额、已获得的奖励
            # 这是程序计算中的关键数据结构
            housekeeper_contracts[unique_housekeeper_key] = {
                'count': 0,
                'total_amount': 0,
                'performance_amount': 0,
                'awarded': housekeeper_award
            }

        contract_amount = float(contract['合同金额(adjustRefundMoney)'])
        performance_amount = min(contract_amount, config.PERFORMANCE_AMOUNT_CAP)  # 使用配置的上限值

        housekeeper_contracts[unique_housekeeper_key]['count'] += 1
        housekeeper_contracts[unique_housekeeper_key]['total_amount'] += contract_amount
        housekeeper_contracts[unique_housekeeper_key]['performance_amount'] += performance_amount

        housekeeper_contracts[unique_housekeeper_key]['total_amount'] = int(housekeeper_contracts[unique_housekeeper_key]['total_amount'])
        housekeeper_contracts[unique_housekeeper_key]['performance_amount'] = int(housekeeper_contracts[unique_housekeeper_key]['performance_amount'])

        logging.debug(f"Housekeeper {unique_housekeeper_key} count: {housekeeper_contracts[unique_housekeeper_key]['count']}")
        logging.debug(f"Housekeeper {unique_housekeeper_key} total amount: {housekeeper_contracts[unique_housekeeper_key]['total_amount']}")

        processed_contract_ids.add(contract_id)

        # 根据每月的奖项规则不同，使用当月的奖项规则函数
        reward_types, reward_names, next_reward_gap = determine_rewards_shanghai_apr(contract_count_in_activity, housekeeper_contracts[unique_housekeeper_key], contract_amount)

        if contract_id in existing_contract_ids:
            logging.debug(f"Skipping existing contract ID: {contract_id}")
            continue

        active_status = 1 if reward_types else 0  # 激活状态基于是否有奖励类型

        performance_entry = {
            '活动编号': 'SH-2025-04',
            '合同ID(_id)': contract_id,
            '活动城市(province)': contract['活动城市(province)'],
            '工单编号(serviceAppointmentNum)': contract['工单编号(serviceAppointmentNum)'],
            'Status': contract['Status'],
            '管家(serviceHousekeeper)': housekeeper,
            '合同编号(contractdocNum)': contract['合同编号(contractdocNum)'],
            '合同金额(adjustRefundMoney)': contract['合同金额(adjustRefundMoney)'],
            '支付金额(paidAmount)': contract['支付金额(paidAmount)'],
            '差额(difference)': contract['差额(difference)'],
            'State': contract['State'],
            '创建时间(createTime)': contract['创建时间(createTime)'],
            '服务商(orgName)': contract['服务商(orgName)'],
            '签约时间(signedDate)': contract['签约时间(signedDate)'],
            'Doorsill': contract['Doorsill'],
            '款项来源类型(tradeIn)': contract['款项来源类型(tradeIn)'],
            '转化率(conversion)': contract['转化率(conversion)'], # 新增字段
            '平均客单价(average)': contract['平均客单价(average)'], # 新增字段
            '活动期内第几个合同': contract_count_in_activity,
            '管家累计单数': housekeeper_contracts[unique_housekeeper_key]['count'],
            '管家累计金额': housekeeper_contracts[unique_housekeeper_key]['total_amount'],
            '奖金池': float(contract['合同金额(adjustRefundMoney)']) * config.BONUS_POOL_RATIO, # 可配置的奖金池计算比例
            '计入业绩金额': housekeeper_contracts[unique_housekeeper_key]['performance_amount'],
            '激活奖励状态': active_status,
            '奖励类型': reward_types,
            '奖励名称': reward_names,
            '是否发送通知': 'N',
            '备注': next_reward_gap if next_reward_gap else '无',  # 添加下一级奖项所需金额差信息
            '登记时间': date.today().strftime("%Y-%m-%d"),  # 新增字段
        }

        existing_contract_ids.add(contract_id)
        logging.info(f"Added contract ID {contract_id} to existing_contract_ids.")
        logging.info(f"Processing contract ID: {contract_id}, Rewards: {reward_types}")
        performance_data.append(performance_entry)
        logging.info(f"Added performance entry for contract ID {contract_id}.")

        contract_count_in_activity += 1

    return performance_data

# 4月份的奖励规则
def determine_rewards_shanghai_apr(contract_number, housekeeper_data, contract_amount):
    # 定义节节高奖励的合同数量阈值
    JIEJIEGAO_CONTRACT_COUNT_THRESHOLD = 5

    reward_types = []
    reward_names = []
    next_reward_gap = ""  # 下一级奖励所需金额差

    # 幸运数字6 (仅在6月份活动中判断)
    current_month = date.today().month
    if current_month == 6:
        reward_type, reward_name = determine_lucky_number_reward(contract_number, contract_amount, "6")
        if reward_type:
            reward_types.append(reward_type)
            reward_names.append(reward_name)

    # 节节高奖励逻辑（需要管家合同数量大于等于5）
    if housekeeper_data['count'] >= JIEJIEGAO_CONTRACT_COUNT_THRESHOLD:
        # 计算下一级奖励所需金额差，如果启用了绩效金额，使用绩效金额，否则使用合同金额
        amount = housekeeper_data['performance_amount'] if config.ENABLE_PERFORMANCE_AMOUNT_CAP else housekeeper_data['total_amount']
        next_reward = None
        if amount >= 120000 and '精英奖' not in housekeeper_data['awarded']:
            # 精英奖
            reward_types.append("节节高")
            reward_names.append("精英奖")
            housekeeper_data['awarded'].append('精英奖')
        elif amount >= 80000 and '优秀奖' not in housekeeper_data['awarded']:
            # 优秀奖
            next_reward = "精英奖"
            reward_types.append("节节高")
            reward_names.append("优秀奖")
            housekeeper_data['awarded'].append('优秀奖')
        elif amount >= 60000 and '达标奖' not in housekeeper_data['awarded']:
            # 达标奖
            next_reward = "优秀奖"
            reward_types.append("节节高")
            reward_names.append("达标奖")
            housekeeper_data['awarded'].append('达标奖')
        elif amount >= 40000 and '基础奖' not in housekeeper_data['awarded']:
            # 达标奖
            next_reward = "达标奖"
            reward_types.append("节节高")
            reward_names.append("基础奖")
            housekeeper_data['awarded'].append('基础奖')
        elif not set(["精英奖", "优秀奖", "达标奖", "基础奖"]).intersection(housekeeper_data['awarded']):
            next_reward = "基础奖"  # 如果没有获得任何奖项，则下一个奖项是基础奖

        # 自动发放所有低级别奖项（如果之前未获得）
        if '基础奖' not in housekeeper_data['awarded'] and amount >= 40000:
            reward_types.append("节节高")
            reward_names.append("基础奖")
            housekeeper_data['awarded'].append('基础奖')
        if '达标奖' not in housekeeper_data['awarded'] and amount >= 60000:
            reward_types.append("节节高")
            reward_names.append("达标奖")
            housekeeper_data['awarded'].append('达标奖')
        if '优秀奖' not in housekeeper_data['awarded'] and amount >= 80000:
            reward_types.append("节节高")
            reward_names.append("优秀奖")
            housekeeper_data['awarded'].append('优秀奖')
        if '精英奖' not in housekeeper_data['awarded'] and amount >= 120000:
            reward_types.append("节节高")
            reward_names.append("精英奖")
            housekeeper_data['awarded'].append('精英奖')

        if not next_reward:
            if '优秀奖' in housekeeper_data['awarded'] and  amount < 120000 and  not set(["精英奖"]).intersection(housekeeper_data['awarded']):
                next_reward = "精英奖"
            elif '达标奖' in housekeeper_data['awarded'] and  amount < 80000 and  not set(["精英奖", "优秀奖"]).intersection(housekeeper_data['awarded']):
                next_reward = "优秀奖"
            elif '基础奖' in housekeeper_data['awarded'] and  amount < 60000 and  not set(["精英奖", "优秀奖", "达标奖"]).intersection(housekeeper_data['awarded']):
                next_reward = "达标奖"

        # 计算距离下一级奖励所需的金额差
        if next_reward:
            if next_reward == "基础奖":
                next_reward_gap = f"距离 {next_reward} 还需 {round(40000 - amount, 2):,} 元"
            elif next_reward == "达标奖":
                next_reward_gap = f"距离 {next_reward} 还需 {round(60000 - amount, 2):,} 元"
            elif next_reward == "优秀奖":
                next_reward_gap = f"距离 {next_reward} 还需 {round(80000 - amount, 2):,} 元"
            elif next_reward == "精英奖":
                next_reward_gap = f"距离 {next_reward} 还需 {round(120000 - amount, 2):,} 元"
    else:
        if  not set(["精英奖", "优秀奖", "达标奖"]).intersection(housekeeper_data['awarded']):
            next_reward_gap = f"距离达成节节高奖励条件还需 {JIEJIEGAO_CONTRACT_COUNT_THRESHOLD -  housekeeper_data['count']} 单"

    return ', '.join(reward_types), ', '.join(reward_names), next_reward_gap