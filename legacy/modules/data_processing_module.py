# data_processing_module.py
import logging
from modules.log_config import setup_logging
from datetime import date
from modules.config import (
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


def determine_lucky_number_reward_generic(
    contract_number: int,
    current_contract_amount: float,
    housekeeper_contract_count: int,
    config_key: str
) -> tuple:
    """
    通用幸运数字奖励确定函数

    Args:
        contract_number: 合同编号（用于传统模式）
        current_contract_amount: 当前合同金额
        housekeeper_contract_count: 管家个人合同数量（用于个人顺序模式）
        config_key: 配置键

    Returns:
        tuple: (reward_type, reward_name)
    """
    reward_config = config.REWARD_CONFIGS.get(config_key, {})
    lucky_number = reward_config.get("lucky_number", "")
    lucky_mode = reward_config.get("lucky_number_mode", "contract_number")

    if not lucky_number:
        return "", ""

    # 根据模式选择判断逻辑
    if lucky_mode == "personal_sequence":
        # 个人签约顺序模式：判断是否为指定倍数
        target_multiple = int(lucky_number)
        if housekeeper_contract_count % target_multiple == 0:
            return "幸运数字", "接好运"
    else:
        # 传统模式：基于合同编号末位
        if lucky_number in str(contract_number % 10):
            lucky_rewards = reward_config.get("lucky_rewards", {})
            high_threshold = lucky_rewards.get("high", {}).get("threshold", 10000)
            if current_contract_amount >= high_threshold:
                return "幸运数字", lucky_rewards.get("high", {}).get("name", "接好运万元以上")
            else:
                return "幸运数字", lucky_rewards.get("base", {}).get("name", "接好运")

    return "", ""


def should_enable_badge(config_key: str, badge_type: str) -> bool:
    """
    检查是否启用指定徽章

    Args:
        config_key: 配置键
        badge_type: 徽章类型 ("elite" 或 "rising_star")

    Returns:
        bool: 是否启用徽章
    """
    reward_config = config.REWARD_CONFIGS.get(config_key, {})
    badge_config = reward_config.get("badge_config", {})

    if badge_type == "elite":
        return badge_config.get("enable_elite_badge", True)  # 默认启用
    elif badge_type == "rising_star":
        return badge_config.get("enable_rising_star_badge", False)  # 默认禁用

    return False


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

    # 幸运数字奖励逻辑 - 使用通用幸运数字函数
    lucky_reward_type, lucky_reward_name = determine_lucky_number_reward_generic(
        contract_number=contract_number,
        current_contract_amount=current_contract_amount,
        housekeeper_contract_count=housekeeper_data.get('count', 0),
        config_key=config_key
    )

    if lucky_reward_type:
        reward_types.append(lucky_reward_type)
        reward_names.append(lucky_reward_name)
    # 节节高奖励逻辑
    tiered_rewards = reward_config.get("tiered_rewards", {})
    min_contracts = tiered_rewards.get("min_contracts", 6)
    tiers = tiered_rewards.get("tiers", [])

    # 记录所有奖励名称，用于后续检查
    all_tier_names = [tier["name"] for tier in tiers]

    # 确定使用哪个金额字段 - 完全基于配置
    performance_limits = reward_config.get("performance_limits", {})
    enable_cap = performance_limits.get("enable_cap", False)

    if enable_cap:
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

# 使用通用奖励确定函数的9月北京奖励计算函数
def determine_rewards_sep_beijing_generic(contract_number, housekeeper_data, current_contract_amount):
    return determine_rewards_generic(
        contract_number,
        housekeeper_data,
        current_contract_amount,
        "BJ-2025-09"
    )

# 使用通用奖励确定函数的4月上海奖励计算函数
def determine_rewards_apr_shanghai_generic(contract_number, housekeeper_data, current_contract_amount):
    """
    上海4月活动奖励确定函数（通用版本）

    Args:
        contract_number: 合同编号
        housekeeper_data: 管家数据，包含count、total_amount、performance_amount和awarded等信息
        current_contract_amount: 当前合同金额

    Returns:
        tuple: (reward_types_str, reward_names_str, next_reward_gap)
    """
    return determine_rewards_generic(
        contract_number,
        housekeeper_data,
        current_contract_amount,
        "SH-2025-04"
    )

# 使用通用奖励确定函数的9月上海奖励计算函数
def determine_rewards_sep_shanghai_generic(contract_number, housekeeper_data, current_contract_amount):
    """
    上海9月活动奖励确定函数（通用版本）

    Args:
        contract_number: 合同编号
        housekeeper_data: 管家数据，包含count、total_amount、performance_amount和awarded等信息
        current_contract_amount: 当前合同金额

    Returns:
        tuple: (reward_types_str, reward_names_str, next_reward_gap)
    """
    return determine_rewards_generic(
        contract_number,
        housekeeper_data,
        current_contract_amount,
        "SH-2025-09"
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

        # 获取当前工单编号的累计金额（包含历史合同占用）
        if service_appointment_num not in service_appointment_amounts:
            # 初始化时包含历史合同占用
            historical_usage = globals().get('historical_project_usage', {}).get(service_appointment_num, 0)
            service_appointment_amounts[service_appointment_num] = historical_usage

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
        # 修复：使用考虑工单上限的实际业绩金额，而不是仅考虑单合同上限的performance_amount
        actual_performance_amount = min(amount_to_add, performance_amount)
        housekeeper_contracts[housekeeper]['performance_amount'] += actual_performance_amount

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
            '活动编号': 'BJ-JUN',
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
            '转化率(conversion)': contract['转化率(conversion)'],
            '平均客单价(average)': contract['平均客单价(average)'],
            '活动期内第几个合同': contract_count_in_activity,
            '管家累计单数': housekeeper_contracts[housekeeper]['count'],
            '管家累计金额': housekeeper_contracts[housekeeper]['total_amount'] ,
            '奖金池': housekeeper_contracts[housekeeper]['total_amount'],  # 奖金池等于累计金额
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
        # 使用配置中的业绩上限值
        performance_cap = config.REWARD_CONFIGS["SH-2025-04"]["performance_limits"]["single_contract_cap"]
        performance_amount = min(contract_amount, performance_cap)

        housekeeper_contracts[unique_housekeeper_key]['count'] += 1
        housekeeper_contracts[unique_housekeeper_key]['total_amount'] += contract_amount
        housekeeper_contracts[unique_housekeeper_key]['performance_amount'] += performance_amount

        housekeeper_contracts[unique_housekeeper_key]['total_amount'] = int(housekeeper_contracts[unique_housekeeper_key]['total_amount'])
        housekeeper_contracts[unique_housekeeper_key]['performance_amount'] = int(housekeeper_contracts[unique_housekeeper_key]['performance_amount'])

        logging.debug(f"Housekeeper {unique_housekeeper_key} count: {housekeeper_contracts[unique_housekeeper_key]['count']}")
        logging.debug(f"Housekeeper {unique_housekeeper_key} total amount: {housekeeper_contracts[unique_housekeeper_key]['total_amount']}")

        processed_contract_ids.add(contract_id)

        # 根据每月的奖项规则不同，使用当月的奖项规则函数（已替换为通用版本）
        reward_types, reward_names, next_reward_gap = determine_rewards_apr_shanghai_generic(contract_count_in_activity, housekeeper_contracts[unique_housekeeper_key], contract_amount)

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


def get_self_referral_config(config_key):
    """
    获取自引单奖励配置

    Args:
        config_key: 配置键，如 "SH-2025-09"

    Returns:
        dict: 自引单奖励配置
    """
    if config_key in config.REWARD_CONFIGS:
        return config.REWARD_CONFIGS[config_key].get("self_referral_rewards", {})
    else:
        # 默认配置（向后兼容）
        return {
            "enable": False,
            "reward_type": "",
            "reward_name": "",
            "deduplication_field": ""
        }


def determine_self_referral_rewards(project_address, housekeeper_data, config_key):
    """
    自引单奖励计算函数

    Args:
        project_address: 项目地址
        housekeeper_data: 管家数据
        config_key: 配置键，如 "SH-2025-09"

    Returns:
        tuple: (reward_type, reward_name, is_qualified)
        - reward_type: 奖励类型，写入业绩数据文件
        - reward_name: 奖励名称，写入业绩数据文件
        - is_qualified: 是否符合奖励条件
    """
    # 获取自引单配置
    self_referral_config = get_self_referral_config(config_key)

    # 检查是否启用自引单奖励
    if not self_referral_config.get("enable", False):
        return ("", "", False)

    # 获取奖励信息（用于写入业绩数据文件）
    reward_type = self_referral_config.get("reward_type", "自引单")
    reward_name = self_referral_config.get("reward_name", "红包")

    # 检查项目地址是否已存在（去重逻辑）
    if project_address not in housekeeper_data['self_referral_projects']:
        housekeeper_data['self_referral_projects'].add(project_address)
        housekeeper_data['self_referral_rewards'] += 1
        return (reward_type, reward_name, True)
    else:
        return ("", "", False)


def process_data_shanghai_sep(contract_data, existing_contract_ids, housekeeper_award_lists):
    """
    上海9月数据处理函数，支持平台单和自引单双轨处理

    Args:
        contract_data: 合同数据列表
        existing_contract_ids: 已存在的合同ID集合
        housekeeper_award_lists: 管家历史奖励列表

    Returns:
        list: 处理后的业绩数据列表
    """
    logging.info(f"Starting Shanghai Sep data processing with {len(existing_contract_ids)} existing contract IDs.")

    config_key = "SH-2025-09"
    performance_data = []
    contract_count_in_activity = len(existing_contract_ids) + 1
    housekeeper_contracts = {}
    processed_contract_ids = set()

    logging.info("Starting to process contract data...")

    for contract in contract_data:
        contract_id = str(contract['合同ID(_id)'])
        if contract_id in processed_contract_ids:
            logging.debug(f"Skipping duplicate contract ID: {contract_id}")
            continue

        # 字段映射：API字段名 -> CSV字段名
        source_type = int(contract.get('工单类型(sourceType)', 2))  # 默认为平台单
        project_address = contract.get('项目地址(projectAddress)', '')
        housekeeper_id = contract.get('管家ID(serviceHousekeeperId)', '')
        contact_address = contract.get('客户联系地址(contactsAddress)', '')

        housekeeper = contract['管家(serviceHousekeeper)']
        service_provider = contract['服务商(orgName)']
        housekeeper_key = f"{housekeeper}_{service_provider}"

        # 初始化管家数据结构
        if housekeeper_key not in housekeeper_contracts:
            housekeeper_award = []
            if housekeeper_key in housekeeper_award_lists:
                housekeeper_award = housekeeper_award_lists[housekeeper_key]

            housekeeper_contracts[housekeeper_key] = {
                'count': 0, 'total_amount': 0, 'performance_amount': 0, 'awarded': housekeeper_award,
                'platform_count': 0, 'platform_amount': 0,
                'self_referral_count': 0, 'self_referral_amount': 0,
                'self_referral_projects': set(),
                'self_referral_rewards': 0
            }

        contract_amount = float(contract['合同金额(adjustRefundMoney)'])

        # 使用配置中的业绩上限值
        performance_cap = config.REWARD_CONFIGS[config_key]["performance_limits"]["single_contract_cap"]
        performance_amount = min(contract_amount, performance_cap)

        # 先更新管家数据（包括已存在的合同）
        housekeeper_contracts[housekeeper_key]['count'] += 1
        housekeeper_contracts[housekeeper_key]['total_amount'] += contract_amount
        housekeeper_contracts[housekeeper_key]['performance_amount'] += performance_amount

        # 根据订单类型更新分类统计
        if source_type == 1:
            # 自引单统计
            housekeeper_contracts[housekeeper_key]['self_referral_count'] += 1
            housekeeper_contracts[housekeeper_key]['self_referral_amount'] += contract_amount
        else:
            # 平台单统计
            housekeeper_contracts[housekeeper_key]['platform_count'] += 1
            housekeeper_contracts[housekeeper_key]['platform_amount'] += contract_amount

        # 转换为整数（保持与现有逻辑一致）
        housekeeper_contracts[housekeeper_key]['total_amount'] = int(housekeeper_contracts[housekeeper_key]['total_amount'])
        housekeeper_contracts[housekeeper_key]['performance_amount'] = int(housekeeper_contracts[housekeeper_key]['performance_amount'])

        # 根据订单类型应用不同的奖励规则（使用更新后的数据）
        reward_types = ""
        reward_names = ""
        next_reward_gap = ""

        if source_type == 1:
            # 自引单：项目地址去重奖励
            reward_types, reward_names, _ = determine_self_referral_rewards(
                project_address, housekeeper_contracts[housekeeper_key], config_key)
            # 自引单固定备注
            next_reward_gap = "继续加油，争取更多奖励"
        else:
            # 平台单：节节高奖励，使用平台单专用数据
            # 创建只包含平台单数据的临时结构
            platform_only_data = {
                'count': housekeeper_contracts[housekeeper_key]['platform_count'],
                'total_amount': housekeeper_contracts[housekeeper_key]['platform_amount'],
                'performance_amount': housekeeper_contracts[housekeeper_key]['platform_amount'],
                'awarded': housekeeper_contracts[housekeeper_key]['awarded']
            }
            reward_types, reward_names, next_reward_gap = determine_rewards_sep_shanghai_generic(
                contract_count_in_activity, platform_only_data, contract_amount)

        # 检查是否为已存在合同，如果是则跳过记录创建
        if contract_id in existing_contract_ids:
            logging.debug(f"Skipping existing contract ID: {contract_id}")
            continue

        # 只为新合同创建业绩记录
        active_status = 1 if reward_types else 0  # 激活状态基于是否有奖励类型
        order_type_text = "自引单" if source_type == 1 else "平台单"

        performance_entry = create_performance_record_shanghai_sep(
            contract, reward_types, reward_names, housekeeper_contracts[housekeeper_key],
            contract_count_in_activity, active_status, order_type_text,
            housekeeper_id, contact_address, project_address, next_reward_gap
        )

        performance_data.append(performance_entry)
        processed_contract_ids.add(contract_id)
        contract_count_in_activity += 1

        logging.debug(f"Processed contract {contract_id}, type: {order_type_text}")

    logging.info(f"Shanghai Sep data processing completed. Processed {len(performance_data)} contracts.")
    return performance_data


def create_performance_record_shanghai_sep(contract, reward_types, reward_names, housekeeper_data,
                                          contract_count, active_status, order_type_text,
                                          housekeeper_id, contact_address, project_address, next_reward_gap):
    """创建上海9月业绩数据记录，包含新增字段"""
    from datetime import datetime

    return {
        # 原有字段
        '活动编号': 'SH-2025-09',
        '合同ID(_id)': contract['合同ID(_id)'],
        '活动城市(province)': contract['活动城市(province)'],
        '工单编号(serviceAppointmentNum)': contract['工单编号(serviceAppointmentNum)'],
        'Status': contract['Status'],
        '管家(serviceHousekeeper)': contract['管家(serviceHousekeeper)'],
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
        '转化率(conversion)': contract['转化率(conversion)'],
        '平均客单价(average)': contract['平均客单价(average)'],
        '活动期内第几个合同': contract_count,
        '管家累计金额': housekeeper_data['total_amount'],  # 已经包含当前合同
        '管家累计单数': housekeeper_data['count'],  # 已经包含当前合同
        '奖金池': 0,  # 暂时设为0，根据需要调整
        '计入业绩金额': housekeeper_data['performance_amount'],
        '激活奖励状态': active_status,
        '奖励类型': reward_types,
        '奖励名称': reward_names,
        '是否发送通知': 'N',
        '备注': next_reward_gap,
        '登记时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

        # 新增字段（8个）
        '管家ID(serviceHousekeeperId)': housekeeper_id,
        '工单类型': order_type_text,
        '客户联系地址(contactsAddress)': contact_address,
        '项目地址(projectAddress)': project_address,
        '平台单累计数量': housekeeper_data['platform_count'],
        '平台单累计金额': housekeeper_data['platform_amount'],
        '自引单累计数量': housekeeper_data['self_referral_count'],
        '自引单累计金额': housekeeper_data['self_referral_amount']
    }
# ==================== 历史合同处理功能 ====================

def is_historical_contract(contract_data: dict) -> bool:
    """
    判断是否为历史合同

    Args:
        contract_data: 合同数据字典

    Returns:
        bool: True表示历史合同，False表示新增合同
    """
    pc_contract_doc_num = contract_data.get('pcContractdocNum', '')
    # pcContractdocNum有值表示历史合同，为空表示新增合同
    return bool(pc_contract_doc_num and str(pc_contract_doc_num).strip())

def get_contract_type_description(is_historical: bool) -> str:
    """获取合同类型描述"""
    return "活动期内历史合同" if is_historical else "活动期内新增合同"

def collect_existing_housekeeper_stats(processed_data):
    """
    从已处理的数据中收集管家累计统计信息

    Args:
        processed_data: 已处理的合同数据列表

    Returns:
        dict: {管家名称: {'count': 累计单数, 'total_amount': 累计金额, 'performance_amount': 累计业绩金额}}
    """
    housekeeper_stats = {}

    for contract in processed_data:
        housekeeper = contract.get('管家(serviceHousekeeper)', '')
        if not housekeeper:
            continue

        # 只统计新增合同（历史合同不计入累计单数）
        is_historical = contract.get('是否历史合同', 'N') == 'Y'
        if is_historical:
            continue

        if housekeeper not in housekeeper_stats:
            housekeeper_stats[housekeeper] = {
                'count': 0,
                'total_amount': 0.0,
                'performance_amount': 0.0
            }

        # 累计统计（注意：这里统计的是已处理的新增合同）
        housekeeper_stats[housekeeper]['count'] += 1
        housekeeper_stats[housekeeper]['total_amount'] += float(contract.get('管家累计金额', 0))
        housekeeper_stats[housekeeper]['performance_amount'] += float(contract.get('计入业绩金额', 0))

    # 从业绩文件中读取更完整的管家统计信息
    file_stats = load_housekeeper_stats_from_file()

    # 合并统计信息（文件中的数据为准，因为它包含了所有历史数据）
    for housekeeper, stats in file_stats.items():
        if housekeeper in housekeeper_stats:
            # 使用文件中的数据，因为它更完整
            housekeeper_stats[housekeeper] = stats
        else:
            housekeeper_stats[housekeeper] = stats

    return housekeeper_stats

def load_housekeeper_stats_from_file():
    """
    从本地业绩文件中加载管家累计统计信息

    用途：获取当前管家的累计绩效数据，作为处理新增合同时的基线数据
    逻辑：重新计算每个管家的新增合同累计单数，确保准确性

    Returns:
        dict: {管家名称: {'count': 累计单数, 'total_amount': 累计金额, 'performance_amount': 累计业绩金额}}
    """
    from modules.config import PERFORMANCE_DATA_FILENAME_BJ_SEP
    import csv

    housekeeper_stats = {}

    try:
        with open(PERFORMANCE_DATA_FILENAME_BJ_SEP, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                housekeeper = row.get('管家(serviceHousekeeper)', '').strip()
                if not housekeeper:
                    continue

                # 只处理新增合同（历史合同不计入累计单数）
                is_historical = row.get('是否历史合同', 'N') == 'Y'
                if is_historical:
                    continue

                # 初始化管家统计信息
                if housekeeper not in housekeeper_stats:
                    housekeeper_stats[housekeeper] = {
                        'count': 0,
                        'total_amount': 0.0,
                        'performance_amount': 0.0
                    }

                # 重新计算累计数据（逐个累加新增合同）
                contract_amount = float(row.get('合同金额(adjustRefundMoney)', 0))
                performance_amount = float(row.get('计入业绩金额', 0))

                housekeeper_stats[housekeeper]['count'] += 1
                housekeeper_stats[housekeeper]['total_amount'] += contract_amount
                housekeeper_stats[housekeeper]['performance_amount'] += performance_amount

    except FileNotFoundError:
        logging.warning(f"Performance file not found: {PERFORMANCE_DATA_FILENAME_BJ_SEP}")
    except Exception as e:
        logging.error(f"Error reading performance file for housekeeper stats: {e}")

    return housekeeper_stats

def count_new_contracts_from_performance_file():
    """
    统计PerformanceData文件中新增合同的数量

    Returns:
        int: 新增合同数量（不包括历史合同）
    """
    from modules.config import PERFORMANCE_DATA_FILENAME_BJ_SEP
    import csv

    count = 0

    try:
        with open(PERFORMANCE_DATA_FILENAME_BJ_SEP, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # 只统计新增合同
                is_historical = row.get('是否历史合同', 'N') == 'Y'
                if not is_historical:
                    count += 1
    except FileNotFoundError:
        # 文件不存在，返回0
        return 0
    except Exception as e:
        logging.error(f"Error counting new contracts from performance file: {e}")
        return 0

    return count

def load_existing_new_contracts_from_performance_file():
    """
    从PerformanceData文件中加载已有的新增合同数据

    Returns:
        list: 已有的新增合同数据列表
    """
    from modules.config import PERFORMANCE_DATA_FILENAME_BJ_SEP
    import csv

    existing_contracts = []

    try:
        with open(PERFORMANCE_DATA_FILENAME_BJ_SEP, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # 只加载新增合同
                is_historical = row.get('是否历史合同', 'N') == 'Y'
                if not is_historical:
                    existing_contracts.append(dict(row))
    except FileNotFoundError:
        # 文件不存在，返回空列表
        return []
    except Exception as e:
        logging.error(f"Error loading existing new contracts from performance file: {e}")
        return []

    return existing_contracts

def get_housekeeper_count_for_service_appointments(housekeeper_name: str, service_appointment_nums: set) -> int:
    """
    获取指定管家在指定工单组中的新增合同数量

    Args:
        housekeeper_name: 管家姓名
        service_appointment_nums: 工单编号集合

    Returns:
        int: 该管家在这些工单中的新增合同数量
    """
    from modules.config import PERFORMANCE_DATA_FILENAME_BJ_SEP
    import csv

    count = 0

    try:
        with open(PERFORMANCE_DATA_FILENAME_BJ_SEP, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # 检查管家姓名
                if row.get('管家(serviceHousekeeper)', '').strip() != housekeeper_name:
                    continue

                # 检查是否为新增合同
                is_historical = row.get('是否历史合同', 'N') == 'Y'
                if is_historical:
                    continue

                # 检查是否属于指定的工单组
                service_appointment_num = row.get('工单编号(serviceAppointmentNum)', '')
                if service_appointment_num in service_appointment_nums:
                    count += 1

    except FileNotFoundError:
        logging.warning(f"Performance file not found: {PERFORMANCE_DATA_FILENAME_BJ_SEP}")
    except Exception as e:
        logging.error(f"Error reading performance file for housekeeper count: {e}")

    return count

def process_data_jun_beijing_with_existing_stats(contract_data, existing_contract_ids, housekeeper_award_lists, existing_housekeeper_stats):
    """
    北京6月数据处理函数的修正版本，支持传入已有的管家累计统计数据

    Args:
        contract_data: 合同数据列表
        existing_contract_ids: 已存在的合同ID集合
        housekeeper_award_lists: 管家奖励列表
        existing_housekeeper_stats: 已有的管家累计统计数据

    Returns:
        list: 处理后的性能数据列表
    """
    import datetime

    logging.info(f"Starting data processing with {len(existing_contract_ids)} existing contract IDs and existing housekeeper stats.")
    logging.debug(f"Existing housekeeper stats: {existing_housekeeper_stats}")

    # 初始化性能数据列表
    performance_data = []
    # 初始化合同计数器，从已存在的新增合同数量开始
    contract_count_in_activity = count_new_contracts_from_performance_file() + 1

    # 初始化管家合同数据字典，使用传入的已有统计数据
    housekeeper_contracts = {}
    for housekeeper, stats in existing_housekeeper_stats.items():
        housekeeper_award = []
        if housekeeper in housekeeper_award_lists:
            housekeeper_award = housekeeper_award_lists[housekeeper]

        housekeeper_contracts[housekeeper] = {
            'count': stats['count'],
            'total_amount': stats['total_amount'],
            'performance_amount': stats['performance_amount'],
            'awarded': housekeeper_award
        }

    # 初始化已处理的合同ID集合
    processed_contract_ids = set()

    # 初始化工单编号累计金额字典
    service_appointment_amounts = {}

    # 遍历合同数据
    logging.info("Starting to process contract data with existing stats...")

    for contract in contract_data:
        # 获取合同ID并转换为字符串
        contract_id = str(contract['合同ID(_id)'])
        # 检查合同ID是否已处理过，如果已经处理过，则跳过当前循环的剩余部分，进入下一次循环
        if contract_id in processed_contract_ids:
            logging.debug(f"Skipping duplicate contract ID: {contract_id}")
            continue

        # 获取管家信息
        housekeeper = contract['管家(serviceHousekeeper)']
        # 如果管家信息不存在，则初始化管家数据（使用默认值）
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

        # 初始化工单编号累计金额（包含历史合同占用）
        if service_appointment_num not in service_appointment_amounts:
            # 初始化时包含历史合同占用
            historical_usage = globals().get('historical_project_usage', {}).get(service_appointment_num, 0)
            service_appointment_amounts[service_appointment_num] = historical_usage

        # 检查工单编号累计金额是否超过上限
        if service_appointment_amounts[service_appointment_num] + current_contract_amount > config.SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB:
            # 计算可以添加的金额
            amount_to_add = config.SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB - service_appointment_amounts[service_appointment_num]
            # 确保不为负数
            amount_to_add = max(0, amount_to_add)
            logging.info(f"Contract {contract_id} for project {service_appointment_num}: amount limited from {current_contract_amount} to {amount_to_add} due to project limit")
        else:
            amount_to_add = current_contract_amount

        # 更新工单编号的累计金额
        service_appointment_amounts[service_appointment_num] += current_contract_amount

        # 更新管家合同总金额与计入的金额，保持为浮点数
        housekeeper_contracts[housekeeper]['total_amount'] += current_contract_amount  # 修复：使用原始合同金额，不受工单上限影响
        # 修复：使用考虑工单上限的实际业绩金额，而不是仅考虑单合同上限的performance_amount
        actual_performance_amount = min(amount_to_add, performance_amount)
        housekeeper_contracts[housekeeper]['performance_amount'] += actual_performance_amount

        # 记录计算过程日志
        logging.debug(f"Housekeeper {housekeeper} count: {housekeeper_contracts[housekeeper]['count']}")
        logging.debug(f"Housekeeper {housekeeper} total amount: {housekeeper_contracts[housekeeper]['total_amount']}")

        # 添加合同ID到已处理集合
        processed_contract_ids.add(contract_id)

        reward_types, reward_names, next_reward_gap = determine_rewards_jun_beijing_generic(contract_count_in_activity, housekeeper_contracts[housekeeper], current_contract_amount)

        # 检查是否激活奖励
        active_status = '1' if reward_types else '0'

        # 构建性能数据记录
        performance_record = {
            '活动编号': 'BJ-JUN',
            '合同ID(_id)': contract['合同ID(_id)'],
            '活动城市(province)': contract['活动城市(province)'],
            '工单编号(serviceAppointmentNum)': contract['工单编号(serviceAppointmentNum)'],
            'Status': contract['Status'],
            '管家(serviceHousekeeper)': contract['管家(serviceHousekeeper)'],
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
            '转化率(conversion)': contract['转化率(conversion)'],
            '平均客单价(average)': contract['平均客单价(average)'],
            '活动期内第几个合同': contract_count_in_activity,
            '管家累计单数': housekeeper_contracts[housekeeper]['count'],
            '管家累计金额': housekeeper_contracts[housekeeper]['total_amount'] ,
            '奖金池': housekeeper_contracts[housekeeper]['total_amount'],  # 奖金池等于累计金额
            '计入业绩金额': performance_amount,  # 修复：使用单个合同的业绩金额，而不是管家累计业绩金额
            '激活奖励状态': active_status,
            '奖励类型': reward_types,
            '奖励名称': reward_names,
            '是否发送通知': 'N',  # 初始状态为未发送，通知函数处理后会更新为Y
            '备注': next_reward_gap if next_reward_gap else '无',  # 添加下一级奖项所需金额差信息
            '登记时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        performance_data.append(performance_record)

        # 增加合同计数器
        contract_count_in_activity += 1

    logging.info(f"Data processing completed. Processed {len(performance_data)} contracts.")
    return performance_data

def get_existing_project_totals_from_performance_file():
    """
    从业绩文件中读取各工单的累计业绩金额

    Returns:
        dict: {工单编号: 累计业绩金额}
    """
    from modules.config import PERFORMANCE_DATA_FILENAME_BJ_SEP
    import csv

    project_totals = {}

    try:
        with open(PERFORMANCE_DATA_FILENAME_BJ_SEP, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                service_appointment_num = row.get('工单编号(serviceAppointmentNum)', '').strip()
                performance_amount = float(row.get('计入业绩金额', 0))

                if service_appointment_num:
                    if service_appointment_num not in project_totals:
                        project_totals[service_appointment_num] = 0
                    project_totals[service_appointment_num] += performance_amount

    except FileNotFoundError:
        # 业绩文件不存在，返回空字典
        pass
    except Exception as e:
        logging.warning(f"Error reading existing project totals: {e}")

    return project_totals

def process_historical_contract_with_project_limit(
    contract_data: dict,
    project_performance_tracker: dict,
    project_limit: float
) -> dict:
    """
    处理历史合同（考虑工单级别5万元上限）
    - 不播报
    - 不计入管家累计单数和金额
    - 计入业绩金额（受工单5万上限限制）
    - 不参与奖励计算
    """
    import datetime

    # 基础字段处理
    contract_id = contract_data.get('合同ID(_id)', '')
    contract_number = contract_data.get('合同编号(contractdocNum)', '')
    service_housekeeper = contract_data.get('管家(serviceHousekeeper)', '')
    service_appointment_num = contract_data.get('工单编号(serviceAppointmentNum)', '')
    adjust_refund_money = float(contract_data.get('合同金额(adjustRefundMoney)', 0))

    # 计算工单级别的业绩金额（考虑5万上限）
    if service_appointment_num not in project_performance_tracker:
        project_performance_tracker[service_appointment_num] = 0

    current_project_total = project_performance_tracker[service_appointment_num]
    remaining_quota = max(0, project_limit - current_project_total)
    performance_amount = min(adjust_refund_money, remaining_quota)

    # 更新工单累计
    project_performance_tracker[service_appointment_num] += performance_amount

    return {
        '活动编号': 'BJ-SEP',
        '合同ID(_id)': contract_id,
        '活动城市(province)': contract_data.get('活动城市(province)', '北京'),
        '工单编号(serviceAppointmentNum)': service_appointment_num,
        'Status': contract_data.get('Status', ''),
        '管家(serviceHousekeeper)': service_housekeeper,
        '合同编号(contractdocNum)': contract_number,
        '合同金额(adjustRefundMoney)': adjust_refund_money,
        '支付金额(paidAmount)': contract_data.get('支付金额(paidAmount)', 0),
        '差额(difference)': contract_data.get('差额(difference)', 0),
        'State': contract_data.get('State', ''),
        '创建时间(createTime)': contract_data.get('创建时间(createTime)', ''),
        '服务商(orgName)': contract_data.get('服务商(orgName)', ''),
        '签约时间(signedDate)': contract_data.get('签约时间(signedDate)', ''),
        'Doorsill': contract_data.get('Doorsill', ''),
        '款项来源类型(tradeIn)': contract_data.get('款项来源类型(tradeIn)', ''),
        '转化率(conversion)': contract_data.get('转化率(conversion)', ''),
        '平均客单价(average)': contract_data.get('平均客单价(average)', ''),
        '活动期内第几个合同': 0,  # 不计入个人合同序号
        '管家累计金额': 0,        # 不计入累计金额
        '管家累计单数': 0,        # 不计入累计单数
        '奖金池': 0,              # 不计入奖金池
        '计入业绩金额': performance_amount,  # 考虑工单5万上限的业绩金额
        '激活奖励状态': '0',      # 不激活奖励
        '奖励类型': '',           # 不参与奖励
        '奖励名称': '',           # 不参与奖励
        '是否发送通知': 'N',      # 不发送通知
        '是否历史合同': 'Y',      # 标记为历史合同
        '合同类型说明': '活动期内历史合同',
        '备注': '历史合同-仅计入业绩金额',
        '登记时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def process_historical_contract(contract_data: dict) -> dict:
    """
    处理历史合同
    - 不播报
    - 不计入管家累计单数和金额
    - 仅计入业绩金额
    - 不参与奖励计算
    """
    import datetime

    # 基础字段处理 - 使用正确的字段名（带括号的完整字段名）
    contract_id = contract_data.get('合同ID(_id)', '')
    contract_number = contract_data.get('合同编号(contractdocNum)', '')
    service_housekeeper = contract_data.get('管家(serviceHousekeeper)', '')
    adjust_refund_money = float(contract_data.get('合同金额(adjustRefundMoney)', 0))

    return {
        '活动编号': 'BJ-SEP',
        '合同ID(_id)': contract_id,
        '活动城市(province)': contract_data.get('活动城市(province)', '北京'),
        '工单编号(serviceAppointmentNum)': contract_data.get('工单编号(serviceAppointmentNum)', ''),
        'Status': contract_data.get('Status', ''),
        '管家(serviceHousekeeper)': service_housekeeper,
        '合同编号(contractdocNum)': contract_number,
        '合同金额(adjustRefundMoney)': adjust_refund_money,
        '支付金额(paidAmount)': contract_data.get('支付金额(paidAmount)', 0),
        '差额(difference)': contract_data.get('差额(difference)', 0),
        'State': contract_data.get('State', ''),
        '创建时间(createTime)': contract_data.get('创建时间(createTime)', ''),
        '服务商(orgName)': contract_data.get('服务商(orgName)', ''),
        '签约时间(signedDate)': contract_data.get('签约时间(signedDate)', ''),
        'Doorsill': contract_data.get('Doorsill', ''),
        '款项来源类型(tradeIn)': contract_data.get('款项来源类型(tradeIn)', ''),
        '转化率(conversion)': contract_data.get('转化率(conversion)', ''),
        '平均客单价(average)': contract_data.get('平均客单价(average)', ''),
        '活动期内第几个合同': 0,  # 不计入个人合同序号
        '管家累计金额': 0,        # 不计入累计金额
        '管家累计单数': 0,        # 不计入累计单数
        '奖金池': 0,              # 不计入奖金池
        '计入业绩金额': adjust_refund_money,  # 仅计入业绩
        '激活奖励状态': '0',      # 不激活奖励
        '奖励类型': '',           # 不参与奖励
        '奖励名称': '',           # 不参与奖励
        '是否发送通知': 'N',      # 不发送通知
        '是否历史合同': 'Y',      # 标记为历史合同
        '合同类型说明': '活动期内历史合同',
        '备注': '历史合同-仅计入业绩金额',
        '登记时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def process_new_contract(
    contract_data: dict,
    existing_contract_ids: set,
    housekeeper_award_lists: dict
) -> dict:
    """
    处理新增合同（按现有逻辑）
    - 正常播报
    - 计入管家累计单数和金额
    - 计入业绩金额
    - 参与奖励计算
    """
    # 临时保存原有的配置和函数
    original_determine_rewards = globals().get('determine_rewards_jun_beijing_generic')
    original_performance_cap = getattr(config, 'PERFORMANCE_AMOUNT_CAP_BJ_FEB', 500000)

    # 临时替换为9月的配置
    globals()['determine_rewards_jun_beijing_generic'] = determine_rewards_sep_beijing_generic
    # 设置9月的5万元上限
    config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000

    try:
        # 调用现有的数据处理逻辑处理单个合同
        result = process_data_jun_beijing([contract_data], existing_contract_ids, housekeeper_award_lists)

        if result:
            processed_contract = result[0]
            # 修改活动编号为9月
            processed_contract['活动编号'] = 'BJ-SEP'

            # 添加合同类型标识
            processed_contract.update({
                '是否历史合同': 'N',
                '合同类型说明': '活动期内新增合同'
            })

            return processed_contract
        else:
            # 如果处理失败，返回基础数据
            return {
                '活动编号': 'BJ-SEP',
                '合同ID(_id)': contract_data.get('_id', ''),
                '是否历史合同': 'N',
                '合同类型说明': '活动期内新增合同',
                '备注': '新增合同-处理异常'
            }
    finally:
        # 恢复原有的配置和函数
        if original_determine_rewards:
            globals()['determine_rewards_jun_beijing_generic'] = original_determine_rewards
        config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = original_performance_cap

def process_data_sep_beijing_with_historical_support(
    contract_data: list,
    existing_contract_ids: set,
    housekeeper_award_lists: dict
) -> list:
    """
    北京9月数据处理函数（支持历史合同处理）

    Args:
        contract_data: 合同数据列表
        existing_contract_ids: 已存在的合同ID集合
        housekeeper_award_lists: 管家奖励列表

    Returns:
        list: 处理后的性能数据列表
    """
    processed_data = []
    new_contracts = []  # 收集新增合同，批量处理

    # 工单级别业绩金额管理器 - 跟踪每个工单的累计业绩金额
    project_performance_tracker = {}
    PROJECT_LIMIT = 50000  # 9月份5万元上限

    for contract in contract_data:
        # 获取合同ID并检查是否已处理过
        contract_id = str(contract.get('合同ID(_id)', ''))
        if contract_id in existing_contract_ids:
            continue  # 跳过已处理的合同

        # 判断是否为历史合同
        is_historical = is_historical_contract(contract)

        if is_historical:
            # 历史合同：处理并更新工单累计
            processed_contract = process_historical_contract_with_project_limit(
                contract, project_performance_tracker, PROJECT_LIMIT
            )
            processed_data.append(processed_contract)
        else:
            # 新增合同：收集起来批量处理
            new_contracts.append(contract)

    # 批量处理新增合同（使用原有逻辑，避免递归）
    if new_contracts:
        # 步骤1：收集已有管家累计数据（从已处理的历史合同和业绩文件中）
        existing_housekeeper_stats = collect_existing_housekeeper_stats(processed_data)
        logging.info(f"Existing housekeeper stats from processed historical contracts: {existing_housekeeper_stats}")

        # 步骤1.5：计算历史合同对工单配额的占用
        global historical_project_usage
        historical_project_usage = {}
        for contract in processed_data:
            if contract.get('是否历史合同', 'N') == 'Y':
                service_appointment_num = contract.get('工单编号(serviceAppointmentNum)', '')
                contract_amount = float(contract.get('合同金额(adjustRefundMoney)', 0))

                if service_appointment_num:
                    if service_appointment_num not in historical_project_usage:
                        historical_project_usage[service_appointment_num] = 0
                    historical_project_usage[service_appointment_num] += contract_amount

        # 临时保存原有的配置和函数
        original_determine_rewards = globals().get('determine_rewards_jun_beijing_generic')
        original_performance_cap = getattr(config, 'PERFORMANCE_AMOUNT_CAP_BJ_FEB', 500000)

        # 临时替换为9月的配置
        globals()['determine_rewards_jun_beijing_generic'] = determine_rewards_sep_beijing_generic
        # 设置9月的5万元上限
        config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000

        try:
            # 步骤2：调用修正后的数据处理逻辑，传递已有管家累计数据
            new_processed_data = process_data_jun_beijing_with_existing_stats(
                new_contracts, existing_contract_ids, housekeeper_award_lists, existing_housekeeper_stats
            )

            # 步骤3：修正新增合同的业绩金额，考虑工单级别累计（包括业绩文件中已存在的累计）
            logging.info(f"Project performance tracker before new contracts: {project_performance_tracker}")

            # 从业绩文件中读取已存在的工单累计金额
            existing_project_totals = get_existing_project_totals_from_performance_file()
            logging.info(f"Existing project totals from performance file: {existing_project_totals}")

            # 步骤4：重新计算累计单数，确保连续性
            # 使用业绩文件中的累计单数作为基础（只包含新增合同的累计）
            housekeeper_cumulative_counts = {}
            for housekeeper, stats in existing_housekeeper_stats.items():
                housekeeper_cumulative_counts[housekeeper] = stats['count']

            for processed_contract in new_processed_data:
                service_appointment_num = processed_contract.get('工单编号(serviceAppointmentNum)', '')
                original_performance = float(processed_contract.get('计入业绩金额', 0))
                housekeeper = processed_contract.get('管家(serviceHousekeeper)', '')

                logging.info(f"Processing new contract {processed_contract.get('合同编号(contractdocNum)', '')} for project {service_appointment_num}, original performance: {original_performance}")



                # 计算工单的总累计：当前批次累计 + 业绩文件中已存在的累计
                current_batch_total = project_performance_tracker.get(service_appointment_num, 0)
                existing_file_total = existing_project_totals.get(service_appointment_num, 0)
                total_project_amount = current_batch_total + existing_file_total

                remaining_quota = max(0, PROJECT_LIMIT - total_project_amount)
                corrected_performance = min(original_performance, remaining_quota)

                logging.info(f"Project {service_appointment_num}: batch_total={current_batch_total}, file_total={existing_file_total}, total={total_project_amount}, remaining_quota={remaining_quota}, corrected_performance={corrected_performance}")

                # 更新业绩金额（受工单上限影响）
                processed_contract['计入业绩金额'] = corrected_performance
                # 更新当前批次累计
                project_performance_tracker[service_appointment_num] = current_batch_total + corrected_performance

                # 步骤5：修正累计单数，确保连续性
                if housekeeper not in housekeeper_cumulative_counts:
                    housekeeper_cumulative_counts[housekeeper] = 0
                housekeeper_cumulative_counts[housekeeper] += 1
                processed_contract['管家累计单数'] = housekeeper_cumulative_counts[housekeeper]

                logging.info(f"Corrected housekeeper {housekeeper} cumulative count to: {housekeeper_cumulative_counts[housekeeper]}")

                # 不修改备注字段，保持原有的奖励信息

            # 修改活动编号为9月并添加类型标识
            for processed_contract in new_processed_data:
                processed_contract['活动编号'] = 'BJ-SEP'
                processed_contract.update({
                    '是否历史合同': 'N',
                    '合同类型说明': '活动期内新增合同'
                })

            processed_data.extend(new_processed_data)
        finally:
            # 恢复原有的配置和函数
            if original_determine_rewards:
                globals()['determine_rewards_jun_beijing_generic'] = original_determine_rewards
            config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = original_performance_cap

    # 步骤6：添加管家累计业绩金额字段
    processed_data = add_housekeeper_cumulative_performance_amount(processed_data)

    return processed_data

def add_housekeeper_cumulative_performance_amount(processed_data: list) -> list:
    """
    为每个合同记录添加管家累计业绩金额字段

    业务逻辑：
    1. 历史合同的累计业绩金额设为0（不参与累计）
    2. 读取PerformanceData文件中已有的新增合同
    3. 与当前批次的新增合同合并
    4. 按签约时间排序后重新计算每个管家的累计业绩金额
    5. 受工单5万上限和单个合同5万上限双重影响（通过"计入业绩金额"字段体现）

    Args:
        processed_data: 处理后的合同数据列表

    Returns:
        list: 添加了管家累计业绩金额字段的合同数据列表
    """
    # 首先为所有记录初始化字段
    for record in processed_data:
        record['管家累计业绩金额'] = 0

    # 读取PerformanceData文件中已有的新增合同
    existing_new_contracts = load_existing_new_contracts_from_performance_file()

    # 按管家分组，合并已有的和当前批次的新增合同
    housekeeper_all_new_contracts = {}

    # 1. 先添加PerformanceData文件中已有的新增合同
    for contract in existing_new_contracts:
        housekeeper = contract.get('管家(serviceHousekeeper)', '')
        if housekeeper not in housekeeper_all_new_contracts:
            housekeeper_all_new_contracts[housekeeper] = []
        housekeeper_all_new_contracts[housekeeper].append(contract)

    # 2. 再添加当前批次的新增合同
    for record in processed_data:
        housekeeper = record.get('管家(serviceHousekeeper)', '')
        is_historical = record.get('是否历史合同', 'N') == 'Y'

        # 只处理新增合同
        if not is_historical:
            if housekeeper not in housekeeper_all_new_contracts:
                housekeeper_all_new_contracts[housekeeper] = []
            housekeeper_all_new_contracts[housekeeper].append(record)

    # 为每个管家的所有新增合同按时间排序并计算累计业绩金额
    for housekeeper, contracts in housekeeper_all_new_contracts.items():
        # 按签约时间排序
        contracts.sort(key=lambda x: x.get('签约时间(signedDate)', ''))

        # 逐步累积计算
        cumulative_performance = 0
        for contract in contracts:
            performance_amount = float(contract.get('计入业绩金额', 0))
            cumulative_performance += performance_amount

            # 只更新当前批次的合同记录（PerformanceData中的记录不需要更新）
            if contract in processed_data:
                contract['管家累计业绩金额'] = cumulative_performance

    return processed_data

# 北京9月数据处理函数（包装函数）
def process_data_sep_beijing(contract_data, existing_contract_ids, housekeeper_award_lists):
    """
    北京9月数据处理函数（包装函数）
    支持历史合同和新增合同的差异化处理
    """
    # 检查是否有历史合同字段，如果有则使用新的处理逻辑
    has_historical_field = any('pcContractdocNum' in contract for contract in contract_data)

    if has_historical_field:
        # 使用支持历史合同的处理逻辑
        return process_data_sep_beijing_with_historical_support(
            contract_data, existing_contract_ids, housekeeper_award_lists
        )
    else:
        # 使用原有的处理逻辑（向后兼容）
        # 临时保存原有的配置和函数
        original_determine_rewards = globals().get('determine_rewards_jun_beijing_generic')
        original_performance_cap = getattr(config, 'PERFORMANCE_AMOUNT_CAP_BJ_FEB', 500000)

        # 临时替换为9月的配置
        globals()['determine_rewards_jun_beijing_generic'] = determine_rewards_sep_beijing_generic
        # 设置9月的5万元上限
        config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000

        try:
            # 调用原有的数据处理逻辑
            result = process_data_jun_beijing(contract_data, existing_contract_ids, housekeeper_award_lists)

            # 修改活动编号为9月
            for record in result:
                record['活动编号'] = 'BJ-SEP'

            # 添加管家累计业绩金额字段
            result = add_housekeeper_cumulative_performance_amount(result)

            return result
        finally:
            # 恢复原有的配置和函数
            if original_determine_rewards:
                globals()['determine_rewards_jun_beijing_generic'] = original_determine_rewards
            config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = original_performance_cap