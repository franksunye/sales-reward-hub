# 集成测试执行指南

**目标**: 提供完整的端到端集成测试执行步骤  
**适用**: 9月份Job新架构验证  
**测试类型**: 真实数据集成测试（模拟手工测试）

## 🎯 测试原则

### 端到端测试要求
1. **环境隔离**: 每次测试前必须清空数据库
2. **真实数据**: 使用生产环境的Metabase API数据
3. **完整流程**: 从数据获取到CSV生成的全流程
4. **严格对比**: 逐字段对比新旧系统输出
5. **零容忍**: 任何差异都必须分析和修复

### 手工测试模拟
- **数据库清理**: 模拟全新环境部署
- **基准建立**: 模拟旧系统的标准输出
- **逐步验证**: 模拟手工检查每个字段
- **完整记录**: 模拟测试文档和报告

## 🛠️ 必要工具准备

### 环境管理工具
```bash
# 环境验证工具
python scripts/environment_validator.py --activity BJ-SEP

# 数据库清理工具
python scripts/database_cleanup.py --activity BJ-SEP

# 字段验证工具
python scripts/detailed_field_validator.py --job BJ-SEP --baseline baseline.csv --current current.csv
```

### 目录结构准备
```
workspace/
├── baseline/                 # 基准数据目录
│   ├── BJ-SEP/
│   └── SH-SEP/
├── reports/                  # 验证报告目录
├── logs/                     # 测试日志目录
└── temp/                     # 临时文件目录
```

## 📋 标准执行流程

### 阶段0：预备检查（每次测试前必须）

#### 0.1 环境验证
```bash
# 验证环境是否准备就绪
python scripts/environment_validator.py --activity BJ-SEP --report reports/env_validation.md

# 检查结果，确保所有项目都是✅状态
```

#### 0.2 数据库清理（关键步骤）
```bash
# 清空指定活动的数据
python scripts/database_cleanup.py --activity BJ-SEP

# 验证清理结果
python scripts/environment_validator.py --activity BJ-SEP
```

#### 0.3 目录准备
```bash
# 创建必要目录
mkdir -p baseline/BJ-SEP reports logs temp

# 清理旧的临时文件
rm -f performance_data_BJ-SEP_*.csv
rm -f logs/integration_test_*.log
```

### 阶段1：基准数据获取（关键）

#### 1.1 旧系统环境准备
- **重要**: 确保旧系统也使用干净的数据库
- **重要**: 确保旧系统使用相同的API数据源
- **重要**: 记录旧系统的执行环境和配置

#### 1.2 执行旧系统
```bash
# 运行旧系统（具体命令根据旧系统而定）
# 例如：python old_system/beijing_sep_job.py

# 记录执行结果
# - 处理记录数
# - 执行时间
# - 生成的文件
```

#### 1.3 收集基准数据
```bash
# 保存基准CSV文件
cp performance_data_BJ-SEP_*.csv baseline/BJ-SEP/performance_data_BJ-SEP_baseline.csv

# 保存基准数据库状态（如果适用）
sqlite3 performance_data.db ".dump performance_records" > baseline/BJ-SEP/baseline_db_dump.sql

# 保存基准通知数据（如果适用）
sqlite3 performance_data.db ".dump notification_queue" > baseline/BJ-SEP/baseline_notifications.sql
```

#### 1.4 基准数据验证
```bash
# 验证基准数据完整性
python scripts/baseline_data_validator.py --file baseline/BJ-SEP/performance_data_BJ-SEP_baseline.csv --activity BJ-SEP
```

### 阶段2：新系统执行

#### 2.1 环境再次确认
```bash
# 确认数据库为空
python scripts/environment_validator.py --activity BJ-SEP

# 如果不为空，重新清理
python scripts/database_cleanup.py --activity BJ-SEP
```

#### 2.2 执行新系统
```bash
# 运行新架构集成测试
python integration_test_september_jobs.py --beijing-only

# 或者直接运行新系统Job
python -c "
from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
records = signing_and_sales_incentive_sep_beijing_v2()
print(f'处理了 {len(records)} 条记录')
"
```

#### 2.3 收集测试数据
```bash
# 保存新系统生成的CSV
cp performance_data_BJ-SEP_*.csv temp/performance_data_BJ-SEP_current.csv

# 导出数据库状态
sqlite3 performance_data.db "SELECT * FROM performance_records WHERE activity_code='BJ-SEP'" > temp/current_db_records.csv

# 导出通知队列
sqlite3 performance_data.db "SELECT * FROM notification_queue WHERE activity_code='BJ-SEP'" > temp/current_notifications.csv
```

### 阶段3：详细验证

#### 3.1 字段级验证
```bash
# 执行详细字段对比
python scripts/detailed_field_validator.py \
  --job BJ-SEP \
  --baseline baseline/BJ-SEP/performance_data_BJ-SEP_baseline.csv \
  --current temp/performance_data_BJ-SEP_current.csv \
  --output reports/BJ-SEP_field_validation_$(date +%Y%m%d_%H%M%S).md
```

#### 3.2 业务逻辑验证
```bash
# 执行业务逻辑专项检查
python scripts/business_logic_checker.py \
  --job BJ-SEP \
  --baseline baseline/BJ-SEP/ \
  --current temp/ \
  --output reports/BJ-SEP_business_logic_$(date +%Y%m%d_%H%M%S).md
```

#### 3.3 性能对比
```bash
# 执行性能对比
python scripts/performance_comparator.py \
  --job BJ-SEP \
  --baseline-log logs/baseline_execution.log \
  --current-log logs/integration_test_*.log \
  --output reports/BJ-SEP_performance_$(date +%Y%m%d_%H%M%S).md
```

### 阶段4：结果分析

#### 4.1 验证报告分析
- 检查所有验证报告
- 记录所有发现的差异
- 分类差异的严重程度
- 制定修复计划

#### 4.2 差异处理原则
- **关键字段差异**: 立即停止，必须修复
- **业务逻辑差异**: 高优先级修复
- **格式差异**: 中优先级修复
- **性能差异**: 低优先级，可接受范围内

#### 4.3 修复验证
- 修复问题后，从阶段0重新开始
- 确保修复不引入新问题
- 记录修复过程和结果

## ⚠️ 关键注意事项

### 数据库清理的重要性
1. **每次测试前必须清理**: 确保测试环境干净
2. **验证清理结果**: 确认相关表为空
3. **记录清理过程**: 便于问题追踪

### 基准数据的重要性
1. **基准数据质量**: 基准数据必须是正确的
2. **环境一致性**: 新旧系统必须使用相同的数据源
3. **版本控制**: 基准数据需要版本管理

### 验证的严格性
1. **零容忍原则**: 任何差异都必须解释和修复
2. **完整性检查**: 不能遗漏任何字段或记录
3. **重复验证**: 修复后必须重新完整验证

### 文档记录
1. **完整日志**: 记录每个步骤的执行结果
2. **差异记录**: 详细记录所有发现的差异
3. **修复记录**: 记录修复过程和验证结果

## 📊 成功标准

### 验证通过标准
- **字段一致性**: 99.9%以上字段完全一致
- **业务逻辑**: 100%业务逻辑结果一致
- **数据完整性**: 无遗漏、无重复、无错误
- **性能要求**: 处理时间在可接受范围内

### 测试完成标准
- **零差异**: 所有关键差异已修复
- **文档完整**: 所有测试过程已记录
- **可重复**: 测试结果可重复验证
- **可部署**: 新系统可安全部署

## 🚨 常见问题和解决方案

### 数据库清理问题
- **问题**: 清理后仍有数据
- **解决**: 检查SQL语句，确认activity_code正确

### API连接问题
- **问题**: API连接失败
- **解决**: 检查网络、session、配置文件

### 字段差异问题
- **问题**: 大量字段不匹配
- **解决**: 检查字段映射、数据类型、精度设置

### 性能问题
- **问题**: 新系统明显慢于旧系统
- **解决**: 分析SQL查询、API调用、算法复杂度

---

**重要提醒**: 集成测试是确保新系统质量的关键步骤，必须严格按照流程执行，不能省略任何步骤。
