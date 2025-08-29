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

### 2.1 新增组件
```
signing_and_sales_incentive_sep_shanghai()
├── 数据获取层: send_request_with_managed_session() [升级]
├── 数据处理层: process_data_shanghai_sep() [新建]
├── 平台单奖励计算: determine_rewards_apr_shanghai_generic() [复用]
├── 自引单奖励计算: determine_self_referral_rewards() [新建]
├── 通知发送层: notify_awards_shanghai_sep() [新建]
└── 文件管理层: archive_file() [复用]
```

### 2.2 统一订单处理流程
```
Metabase API → CSV临时文件 → 订单分类处理 → 差异化奖励计算 → 统一业绩数据文件 → 统一通知发送 → 文件归档
                    ↓
            订单类型识别 (sourceType)
                ↓
        [平台单订单] + [自引单订单]
                ↓         ↓
        节节高奖励规则  项目地址去重规则
                ↓         ↓
        写入统一的奖励类型/名称到业绩数据文件
                ↓
        统一从业绩数据文件读取 → 配置获取金额 → 生成通知消息
```

### 2.3 详细数据转换流程
```
API数组数据 → CSV字典数据 → 分类处理 → 奖励计算 → 业绩数据文件 → 通知发送
     ↓              ↓           ↓         ↓           ↓           ↓
  原始字段      标准化字段   平台单/自引单  奖励类型/名称  完整记录    读取奖励信息
                                ↓         ↓
                            节节高奖励  自引单红包
                                ↓         ↓
                            写入CSV    写入CSV
                                ↓
                        统一从CSV读取 → 配置获取金额 → 生成消息
```

**数据流说明**：
1. **数据处理阶段**：计算奖励后将奖励类型和名称写入业绩数据文件
2. **通知发送阶段**：从业绩数据文件读取奖励信息，通过awards_mapping获取金额
3. **关键原则**：业绩数据文件是奖励信息的唯一数据源

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
- `管家累计金额` → **语义变更**：现在专指平台单累计金额
- `管家累计单数` → **语义变更**：现在专指平台单累计单数
- 其他27个字段保持原有含义不变

**新增字段（6个）**：
- `工单类型`: 自引单/平台单，从sourceType字段转换而来 (String)
- `项目地址`: 项目地址，从API新增字段projectAddress获取 (String)
- `平台单累计数量`: 管家平台单累计数量，与`管家累计单数`数值相同 (Integer)
- `平台单累计金额`: 管家平台单累计金额，与`管家累计金额`数值相同 (Float)
- `自引单累计数量`: 管家自引单累计数量 (Integer)
- `自引单累计金额`: 管家自引单累计金额 (Float)

**重要说明**：
1. **无字段删除**：为保证数据完整性和向后兼容，不删除任何原有字段
2. **语义重定义**：`管家累计金额`和`管家累计单数`现在专指平台单数据
3. **数据冗余**：`平台单累计数量`与`管家累计单数`数值相同，`平台单累计金额`与`管家累计金额`数值相同
4. **统一奖励字段**：平台单和自引单都使用原有的`奖励类型`和`奖励名称`字段，无需新增专用字段
5. **渐进迁移**：后续版本可考虑逐步废弃冗余字段，当前版本保持兼容性优先

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

    # 2. 统一遍历所有订单
    for contract in contract_data:
        source_type = contract['工单类型(sourceType)']

        # 根据订单类型应用不同的奖励规则
        if source_type == 1:
            # 自引单订单：应用项目地址去重奖励规则
            apply_self_referral_reward_rules(contract, housekeeper_contracts, config_key)
        else:
            # 平台单订单：应用节节高奖励规则
            apply_platform_reward_rules(contract, housekeeper_contracts, config_key)

    # 3. 生成统一的业绩数据记录
    # 4. 返回处理结果
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

### 4.3 统一通知发送 - notify_awards_shanghai_sep()
**新建函数，基于 notify_awards_shanghai_generate_message_march() 升级**

**核心逻辑**：
1. 群通知：发送订单签约喜报到运营群（包含不同订单类型的统计）
2. 个人奖励通知：发送给活动管理员（满浩浩）
3. 统一从业绩数据文件读取所有订单的奖励信息
4. 使用配置驱动的奖励金额映射，无需区分订单类型

**实现逻辑**：
```python
def notify_awards_shanghai_sep(performance_data_filename, status_filename, contract_data):
    # 读取业绩数据文件（与原有逻辑一致）
    records = get_all_records_from_csv(performance_data_filename)

    # 使用配置化的奖励映射（上海9月配置）
    awards_mapping = get_awards_mapping("SH-2025-09")

    for record in records:
        if record['是否发送通知'] == 'N':
            # 生成群通知消息（包含平台单和自引单统计）
            msg = generate_group_notification_message(record)
            create_task('send_wecom_message', WECOM_GROUP_NAME_SH_SEP, msg)

            # 生成个人奖励消息（统一处理）
            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "SH")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_SH_SEP, jiangli_msg)
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

🌻 个人累计签约平台单第 {个人平台单数量} 单， 个人累计签约自引单第 {个人自引单数量} 单。
🌻 个人累计签约平台单金额 {平台单金额} 元，自引单金额{自引单金额}元

🌻 个人平台单转化率 {转化率}%，

👊 {奖励状态描述} 🎉🎉🎉。
```

**数据来源**：
- 平台单/自引单类型：从业绩数据文件的 `工单类型` 字段获取
- 统计数据：从业绩数据文件的新增统计字段获取

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
            "reward_amount": 50,
            "deduplication_field": "projectAddress"  # 去重字段
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
            "reward_amount": 0,
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
- **数据源变化风险**: 需要确认新字段的数据质量
- **逻辑复杂度增加**: 双轨处理可能增加出错概率
- **向后兼容性**: 确保不影响其他月份的job
- **字段语义变更风险**: `管家累计金额`和`管家累计单数`语义变更可能影响现有报表和分析
- **数据冗余风险**: 新增的平台单字段与原有字段数据重复，需要确保数据一致性

## 7. 后续优化建议

### 7.1 代码复用优化
- 抽象通用的合同处理逻辑
- 统一奖励计算接口
- 优化通知消息模板系统
- **配置驱动优化**：将自引单配置完全纳入REWARD_CONFIGS体系

### 7.2 监控增强
- 新增自引单处理监控指标
- 项目地址去重效果监控
- 双轨奖励发放准确性监控
- **配置一致性监控**：确保awards_mapping与self_referral_rewards配置一致

### 7.3 配置管理优化
- 考虑将配置外部化（JSON文件或数据库）
- 增加配置验证机制
- 支持配置热更新（如果需要）

---
*本设计文档遵循KISS原则，专注核心升级要点。详细实现请参考现有代码模式。*
