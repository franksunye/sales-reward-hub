# 上海9月签约激励Job升级设计文档

## 文档信息
- **Job名称**: `signing_and_sales_incentive_sep_shanghai()`
- **创建日期**: 2025-08-29
- **版本**: v1.0
- **状态**: 设计阶段
- **基于**: 上海8月job (`signing_and_sales_incentive_aug_shanghai`)

## 1. 升级概述

### 1.1 核心变化
- **数据源升级**: 新增4个字段支持自引单和平台单区分
- **业务逻辑升级**: 引入自引单奖励机制
- **通知消息升级**: 区分自引单和平台单的播报格式
- **台账结构升级**: 新增自引单相关统计字段

### 1.2 新增字段
根据数据源 http://metabase.fsgo365.cn:3000/question/1838 的结构变化：
- `serviceHousekeeperId`: 管家ID
- `sourceType`: 工单类型 (1=自引单, 2/4/5=平台单)
- `contactsAddress`: 客户联系地址
- `projectAddress`: 项目地址

### 1.3 业务规则变化
- **统一订单处理**: 平台单和自引单都是订单，使用统一的处理流程
- **差异化奖励规则**:
  - 平台单：节节高奖励体系（累计金额阈值）
  - 自引单：项目地址去重奖励（每个唯一项目地址50元红包）
- **统一数据结构**: 两种订单类型使用相同的业绩数据文件结构

## 2. 技术架构升级

### 2.1 组件复用和新建
```
signing_and_sales_incentive_sep_shanghai()
├── 数据获取层: send_request_with_managed_session() [复用]
├── 数据保存层: save_to_csv_with_headers() [复用，传入新字段列表]
├── 数据处理层: process_data_shanghai_sep() [新建，基于process_data_shanghai_apr]
├── 平台单奖励计算: determine_rewards_apr_shanghai_generic() [复用]
├── 自引单奖励计算: determine_self_referral_rewards() [新建]
├── 通知发送层: notify_awards_shanghai_generic() [新建，参考北京模式]
└── 文件管理层: archive_file() [复用]
```

### 2.2 统一订单处理流程
```
Metabase API → 订单数据 → 按类型应用奖励规则 → 业绩数据文件 → 生成通知任务 → 归档
                ↓              ↓                ↓            ↓
            sourceType    平台单:节节高规则      统一记录    create_task()
            识别订单类型   自引单:去重规则      奖励信息    加入任务队列
```

### 2.3 数据处理详细流程
```
订单数据 → 类型识别 → 奖励计算 → 记录到CSV → 生成通知任务
   ↓         ↓         ↓         ↓         ↓
原始订单   sourceType  应用规则   奖励信息   create_task()
          1=自引单    平台单:累计金额阈值      ↓
          其他=平台单  自引单:项目地址去重   任务队列
```

**核心原则**：
- 所有订单统一处理，仅奖励规则不同
- 业绩数据文件是唯一的奖励信息源
- 通知任务与业务逻辑解耦，通过任务队列异步处理

## 3. 数据结构升级

### 3.1 API响应数据结构（新增字段）
```json
{
  "data": {
    "rows": [
      [
        // ... 原有17个字段 ...
        "housekeeper_id_001",           // serviceHousekeeperId
        "1",                            // sourceType (1=自引单, 2/4/5=平台单)
        "上海市浦东新区张江路123号",      // contactsAddress
        "上海市浦东新区科技园456号"       // projectAddress
      ]
    ]
  }
}
```

### 3.2 CSV文件数据结构升级

#### 3.2.1 原始合同数据文件 (ContractData-SH-Sep.csv)
```csv
合同ID(_id),活动城市(province),...,平均客单价(average),管家ID(serviceHousekeeperId),工单类型(sourceType),客户联系地址(contactsAddress),项目地址(projectAddress)
```

**新增字段说明**：
- `管家ID(serviceHousekeeperId)`: 管家唯一标识 (String)
- `工单类型(sourceType)`: 1=自引单, 2/4/5=平台单 (Integer)
- `客户联系地址(contactsAddress)`: 客户联系地址 (String)
- `项目地址(projectAddress)`: 项目地址，用于自引单去重 (String)

#### 3.2.2 业绩数据文件 (PerformanceData-SH-Sep.csv)

**完整字段结构**：
```csv
活动编号,合同ID(_id),活动城市(province),工单编号(serviceAppointmentNum),Status,管家(serviceHousekeeper),合同编号(contractdocNum),合同金额(adjustRefundMoney),支付金额(paidAmount),差额(difference),State,创建时间(createTime),服务商(orgName),签约时间(signedDate),Doorsill,款项来源类型(tradeIn),转化率(conversion),平均客单价(average),活动期内第几个合同,管家累计金额,管家累计单数,奖金池,计入业绩金额,激活奖励状态,奖励类型,奖励名称,是否发送通知,备注,登记时间,工单类型,项目地址,平台单累计数量,平台单累计金额,自引单累计数量,自引单累计金额
```

**字段变化策略**：

**保留字段（29个原有字段）**：
- 所有原有字段保持不变，确保向后兼容性
- `管家累计金额` → **保持原有语义**：继续表示管家所有类型订单的累计金额
- `管家累计单数` → **保持原有语义**：继续表示管家所有类型订单的累计单数
- 其他27个字段保持原有含义不变

**新增字段（6个）**：
- `工单类型`: 自引单/平台单，从sourceType字段转换而来 (String)
- `项目地址`: 项目地址，从API新增字段projectAddress获取 (String)
- `平台单累计数量`: 管家平台单累计数量 (Integer)
- `平台单累计金额`: 管家平台单累计金额 (Float)
- `自引单累计数量`: 管家自引单累计数量 (Integer)
- `自引单累计金额`: 管家自引单累计金额 (Float)

**重要说明**：
1. **无字段删除**：为保证数据完整性和向后兼容，不删除任何原有字段
2. **语义保持**：`管家累计金额`和`管家累计单数`保持原有含义，避免破坏现有报表和分析
3. **新增统计**：通过新增字段提供平台单和自引单的分类统计
4. **统一奖励字段**：平台单和自引单都使用原有的`奖励类型`和`奖励名称`字段，无需新增专用字段
5. **数据一致性**：`管家累计金额` = `平台单累计金额` + `自引单累计金额`

### 3.3 内存数据结构升级

#### 3.3.1 管家合同数据结构
```python
housekeeper_contracts = {
    "张三_上海英森防水工程有限公司": {
        'platform_count': 3,              # 平台单数量
        'platform_amount': 45000.0,       # 平台单累计金额
        'platform_performance_amount': 45000.0,  # 平台单业绩金额
        'self_referral_count': 2,          # 自引单数量
        'self_referral_amount': 15000.0,   # 自引单累计金额
        'awarded': ["基础奖"],             # 平台单已获得奖励
        'self_referral_projects': set(),   # 自引单项目地址集合（去重用）
        'self_referral_rewards': 0         # 自引单奖励数量
    }
}
```

#### 3.3.2 自引单奖励计算返回结构
```python
# determine_self_referral_rewards() 返回值（配置驱动）
(
    "自引单",                    # reward_type (String, 从配置获取)
    "红包",                      # reward_name (String, 从配置获取)
    True                        # is_qualified (Boolean)
)
```

#### 3.3.3 自引单配置结构
```python
# get_self_referral_config() 返回值
{
    "enable": True,                    # 是否启用自引单奖励
    "reward_type": "自引单",           # 奖励类型
    "reward_name": "红包",             # 奖励名称
    "reward_amount": 50,               # 奖励金额
    "deduplication_field": "projectAddress"  # 去重字段
}
```

## 4. 核心功能升级

### 4.1 数据处理函数 - process_data_shanghai_sep()
**新建函数，基于 process_data_shanghai_apr() 升级**

**核心逻辑**：
1. 按 sourceType 字段分类处理合同
2. 平台单：复用原有逻辑计算节节高奖励
3. 自引单：按项目地址去重，符合条件的发放红包奖励
4. 统一记录到业绩台账

**统一订单处理逻辑**：
```python
def process_data_shanghai_sep(contract_data, existing_contract_ids, housekeeper_award_lists):
    # 1. 初始化数据结构
    config_key = "SH-2025-09"
    performance_data = []
    contract_count_in_activity = len(existing_contract_ids) + 1
    housekeeper_contracts = {}
    processed_contract_ids = set()

    # 2. 统一遍历所有订单
    for contract in contract_data:
        contract_id = contract['合同ID(_id)']
        if contract_id in existing_contract_ids or contract_id in processed_contract_ids:
            continue

        # 字段映射：API字段名 -> CSV字段名
        source_type = int(contract.get('工单类型(sourceType)', 2))  # 默认为平台单
        project_address = contract.get('项目地址(projectAddress)', '')
        housekeeper_key = f"{contract['管家(serviceHousekeeper)']}_{contract['服务商(orgName)']}"

        # 初始化管家数据结构
        if housekeeper_key not in housekeeper_contracts:
            housekeeper_contracts[housekeeper_key] = {
                'count': 0, 'total_amount': 0, 'performance_amount': 0, 'awarded': [],
                'platform_count': 0, 'platform_amount': 0,
                'self_referral_count': 0, 'self_referral_amount': 0,
                'self_referral_projects': set()
            }

        # 根据订单类型应用不同的奖励规则
        if source_type == 1:
            # 自引单：项目地址去重奖励
            reward_types, reward_names, _ = determine_self_referral_rewards(
                project_address, housekeeper_contracts[housekeeper_key], config_key)
            # 更新自引单统计
            housekeeper_contracts[housekeeper_key]['self_referral_count'] += 1
            housekeeper_contracts[housekeeper_key]['self_referral_amount'] += contract_amount
        else:
            # 平台单：节节高奖励
            reward_types, reward_names, _ = determine_rewards_apr_shanghai_generic(
                contract_count_in_activity, housekeeper_contracts[housekeeper_key], contract_amount)
            # 更新平台单统计
            housekeeper_contracts[housekeeper_key]['platform_count'] += 1
            housekeeper_contracts[housekeeper_key]['platform_amount'] += contract_amount

        # 更新总体统计
        housekeeper_contracts[housekeeper_key]['count'] += 1
        housekeeper_contracts[housekeeper_key]['total_amount'] += contract_amount

        # 生成业绩数据记录（包含新增字段）
        performance_record = create_performance_record(contract, reward_types, reward_names,
                                                     housekeeper_contracts[housekeeper_key],
                                                     contract_count_in_activity, source_type, project_address)
        performance_data.append(performance_record)

        processed_contract_ids.add(contract_id)
        contract_count_in_activity += 1

    return performance_data
```

### 4.2 自引单奖励计算 - determine_self_referral_rewards()
**新建函数，返回奖励信息供写入业绩数据文件**

**核心逻辑**：
```python
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
```

### 4.3 统一通知任务生成 - notify_awards_shanghai_generic()
**新建函数，参考北京通用模式 notify_awards_beijing_generic()**

**核心逻辑**：
1. 读取业绩数据文件，获取奖励信息
2. 生成群通知任务：发送订单签约喜报到运营群
3. 生成个人奖励通知任务：发送给活动管理员
4. 通过 create_task() 将通知任务加入队列，与业务逻辑解耦

**实现逻辑**：
```python
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
            processed_accumulated_amount = preprocess_amount(record["管家累计金额"])
            processed_conversion_rate = preprocess_rate(record["转化率(conversion)"])
            next_msg = '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩 🎉🎉🎉' if '无' in record["备注"] else f'{record["备注"]}'

            # 新增：显示订单类型
            order_type = record.get("工单类型", "平台单")  # 默认为平台单
            msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {record["管家(serviceHousekeeper)"]} 签约合同（{order_type}） {record["合同编号(contractdocNum)"]} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {record["活动期内第几个合同"]} 单，

🌻 个人累计签约第 {record["管家累计单数"]} 单，

🌻 个人累计签约 {processed_accumulated_amount} 元，

🌻 个人转化率 {processed_conversion_rate}，

👊 {next_msg}。
'''
            create_task('send_wecom_message', WECOM_GROUP_NAME_SH_SEP, msg)

            # 生成个人奖励通知任务
            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "SH")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_SH_SEP, jiangli_msg)

            # 更新发送状态（保持与现有系统一致）
            update_send_status(status_filename, contract_id, '发送成功')
            record['是否发送通知'] = 'Y'
            updated = True

    if updated:
        write_performance_data_to_csv(performance_data_filename, records, list(records[0].keys()))

# 包装函数：上海9月
def notify_awards_sep_shanghai(performance_data_filename, status_filename):
    return notify_awards_shanghai_generic(
        performance_data_filename, status_filename, "SH-2025-09"
    )
```

**关键特点**：
- 统一处理所有订单类型，奖励信息完全来自业绩数据文件
- 直接复用现有的 `generate_award_message()` 函数，无需区分订单类型
- 群通知消息显示不同订单类型的统计信息

**群通知消息格式升级**：
```
🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {管家名称} 签约合同（{平台单/自引单}） {合同编号} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {平台单序号} 单，

🌻 个人累计签约第 {个人累计单数} 单，

🌻 个人累计签约 {个人累计金额} 元，

🌻 个人转化率 {转化率}，

👊 {奖励状态描述} 🎉🎉🎉。
```

**数据来源**：
- 平台单/自引单类型：从业绩数据文件的 `工单类型` 字段获取
- 统计数据：保持与现有上海通知格式一致，使用原有字段
- 详细分类统计：可在后续版本中考虑添加平台单/自引单分类显示

**个人奖励消息格式（发送给活动管理员）**：
统一使用现有的 `generate_award_message()` 函数处理所有奖励类型：

- 平台单奖励：
```
{管家名称}签约合同{合同编号}

达成{奖励名称}奖励条件，获得签约奖励{奖励金额}元 🧧🧧🧧
```

- 自引单奖励：
```
{管家名称}签约合同{合同编号}

达成{奖励名称}奖励条件，获得签约奖励{奖励金额}元 🧧🧧🧧
```

**实现说明**：
- 直接复用现有的 `generate_award_message(record, awards_mapping, "SH")` 函数
- 奖励类型和名称从业绩数据文件的 `奖励类型` 和 `奖励名称` 字段读取
- 奖励金额通过 `awards_mapping[奖励名称]` 获取
- 无需区分平台单和自引单，统一处理

**示例**：
- 平台单：`芮恒签约合同YHWX-SH-GTZH-2025080083\n\n达成达标奖奖励条件，获得签约奖励300元 🧧🧧🧧`
- 自引单：`张三签约合同YHWX-SH-ZYYY-2025090001\n\n达成自引单奖励条件，获得自引单红包50元 🧧🧧🧧`



## 5. 配置升级

### 5.1 新增配置项

#### 5.1.1 基础配置
```python
# API配置
API_URL_SH_SEP = METABASE_URL + "/api/card/1838/query"

# 文件路径
TEMP_CONTRACT_DATA_FILE_SH_SEP = 'state/ContractData-SH-Sep.csv'
PERFORMANCE_DATA_FILENAME_SH_SEP = 'state/PerformanceData-SH-Sep.csv'
STATUS_FILENAME_SH_SEP = 'state/send_status_sh_sep.json'

# 通知配置
WECOM_GROUP_NAME_SH_SEP = '（上海）运营群'
CAMPAIGN_CONTACT_SH_SEP = '满浩浩'
```

#### 5.1.2 通用化奖励配置（新增到REWARD_CONFIGS）
```python
REWARD_CONFIGS = {
    # ... 现有配置 ...

    # 上海2025年9月活动配置
    "SH-2025-09": {
        "lucky_number": "",  # 禁用幸运奖
        "performance_limits": {
            "enable_cap": False,  # 上海不启用业绩上限
            "single_contract_cap": 40000
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 平台单需要5个合同
            "tiers": [
                {"name": "基础奖", "threshold": 40000},
                {"name": "达标奖", "threshold": 60000},
                {"name": "优秀奖", "threshold": 80000},
                {"name": "精英奖", "threshold": 120000},
                {"name": "卓越奖", "threshold": 160000}
            ]
        },
        "awards_mapping": {
            # 平台单奖励（复用上海4月配置）
            "基础奖": "200",
            "达标奖": "300",
            "优秀奖": "400",
            "精英奖": "800",
            "卓越奖": "1200",
            # 自引单奖励（新增）
            "红包": "50"
        },
        # 新增：自引单奖励配置
        "self_referral_rewards": {
            "enable": True,  # 启用自引单奖励
            "reward_type": "自引单",
            "reward_name": "红包",
            "deduplication_field": "projectAddress"  # 去重字段
            # 注意：奖励金额统一在awards_mapping中定义，避免重复配置
        }
    }
}
```

#### 5.1.3 配置获取函数升级
```python
def get_self_referral_config(config_key):
    """
    获取自引单奖励配置

    Args:
        config_key: 配置键，如 "SH-2025-09"

    Returns:
        dict: 自引单奖励配置
    """
    if config_key in REWARD_CONFIGS:
        return REWARD_CONFIGS[config_key].get("self_referral_rewards", {})
    else:
        # 默认配置（向后兼容）
        return {
            "enable": False,
            "reward_type": "",
            "reward_name": "",
            "deduplication_field": ""
        }
```

## 6. 实施计划

### 6.1 开发阶段
1. **Phase 1**: 数据结构升级和配置添加
2. **Phase 2**: 核心处理函数开发
3. **Phase 3**: 通知消息升级
4. **Phase 4**: 集成测试和验证

### 6.2 测试要点
- **数据分类正确性**: sourceType字段正确识别
- **自引单去重逻辑**: 项目地址唯一性验证
- **平台单逻辑保持**: 原有节节高奖励不受影响
- **通知消息格式**: 新格式正确显示统计数据
- **台账数据完整性**: 所有新增字段正确记录

### 6.3 风险评估
- **数据源变化风险**: 需要确认新字段的数据质量和API稳定性
- **逻辑复杂度增加**: 双轨处理可能增加出错概率，需要充分测试
- **向后兼容性**: 确保不影响其他月份的job和现有报表系统
- **字段映射风险**: API字段名与CSV字段名的映射需要准确无误
- **配置一致性风险**: 确保awards_mapping与self_referral_rewards配置保持一致

## 7. 技术实现补充

### 7.1 字段映射关系
```python
# API响应字段 -> CSV字段映射
FIELD_MAPPING = {
    # 原有字段保持不变
    '_id': '合同ID(_id)',
    'serviceHousekeeper': '管家(serviceHousekeeper)',
    # ... 其他原有字段 ...

    # 新增字段映射
    'serviceHousekeeperId': '管家ID(serviceHousekeeperId)',
    'sourceType': '工单类型(sourceType)',
    'contactsAddress': '客户联系地址(contactsAddress)',
    'projectAddress': '项目地址(projectAddress)'
}
```

### 7.2 辅助函数实现
```python
def create_performance_record(contract, reward_types, reward_names, housekeeper_data,
                            contract_count, source_type, project_address):
    """创建业绩数据记录，包含新增字段"""
    order_type_text = "自引单" if source_type == 1 else "平台单"

    return {
        # 原有字段...
        '合同ID(_id)': contract['合同ID(_id)'],
        '管家(serviceHousekeeper)': contract['管家(serviceHousekeeper)'],
        # ... 其他原有字段 ...

        # 新增字段
        '工单类型': order_type_text,
        '项目地址': project_address,
        '平台单累计数量': housekeeper_data['platform_count'],
        '平台单累计金额': housekeeper_data['platform_amount'],
        '自引单累计数量': housekeeper_data['self_referral_count'],
        '自引单累计金额': housekeeper_data['self_referral_amount']
    }

def preprocess_amount(amount_str):
    """金额预处理函数（复用现有逻辑）"""
    # 实现与现有上海通知函数一致的金额格式化
    pass

def preprocess_rate(rate_str):
    """转化率预处理函数（复用现有逻辑）"""
    # 实现与现有上海通知函数一致的转化率格式化
    pass
```

## 8. 后续优化建议

### 8.1 代码复用优化
- 抽象通用的合同处理逻辑
- 统一奖励计算接口
- 优化通知消息模板系统
- **配置驱动优化**：将自引单配置完全纳入REWARD_CONFIGS体系

### 8.2 监控增强
- 新增自引单处理监控指标
- 项目地址去重效果监控
- 双轨奖励发放准确性监控
- **配置一致性监控**：确保awards_mapping与self_referral_rewards配置一致

### 8.3 配置管理优化
- 考虑将配置外部化（JSON文件或数据库）
- 增加配置验证机制
- 支持配置热更新（如果需要）

---
*本设计文档已根据现有技术实现进行修订，确保技术方案的一致性和可行性。*
