# 测试指南 v1.0.1-stable

## 测试策略

### 核心测试重点
- **奖励计算**: 幸运数字奖、节节高奖逻辑验证
- **数据处理**: 合同数据转换和重复处理
- **文件操作**: CSV文件读写和状态管理
- **通知发送**: 消息生成和发送流程

### 测试方法
- **单任务测试**: 在main.py中取消注释特定任务
- **手动验证**: 检查生成的CSV文件和日志
- **功能测试**: 验证奖励计算和通知发送

## 手动测试

### 基本测试方法
在 `main.py` 中取消注释相应任务进行单独测试：

```python
# 单独测试任务（在main.py第92-97行）
# generate_daily_service_report()
# check_technician_status()
# signing_and_sales_incentive_may_beijing()
# signing_and_sales_incentive_apr_beijing()
# signing_and_sales_incentive_may_shanghai()
```

### 测试步骤
1. **备份现有数据**
```bash
copy state\PerformanceData-BJ-May.csv state\PerformanceData-BJ-May.csv.backup
```

2. **清理测试数据**
```bash
del state\ContractData-*.csv
del state\send_status_*.json
```

3. **执行测试**
```bash
python main.py
```

4. **验证结果**
- 检查 `state/PerformanceData-*.csv` 文件
- 查看 `logs/app.log` 日志
- 验证通知发送状态

## 数据验证

### CSV文件检查
```python
import pandas as pd

# 读取业绩数据
df = pd.read_csv('state/PerformanceData-BJ-May.csv')

# 检查数据完整性
print(f"总记录数: {len(df)}")
print(f"有奖励的记录: {len(df[df['激活奖励状态'] == 1])}")
print(f"奖励类型分布: {df['奖励类型'].value_counts()}")
```

### 奖励计算验证
```python
# 验证幸运数字奖励
lucky_rewards = df[df['奖励类型'].str.contains('幸运数字', na=False)]
print(f"幸运数字奖励数量: {len(lucky_rewards)}")

# 验证节节高奖励
tiered_rewards = df[df['奖励类型'].str.contains('节节高', na=False)]
print(f"节节高奖励数量: {len(tiered_rewards)}")
```

## 功能测试

### 北京5月活动测试
```python
# 测试配置
campaign_config = REWARD_CONFIGS["BJ-2025-05"]
print(f"幸运数字: {campaign_config['lucky_number']}")
print(f"最低合同数: {campaign_config['tiered_rewards']['min_contracts']}")

# 测试奖励阈值
for tier in campaign_config['tiered_rewards']['tiers']:
    print(f"{tier['name']}: {tier['threshold']}")
```

### 上海5月活动测试
```python
# 测试上海特殊配置
campaign_config = REWARD_CONFIGS["SH-2025-05"]
print(f"最低合同数: {campaign_config['tiered_rewards']['min_contracts']}")  # 应该是5
print(f"奖励档数: {len(campaign_config['tiered_rewards']['tiers'])}")  # 应该是4档
```

## 日志分析

### 日志文件位置
- `logs/app.log` - 主应用日志
- `logs/send_messages.log` - 消息发送日志

### 关键日志信息
```bash
# 查看最近的处理日志
tail -n 50 logs/app.log | grep "BEIJING 2025 5月"

# 查看错误日志
grep "ERROR" logs/app.log

# 查看通知发送日志
grep "notify_awards" logs/app.log
```

### 日志分析示例
```
2025-05-17 10:30:01 - INFO - BEIJING 2025 5月, Job started ...
2025-05-17 10:30:02 - INFO - BEIJING 2025 5月, Request sent
2025-05-17 10:30:05 - INFO - Starting data processing with 156 existing contract IDs.
2025-05-17 10:30:08 - INFO - BEIJING 2025 5月, Data processed
2025-05-17 10:30:10 - INFO - BEIJING 2025 5月, Data archived
2025-05-17 10:30:10 - INFO - BEIJING 2025 5月, Job ended
```

## 状态文件检查

### 发送状态文件
```python
import json

# 检查发送状态
with open('state/send_status_bj_may.json', 'r', encoding='utf-8') as f:
    status = json.load(f)

print(f"已发送通知数量: {len(status)}")
for contract_id, info in status.items():
    print(f"合同 {contract_id}: {info}")
```

### 技师状态文件
```python
# 检查技师状态记录
with open('state/technician_status_record.json', 'r', encoding='utf-8') as f:
    tech_status = json.load(f)

print(f"技师状态记录数: {len(tech_status)}")
```

## 常见问题排查

### 数据处理问题
1. **重复合同处理**
   - 检查 `existing_contract_ids` 是否正确加载
   - 验证合同ID去重逻辑

2. **奖励计算错误**
   - 检查幸运数字计算: `contract_number % 10`
   - 验证累计金额和合同数量
   - 确认奖励阈值配置

3. **文件读写问题**
   - 确保state目录存在
   - 检查文件权限
   - 验证CSV文件格式

### 通知发送问题
1. **Webhook失效**
   - 检查企业微信机器人配置
   - 验证Webhook URL有效性
   - 测试消息格式

2. **消息格式错误**
   - 检查消息模板
   - 验证特殊字符处理
   - 确认消息长度限制

### API调用问题
1. **Metabase连接失败**
   - 检查用户名密码
   - 验证API地址
   - 确认网络连接

2. **数据格式变化**
   - 检查API返回数据结构
   - 验证字段名称
   - 确认数据类型

## 测试数据准备

### 模拟测试数据
```python
# 创建测试合同数据
test_contracts = [
    {
        '合同ID(_id)': 'test_001',
        '活动城市(province)': '110000',
        '管家(serviceHousekeeper)': '测试管家',
        '合同金额(adjustRefundMoney)': '25000.0',
        '工单编号(serviceAppointmentNum)': 'TEST001',
        # ... 其他必要字段
    }
]
```

### 测试环境隔离
1. **使用测试配置**
   - 修改API地址指向测试环境
   - 使用测试Webhook地址
   - 设置测试文件路径

2. **数据备份**
   - 备份生产数据文件
   - 使用独立的测试目录
   - 避免影响生产环境

---

**测试版本**: v1.0.1-stable | **更新日期**: 2025-05-17 | **状态**: 生产稳定
