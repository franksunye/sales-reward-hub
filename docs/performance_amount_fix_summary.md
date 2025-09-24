# 🔧 累计金额统计问题修复总结

## 问题描述

在数据库视图中发现了多个重要的统计错误：

- **问题字段**: 多个累计金额字段统计了所有合同，包括历史合同
- **错误行为**: `total_amount`, `performance_amount`, `platform_amount`, `self_referral_amount`, `avg_contract_amount` 等
- **正确需求**: 累计金额统计仅计入新工单，不计入历史工单
- **业务逻辑**: 历史工单仅作为后台计算的逻辑数据，不参与前端的数据统计
- **影响范围**: 北京和上海的所有累计金额统计都受到影响

## 根本原因

在 `modules/core/database_schema.sql` 中的三个视图定义存在问题：

1. **housekeeper_stats 视图** - 多个累计金额字段未过滤历史合同
2. **project_stats 视图** - 累计金额字段未过滤历史合同
3. **activity_stats 视图** - 累计金额字段未过滤历史合同

这些视图在计算累计金额时没有过滤 `is_historical` 字段，导致历史合同被错误地计入前端统计。

## 修复方案

### 修改前
```sql
SUM(contract_amount) as total_amount
SUM(performance_amount) as performance_amount
SUM(CASE WHEN order_type = 'platform' THEN contract_amount ELSE 0 END) as platform_amount
AVG(contract_amount) as avg_contract_amount
```

### 修改后
```sql
SUM(CASE WHEN is_historical = FALSE THEN contract_amount ELSE 0 END) as total_amount
SUM(CASE WHEN is_historical = FALSE THEN performance_amount ELSE 0 END) as performance_amount
SUM(CASE WHEN order_type = 'platform' AND is_historical = FALSE THEN contract_amount ELSE 0 END) as platform_amount
AVG(CASE WHEN is_historical = FALSE THEN contract_amount ELSE NULL END) as avg_contract_amount
```

## 修复内容

### 1. 数据库Schema修复

**文件**: `modules/core/database_schema.sql`

- ✅ 修复 `housekeeper_stats` 视图的所有累计金额字段
  - `total_amount` (累计合同金额)
  - `performance_amount` (累计业绩金额)
  - `platform_amount` (平台单累计金额)
  - `self_referral_amount` (自引单累计金额)
- ✅ 修复 `project_stats` 视图的所有累计金额字段
  - `total_amount` (工单累计合同金额)
  - `performance_amount` (工单累计业绩金额)
- ✅ 修复 `activity_stats` 视图的所有累计金额字段
  - `total_amount` (活动总合同金额)
  - `total_performance_amount` (活动总业绩金额)
  - `avg_contract_amount` (平均合同金额)

### 2. 数据库迁移脚本

**文件**: `scripts/migrate_views_fix_performance_amount.py`

- ✅ 自动备份数据库
- ✅ 删除旧视图并创建修复后的视图
- ✅ 更新schema版本到 1.0.2
- ✅ 验证迁移结果
- ✅ 支持预览模式 (`--dry-run`)

### 3. 测试验证脚本

**文件**: `scripts/test_performance_amount_fix.py`

- ✅ 创建包含历史合同和新合同的测试数据
- ✅ 验证 `housekeeper_stats` 视图所有金额字段修复效果
- ✅ 验证 `project_stats` 视图所有金额字段修复效果
- ✅ 验证 `activity_stats` 视图所有金额字段修复效果

### 4. 视图验证工具

**文件**: `scripts/verify_views.py`

- ✅ 查看当前数据库中的视图定义
- ✅ 检查schema版本信息

## 测试结果

### 测试数据
- 张三：2个新合同(10000+15000，平台单) + 2个历史合同(20000+8000，平台单)
- 李四：1个新合同(12000，平台单)
- 王五：2个新合同(18000平台单+22000自引单，上海数据)

### 验证结果
```
管家统计视图: ✅ 通过
工单统计视图: ✅ 通过
活动统计视图: ✅ 通过

🎉 所有测试通过！所有累计金额字段修复成功
💡 现在所有累计金额统计只包含新工单，不包含历史工单
```

### 具体验证点
- ✅ 张三的总金额: 25000 (只统计新合同，排除历史合同的28000)
- ✅ 张三的业绩金额: 25000 (只统计新合同，排除历史合同的28000)
- ✅ 张三的平台单金额: 25000 (只统计新合同平台单)
- ✅ 历史工单的所有金额总和: 0 (正确排除)
- ✅ BJ-SEP活动总金额: 37000 (只统计新合同)
- ✅ BJ-SEP活动业绩金额: 37000 (只统计新合同)
- ✅ BJ-SEP平均合同金额: 12333.33 (基于新合同计算)

## 影响分析

### 北京 (BJ-SEP)
- **修复前**: 所有累计金额字段包含历史合同，数值偏高
- **修复后**: 所有累计金额字段只包含新工单，符合业务需求
- **具体影响**: 总金额、业绩金额、平台单金额等都更加准确
- **数据一致性**: 与代码中其他地方的逻辑保持一致

### 上海 (SH-SEP)
- **影响**: 无历史合同，修复对上海数据无影响
- **一致性**: 确保北京和上海使用相同的统计逻辑
- **双轨统计**: 平台单和自引单的累计金额统计更加准确

## 部署说明

### 对于现有数据库
1. 运行迁移脚本：
   ```bash
   python scripts/migrate_views_fix_performance_amount.py --db performance_data.db
   ```

2. 验证修复效果：
   ```bash
   python scripts/test_performance_amount_fix.py performance_data.db
   ```

### 对于新数据库
- 新创建的数据库会自动使用修复后的schema
- 无需额外操作

## 技术细节

### Schema版本管理
- **修复前版本**: 1.0.0
- **修复后版本**: 1.0.2
- **版本描述**: "Fix all amount calculations to exclude historical contracts"

### 向后兼容性
- ✅ 修复不影响现有代码逻辑
- ✅ 数据库表结构无变化
- ✅ 只修改视图定义，应用层无感知

### 性能影响
- ✅ 使用 CASE WHEN 条件，性能影响微乎其微
- ✅ 现有索引仍然有效
- ✅ 查询性能无明显变化

## 总结

这次修复解决了一个重要的业务逻辑错误，确保：

1. **数据准确性**: 所有累计金额统计符合业务需求，历史工单不参与前端统计
2. **逻辑一致性**: 视图统计与代码逻辑保持一致，北京和上海统一标准
3. **业务合规性**: 历史工单仅作为后台计算逻辑数据，不影响前端展示
4. **系统稳定性**: 修复过程安全，有完整的备份和验证
5. **可维护性**: 提供了完整的迁移和测试工具

修复已成功提交到 GitHub 的 `production-db-v2` 分支，可以安全部署到生产环境。
