# 手动验证指南

## 🎯 目标
在您的电脑上手动执行新旧架构，对比验证结果一致性。

## 📋 准备工作

```bash
# 1. 清理环境
rm -f performance_data_*.csv
rm -f state/PerformanceData-*.csv  
rm -f performance_data.db

# 2. 确保在项目根目录
pwd  # 应该显示项目根路径
```

## 🏢 执行旧架构

```bash
# 运行旧架构北京9月
python -c "
import sys
sys.path.insert(0, '.')
from jobs import signing_and_sales_incentive_sep_beijing
print('🏢 开始执行旧架构...')
signing_and_sales_incentive_sep_beijing()
print('✅ 旧架构执行完成')
"

# 检查输出
ls state/PerformanceData-BJ-Sep.csv
wc -l state/PerformanceData-BJ-Sep.csv
```

## 🆕 执行新架构

```bash
# 运行新架构北京9月（数据存储到数据库）
python -c "
import sys
sys.path.insert(0, '.')
from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
print('🆕 开始执行新架构...')
result = signing_and_sales_incentive_sep_beijing_v2()
print(f'✅ 新架构执行完成，处理了{len(result)}条记录')
print('📊 数据已保存到数据库: performance_data.db')
"

# 检查数据库
ls performance_data.db
```

## 📊 导出新架构数据进行对比

```bash
# 从数据库导出CSV（兼容旧格式）
python scripts/export_database_to_csv.py --activity BJ-SEP --compatible

# 检查导出文件
ls performance_data_BJ-SEP_*.csv
wc -l performance_data_BJ-SEP_*.csv
```

## 🔍 对比验证

```bash
# 设置文件变量
OLD_FILE="state/PerformanceData-BJ-Sep.csv"
NEW_FILE=$(ls performance_data_BJ-SEP_*.csv | head -1)

echo "旧架构文件: $OLD_FILE"
echo "新架构文件: $NEW_FILE"

# 基础对比
echo "=== 记录数量对比 ==="
wc -l $OLD_FILE $NEW_FILE

echo "=== 字段对比 ==="
head -1 $OLD_FILE
head -1 $NEW_FILE

echo "=== 奖励统计对比 ==="
echo "旧架构奖励数:"
grep -c "接好运\|达标奖\|优秀奖" $OLD_FILE
echo "新架构奖励数:"
grep -c "接好运\|达标奖\|优秀奖" $NEW_FILE
```

## ✅ 预期结果

基于我们的验证，您应该看到：

- **记录数量**: 都是1055条
- **合同金额总和**: 6,928,792.94元
- **奖励记录**: 34条（31个接好运+6个达标奖+1个优秀奖）
- **管家数量**: 53个

## 🔧 详细验证（可选）

```python
# 创建 compare.py 文件
import pandas as pd

old_df = pd.read_csv('state/PerformanceData-BJ-Sep.csv')
new_df = pd.read_csv('performance_data_BJ-SEP_20250922_XXXXXX.csv')  # 替换实际文件名

print(f"记录数: 旧{len(old_df)} vs 新{len(new_df)}")
print(f"合同金额: 旧{old_df['合同金额(adjustRefundMoney)'].sum():.2f} vs 新{new_df['合同金额(adjustRefundMoney)'].sum():.2f}")

old_rewards = len(old_df[old_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
new_rewards = len(new_df[new_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
print(f"奖励数: 旧{old_rewards} vs 新{new_rewards}")
```

```bash
# 运行详细对比
python compare.py
```

## 🚨 注意事项

1. **数据库清理**: 每次运行新架构前确保删除`performance_data.db`
2. **网络连接**: 确保能访问Metabase API
3. **文件名**: 新架构导出的文件名包含时间戳，需要替换实际文件名
4. **根目录清洁**: 新架构默认不生成CSV，保持根目录清洁

## 💡 工具使用

```bash
# 查看数据库中的活动
python scripts/export_database_to_csv.py --list

# 导出特定活动
python scripts/export_database_to_csv.py --activity BJ-SEP --output my_export.csv

# 导出兼容格式
python scripts/export_database_to_csv.py --activity BJ-SEP --compatible
```

---

**核心理念**: 新架构数据库优先，按需导出CSV，保持架构纯粹性。
