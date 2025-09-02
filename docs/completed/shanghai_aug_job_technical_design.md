# 上海8月签约激励Job技术设计文档

## 文档信息
- **Job名称**: `signing_and_sales_incentive_aug_shanghai()`
- **创建日期**: 2025-08-29
- **版本**: v1.0
- **状态**: 生产运行

## 1. 概述

### 1.1 功能目的
处理上海地区2025年8月的签约和销售激励活动，实现自动化的合同数据获取、奖励计算和通知发送。

### 1.2 业务价值
- 自动化管家奖励计算，减少人工错误
- 实时通知签约成果，提升团队士气
- 数据归档管理，支持后续分析

### 1.3 核心特性
- 复用4月份成熟的奖励规则
- 禁用幸运数字奖励，专注节节高体系
- 支持管家+服务商唯一性识别
- 增量处理，避免重复计算

## 2. 技术架构

### 2.1 主要组件
```
signing_and_sales_incentive_aug_shanghai()
├── 数据获取层: send_request_with_managed_session()
├── 数据处理层: process_data_shanghai_apr()
├── 奖励计算层: determine_rewards_apr_shanghai_generic()
├── 通知发送层: notify_awards_shanghai_generate_message_march()
└── 文件管理层: archive_file()
```

### 2.2 数据流向
```
Metabase API → CSV临时文件 → 数据处理 → 奖励计算 → 通知发送 → 文件归档
```

## 3. 核心流程

### 3.1 主流程步骤
1. **数据获取**: 从Metabase API获取合同数据
2. **数据保存**: 保存原始数据到临时CSV文件
3. **数据读取**: 读取合同数据和历史奖励记录
4. **数据处理**: 计算管家累计数据和奖励
5. **通知发送**: 发送微信群和个人通知
6. **文件归档**: 归档临时文件到archive目录

### 3.2 关键处理逻辑

#### 3.2.1 管家数据结构
```python
housekeeper_contracts[unique_key] = {
    'count': 0,                    # 合同数量
    'total_amount': 0,             # 累计金额
    'performance_amount': 0,       # 业绩金额
    'awarded': []                  # 已获得奖励列表
}
```

#### 3.2.2 奖励计算规则
- **最低门槛**: 5个合同才能获得节节高奖励
- **奖励等级**: 基础奖(4万) → 达标奖(8万) → 卓越奖(15万)
- **配置标识**: "SH-2025-04" (复用4月配置)
- **幸运奖**: 已禁用

#### 3.2.3 唯一性识别
使用 `管家名称_服务商名称` 作为唯一标识，避免同名管家冲突。

## 4. 配置说明

### 4.1 核心配置项
```python
# API配置
API_URL_SH_AUG = METABASE_URL + "/api/card/1801/query"

# 文件路径
TEMP_CONTRACT_DATA_FILE_SH_AUG = 'state/ContractData-SH-Aug.csv'
PERFORMANCE_DATA_FILENAME_SH_AUG = 'state/PerformanceData-SH-Aug.csv'
STATUS_FILENAME_SH_AUG = 'state/send_status_sh_aug.json'

# 通知配置
WECOM_GROUP_NAME_SH_AUG = '（上海）运营群'
CAMPAIGN_CONTACT_SH_AUG = '满浩浩'
```

### 4.2 奖励配置
使用通用奖励配置系统，配置键为 "SH-2025-04"。

## 5. 依赖关系

### 5.1 核心模块依赖
- `modules.request_module`: API请求管理
- `modules.data_processing_module`: 数据处理和奖励计算
- `modules.notification_module`: 通知发送
- `modules.file_utils`: 文件操作
- `modules.data_utils`: 数据工具函数

### 5.2 关键函数依赖
- `send_request_with_managed_session()`: 带会话管理的API请求
- `process_data_shanghai_apr()`: 上海4月数据处理逻辑
- `determine_rewards_apr_shanghai_generic()`: 通用奖励计算
- `get_unique_housekeeper_award_list()`: 获取管家历史奖励
- `notify_awards_shanghai_generate_message_march()`: 上海通知发送

## 6. 数据结构

### 6.1 API响应数据结构
从Metabase API获取的原始数据格式：
```json
{
  "data": {
    "rows": [
      [
        "contract_id_001",           // 合同ID(_id)
        "310000",                    // 活动城市(province)
        "GD2024080001",             // 工单编号(serviceAppointmentNum)
        "已完成",                    // Status
        "张三",                      // 管家(serviceHousekeeper)
        "YHWX-SH-2024080001",       // 合同编号(contractdocNum)
        "15000.0",                  // 合同金额(adjustRefundMoney)
        "15000.0",                  // 支付金额(paidAmount)
        "0.0",                      // 差额(difference)
        "已签约",                    // State
        "2025-08-15T10:30:00.000+08:00", // 创建时间(createTime)
        "上海英森防水工程有限公司",    // 服务商(orgName)
        "2025-08-15T14:20:00.000+08:00", // 签约时间(signedDate)
        "10000.0",                  // Doorsill
        "线上支付",                  // 款项来源类型(tradeIn)
        "0.85",                     // 转化率(conversion)
        "18500"                     // 平均客单价(average)
      ]
    ]
  }
}
```

### 6.2 CSV文件数据结构

#### 6.2.1 原始合同数据文件 (ContractData-SH-Aug.csv)
```csv
合同ID(_id),活动城市(province),工单编号(serviceAppointmentNum),Status,管家(serviceHousekeeper),合同编号(contractdocNum),合同金额(adjustRefundMoney),支付金额(paidAmount),差额(difference),State,创建时间(createTime),服务商(orgName),签约时间(signedDate),Doorsill,款项来源类型(tradeIn),转化率(conversion),平均客单价(average)
```

**字段说明**：
- `合同ID(_id)`: 唯一合同标识符 (String)
- `活动城市(province)`: 城市代码，上海为"310000" (String)
- `工单编号(serviceAppointmentNum)`: 服务工单编号 (String)
- `Status`: 工单状态 (String)
- `管家(serviceHousekeeper)`: 管家姓名 (String)
- `合同编号(contractdocNum)`: 业务合同编号 (String)
- `合同金额(adjustRefundMoney)`: 合同金额 (Float)
- `支付金额(paidAmount)`: 已支付金额 (Float)
- `差额(difference)`: 金额差额 (Float)
- `State`: 合同状态 (String)
- `创建时间(createTime)`: ISO格式时间戳 (String)
- `服务商(orgName)`: 服务商公司名称 (String)
- `签约时间(signedDate)`: ISO格式时间戳 (String)
- `Doorsill`: 门槛金额 (Float)
- `款项来源类型(tradeIn)`: 支付方式 (String)
- `转化率(conversion)`: 转化率 (Float)
- `平均客单价(average)`: 平均客单价 (Float)

#### 6.2.2 业绩数据文件 (PerformanceData-SH-Aug.csv)
```csv
活动编号,合同ID(_id),活动城市(province),工单编号(serviceAppointmentNum),Status,管家(serviceHousekeeper),合同编号(contractdocNum),合同金额(adjustRefundMoney),支付金额(paidAmount),差额(difference),State,创建时间(createTime),服务商(orgName),签约时间(signedDate),Doorsill,款项来源类型(tradeIn),转化率(conversion),平均客单价(average),活动期内第几个合同,管家累计金额,管家累计单数,奖金池,计入业绩金额,激活奖励状态,奖励类型,奖励名称,是否发送通知,备注,登记时间
```

**新增计算字段说明**：
- `活动编号`: 活动标识，固定为"SH-AUG" (String)
- `活动期内第几个合同`: 活动期内合同序号 (Integer)
- `管家累计金额`: 管家累计签约金额 (Float)
- `管家累计单数`: 管家累计合同数量 (Integer)
- `奖金池`: 奖金池金额 (Float)
- `计入业绩金额`: 计入业绩的金额 (Float)
- `激活奖励状态`: 是否激活奖励 (0/1) (Integer)
- `奖励类型`: 奖励类型，如"节节高" (String)
- `奖励名称`: 具体奖励名称，如"基础奖" (String)
- `是否发送通知`: 通知发送状态 (Y/N) (String)
- `备注`: 奖励计算备注信息 (String)
- `登记时间`: 数据处理时间戳 (String)

### 6.3 内存数据结构

#### 6.3.1 管家合同数据结构
```python
housekeeper_contracts = {
    "张三_上海英森防水工程有限公司": {
        'count': 3,                    # 合同数量
        'total_amount': 45000.0,       # 累计金额
        'performance_amount': 45000.0,  # 业绩金额
        'awarded': ["基础奖"]          # 已获得奖励列表
    }
}
```

#### 6.3.2 奖励计算返回结构
```python
# determine_rewards_apr_shanghai_generic() 返回值
(
    "节节高",                    # reward_types (String)
    "基础奖",                    # reward_names (String)
    "距离 达标奖 还需 35000 元"   # next_reward_gap (String)
)
```

### 6.4 通知数据结构

#### 6.4.1 发送状态文件 (send_status_sh_aug.json)
```json
{
  "contract_id_001": "发送成功",
  "contract_id_002": "发送失败",
  "contract_id_003": "待发送"
}
```

#### 6.4.2 通知消息格式
**群通知消息**：
```
🎉 恭喜管家 张三 签约成功！
合同编号：YHWX-SH-2024080001
合同金额：15000 元
服务商：上海英森防水工程有限公司

👊 距离 达标奖 还需 35000 元。
```

**个人奖励消息**：
```
🎉 恭喜获得奖励！
奖励类型：节节高
奖励名称：基础奖
奖励金额：200 元
```

### 6.5 数据转换流程
```
API数组数据 → CSV字典数据 → 内存处理 → 增强CSV数据 → 通知数据
     ↓              ↓           ↓           ↓           ↓
  原始字段      标准化字段    计算字段    完整记录    消息格式
```

## 7. 错误处理

### 7.1 异常场景
- API请求失败
- 数据格式异常
- 文件读写错误
- 通知发送失败

### 7.2 处理策略
- 使用logging记录详细错误信息
- 在main.py中捕获异常并记录traceback
- 失败时不影响其他job的执行

## 8. 测试要点

### 8.1 单元测试
- 奖励计算逻辑正确性
- 数据处理完整性
- 配置加载正确性

### 8.2 集成测试
- 端到端流程验证
- Mock外部依赖测试
- 异常场景处理

### 8.3 关键测试场景
- 新管家首次签约
- 管家达到奖励阈值
- 重复合同处理
- 历史奖励继承

## 9. 运维说明

### 9.1 监控要点
- Job执行时间
- 处理的合同数量
- 发送的通知数量
- 错误日志监控

### 9.2 文件管理
- 临时文件自动归档到archive目录
- 状态文件持久化保存
- 日志文件定期清理

## 10. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2025-08-29 | 初始版本，复用4月奖励规则 |

---
*本文档遵循KISS原则，专注核心技术要点。如需更详细信息，请参考相关模块的代码注释。*
