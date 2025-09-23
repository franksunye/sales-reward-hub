# 手动验证指南

**版本**: v3.0
**更新日期**: 2025-09-23
**适用范围**: 北京和上海9月销售激励活动验证

## 🎯 目标
在您的本地环境手动执行新旧架构，对比验证结果一致性。支持北京和上海两个城市的完整验证流程。

## 📋 验证清单
- [ ] 北京9月 (BJ-SEP) 验证
- [ ] 上海9月 (SH-SEP) 验证

## 📋 准备工作

### 环境要求
- Python 3.7+
- 网络连接（访问Metabase API）
- 项目依赖已安装

### ⚠️ 实时数据验证说明
**重要**: 手工测试使用实时API数据，验证系统功能正常。

**预期的微小差异**（正常情况）:
- 记录数量: ±1-2条（数据更新延迟）
- 合同金额: 微小差异（新增合同）
- 奖励数量: 基于实时数据的正常变化

**需要关注的异常**:
- 大量数据缺失（>5%差异）
- 业务逻辑错误（奖励计算完全错误）
- 系统功能异常（无法生成文件、数据库错误）

### 清理环境
```bash
# 1. 清理所有输出文件
rm -f performance_data_*.csv
rm -f state/PerformanceData-*.csv
rm -f performance_data.db
rm -f tasks.db

# 2. 确保在项目根目录
pwd  # 应该显示项目根路径
ls modules/  # 应该能看到core目录

# 3. 验证Python环境
python --version
python -c "import pandas, sqlite3; print('依赖检查通过')"
```

## 🏢 北京9月验证 (BJ-SEP)

### 步骤1: 执行旧架构
```bash
echo "🏢 开始北京9月旧架构验证..."

# 运行旧架构北京9月
python -c "
import sys
sys.path.insert(0, '.')
from jobs import signing_and_sales_incentive_sep_beijing
print('🏢 开始执行旧架构北京9月...')
signing_and_sales_incentive_sep_beijing()
print('✅ 旧架构执行完成')
"

# 检查输出文件
echo "📊 检查旧架构输出:"
ls -la state/PerformanceData-BJ-Sep.csv
wc -l state/PerformanceData-BJ-Sep.csv
echo "旧架构文件大小: $(du -h state/PerformanceData-BJ-Sep.csv)"
```

### 步骤2: 执行新架构
```bash
echo "🆕 开始北京9月新架构验证..."

# 清理数据库（确保干净环境）
rm -f performance_data.db

# 运行新架构北京9月（数据存储到数据库）
python -c "
import sys
sys.path.insert(0, '.')
from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
print('🆕 开始执行新架构北京9月...')
result = signing_and_sales_incentive_sep_beijing_v2()
print(f'✅ 新架构执行完成，处理了{len(result)}条记录')
print('📊 数据已保存到数据库: performance_data.db')

# 统计奖励记录
reward_count = len([r for r in result if r.rewards])
print(f'🏆 获得奖励的记录: {reward_count}条')
"

# 检查数据库文件
echo "📊 检查新架构输出:"
ls -la performance_data.db
echo "数据库文件大小: $(du -h performance_data.db)"
```

### 步骤3: 导出新架构数据进行对比
```bash
echo "📊 导出新架构数据..."

# 从数据库导出CSV（兼容旧格式）
python scripts/export_database_to_csv.py --activity BJ-SEP --output beijing_new_output.csv

# 检查导出文件
echo "新架构导出文件: beijing_new_output.csv"
ls -la beijing_new_output.csv
wc -l beijing_new_output.csv
echo "新架构文件大小: $(du -h beijing_new_output.csv)"
```

### 步骤4: 北京对比验证
```bash
echo "🔍 开始北京9月对比验证..."

# 设置文件变量
OLD_BJ_FILE="state/PerformanceData-BJ-Sep.csv"
NEW_BJ_FILE="beijing_new_output.csv"

echo "旧架构文件: $OLD_BJ_FILE"
echo "新架构文件: $NEW_BJ_FILE"

# 基础对比
echo "=== 记录数量对比 ==="
wc -l $OLD_BJ_FILE $NEW_BJ_FILE

echo "=== 字段对比 ==="
echo "旧架构字段:"
head -1 $OLD_BJ_FILE
echo "新架构字段:"
head -1 $NEW_BJ_FILE

echo "=== 奖励统计对比 ==="
echo "旧架构奖励数:"
OLD_BJ_REWARDS=$(grep -c "接好运\|达标奖\|优秀奖" $OLD_BJ_FILE)
echo $OLD_BJ_REWARDS
echo "新架构奖励数:"
NEW_BJ_REWARDS=$(grep -c "接好运\|达标奖\|优秀奖" $NEW_BJ_FILE)
echo $NEW_BJ_REWARDS

# 验证结果
if [ "$OLD_BJ_REWARDS" -eq "$NEW_BJ_REWARDS" ]; then
    echo "✅ 北京9月奖励数量一致"
else
    echo "❌ 北京9月奖励数量不一致"
fi
```

## 🏙️ 上海9月验证 (SH-SEP)

### 步骤1: 执行旧架构
```bash
echo "🏙️ 开始上海9月旧架构验证..."



# 运行旧架构上海9月
python -c "
import sys
sys.path.insert(0, '.')
from jobs import signing_and_sales_incentive_sep_shanghai
print('🏙️ 开始执行旧架构上海9月...')
signing_and_sales_incentive_sep_shanghai()
print('✅ 旧架构执行完成')
"

# 检查输出文件
echo "📊 检查旧架构输出:"
ls -la state/PerformanceData-SH-Sep.csv
wc -l state/PerformanceData-SH-Sep.csv
echo "旧架构文件大小: $(du -h state/PerformanceData-SH-Sep.csv)"
```

### 步骤2: 执行新架构
```bash
echo "🆕 开始上海9月新架构验证..."

# 清理数据库（确保干净环境）
rm -f performance_data.db

# 运行新架构上海9月（支持双轨统计）
python -c "
import sys
sys.path.insert(0, '.')
from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
print('🆕 开始执行新架构上海9月...')
result = signing_and_sales_incentive_sep_shanghai_v2()
print(f'✅ 新架构执行完成，处理了{len(result)}条记录')
print('📊 数据已保存到数据库: performance_data.db')

# 统计奖励记录
reward_count = len([r for r in result if r.rewards])
print(f'🏆 获得奖励的记录: {reward_count}条')
"

# 检查数据库文件
echo "📊 检查新架构输出:"
ls -la performance_data.db
echo "数据库文件大小: $(du -h performance_data.db)"
```

### 步骤3: 导出新架构数据进行对比
```bash
echo "📊 导出上海新架构数据..."

# 从数据库导出CSV（兼容旧格式）
python scripts/export_database_to_csv.py --activity SH-SEP --output shanghai_new_output.csv

# 检查导出文件
echo "新架构导出文件: shanghai_new_output.csv"
ls -la shanghai_new_output.csv
wc -l shanghai_new_output.csv
echo "新架构文件大小: $(du -h shanghai_new_output.csv)"
```

### 步骤4: 上海对比验证
```bash
echo "🔍 开始上海9月对比验证..."

# 设置文件变量
OLD_SH_FILE="state/PerformanceData-SH-Sep.csv"
NEW_SH_FILE="shanghai_new_output.csv"

echo "旧架构文件: $OLD_SH_FILE"
echo "新架构文件: $NEW_SH_FILE"

# 基础对比
echo "=== 记录数量对比 ==="
wc -l $OLD_SH_FILE $NEW_SH_FILE

echo "=== 双轨统计对比 ==="
echo "旧架构平台单数:"
OLD_SH_PLATFORM=$(grep -c "平台单" $OLD_SH_FILE)
echo $OLD_SH_PLATFORM
echo "新架构平台单数:"
NEW_SH_PLATFORM=$(grep -c "平台单" $NEW_SH_FILE)
echo $NEW_SH_PLATFORM

echo "旧架构自引单数:"
OLD_SH_SELF=$(grep -c "自引单" $OLD_SH_FILE)
echo $OLD_SH_SELF
echo "新架构自引单数:"
NEW_SH_SELF=$(grep -c "自引单" $NEW_SH_FILE)
echo $NEW_SH_SELF

echo "旧架构红包奖励数:"
OLD_SH_HONGBAO=$(grep -c "红包" $OLD_SH_FILE)
echo $OLD_SH_HONGBAO
echo "新架构红包奖励数:"
NEW_SH_HONGBAO=$(grep -c "红包" $NEW_SH_FILE)
echo $NEW_SH_HONGBAO

# 验证结果
if [ "$OLD_SH_PLATFORM" -eq "$NEW_SH_PLATFORM" ] && [ "$OLD_SH_SELF" -eq "$NEW_SH_SELF" ] && [ "$OLD_SH_HONGBAO" -eq "$NEW_SH_HONGBAO" ]; then
    echo "✅ 上海9月双轨统计一致"
else
    echo "❌ 上海9月双轨统计不一致"
fi
```

## ✅ 预期结果

基于实时数据，您应该看到：

### 北京9月 (BJ-SEP)
- **记录数量**: 约1000+条（根据实时数据变化）
- **奖励类型**: 接好运、达标奖、优秀奖、精英奖
- **幸运数字**: 个人序号模式的幸运数字奖励
- **历史合同**: 标记为"Y"，仅计入业绩金额

### 上海9月 (SH-SEP)
- **记录数量**: 根据实时数据变化
- **双轨统计**: 平台单和自引单分别统计
- **奖励类型**: 阶梯奖励（基础奖、达标奖、优秀奖、精英奖、卓越奖）+ 自引单红包
- **管家格式**: "管家_服务商"格式
- **数据源**: 实时从Metabase API获取

## 🔧 手动数据对比（可选）

如果需要更详细的对比，可以手动检查关键数据：

### 检查关键管家数据
```bash
# 北京 - 检查关键管家的合同数量
echo "=== 北京关键管家对比 ==="
for hk in "余金凤" "文刘飞" "梁庆龙"; do
    old_count=$(grep -c "$hk" state/PerformanceData-BJ-Sep.csv)
    new_count=$(grep -c "$hk" beijing_new_output.csv)
    echo "管家 $hk: 旧系统 $old_count vs 新系统 $new_count"
done

# 上海 - 检查关键管家的合同数量
echo "=== 上海关键管家对比 ==="
for hk in "李涛" "周志林" "胡长俊"; do
    old_count=$(grep -c "$hk" state/PerformanceData-SH-Sep.csv)
    new_count=$(grep -c "$hk" shanghai_new_output.csv)
    echo "管家 $hk: 旧系统 $old_count vs 新系统 $new_count"
done
```

### 检查业绩金额统计
```bash
# 使用awk计算总业绩金额
echo "=== 业绩金额对比 ==="
old_bj_amount=$(awk -F',' 'NR>1 {sum+=$8} END {print sum}' state/PerformanceData-BJ-Sep.csv)
new_bj_amount=$(awk -F',' 'NR>1 {sum+=$8} END {print sum}' beijing_new_output.csv)
echo "北京总业绩: 旧系统 $old_bj_amount vs 新系统 $new_bj_amount"

old_sh_amount=$(awk -F',' 'NR>1 {sum+=$8} END {print sum}' state/PerformanceData-SH-Sep.csv)
new_sh_amount=$(awk -F',' 'NR>1 {sum+=$8} END {print sum}' shanghai_new_output.csv)
echo "上海总业绩: 旧系统 $old_sh_amount vs 新系统 $new_sh_amount"
```

## 🚨 注意事项

### 环境要求
1. **数据库清理**: 每次运行新架构前确保删除`performance_data.db`和`tasks.db`
2. **网络连接**: 确保能访问Metabase API
3. **文件权限**: 确保有写入权限创建CSV和数据库文件
4. **Python环境**: 需要pandas, sqlite3等依赖

### 验证要点
1. **数据一致性**: 重点检查记录数量、合同金额、奖励数量
2. **业务逻辑**: 北京关注幸运数字和历史合同，上海关注双轨统计
3. **实时数据**: 由于使用实时API数据，允许±1-2条记录的微小差异
4. **格式差异**: 新旧架构在数据格式上可能有差异，但业务逻辑应该一致

### 常见差异说明
1. **管家累计业绩金额**: 旧系统显示累计值，新系统通过数据库查询获得
2. **奖励名称格式**: 旧系统用逗号分隔，新系统用JSON数组格式
3. **管家名称格式**: 上海新系统包含"管家_服务商"格式

## 📞 支持

如果验证过程中遇到问题：

1. **检查网络**: 确保能访问Metabase API
2. **清理重试**: 删除所有输出文件后重新执行
3. **检查依赖**: 确保Python环境和依赖包正常

---

**验证原则**: 关注业务逻辑一致性，允许技术实现上的格式差异。
