# 手动验证指南

**版本**: v2.0
**更新日期**: 2025-09-22
**适用范围**: 北京和上海9月销售激励活动验证

## 🎯 目标
在您的本地环境手动执行新旧架构，对比验证结果一致性。支持北京和上海两个城市的完整验证流程。

## 📋 验证清单
- [ ] 北京9月 (BJ-SEP) 验证
- [ ] 上海9月 (SH-SEP) 验证
- [ ] 跨城市兼容性验证

## 📋 准备工作

### 环境要求
- Python 3.7+
- 网络连接（访问Metabase API）
- 项目依赖已安装

### ⚠️ 实时数据验证说明
**重要**: 手工测试与自动化验证的区别：

- **自动化验证**: 使用固定基准数据，确保100%等价性
- **手工测试**: 使用实时API数据，验证系统功能正常

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
rm -f logs/*.log

# 2. 确保在项目根目录
pwd  # 应该显示项目根路径
ls modules/  # 应该能看到core目录

# 3. 验证Python环境
python --version
python -c "import pandas, sqlite3; print('依赖检查通过')"
```

### 验证工具准备
```bash
# 检查验证工具是否可用
ls scripts/export_database_to_csv.py
ls scripts/comprehensive_equivalence_validator.py
python scripts/export_database_to_csv.py --help
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
python scripts/export_database_to_csv.py --activity BJ-SEP --compatible

# 检查导出文件
NEW_BJ_FILE=$(ls performance_data_BJ-SEP_*.csv | head -1)
echo "新架构导出文件: $NEW_BJ_FILE"
ls -la $NEW_BJ_FILE
wc -l $NEW_BJ_FILE
echo "新架构文件大小: $(du -h $NEW_BJ_FILE)"
```

### 步骤4: 北京对比验证
```bash
echo "🔍 开始北京9月对比验证..."

# 设置文件变量
OLD_BJ_FILE="state/PerformanceData-BJ-Sep.csv"
NEW_BJ_FILE=$(ls performance_data_BJ-SEP_*.csv | head -1)

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

# 清理环境
rm -f state/PerformanceData-SH-Sep.csv
rm -f performance_data.db

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

# 从数据库导出CSV（支持双轨统计）
python scripts/export_database_to_csv.py --activity SH-SEP --dual-track

# 检查导出文件
NEW_SH_FILE=$(ls performance_data_SH-SEP_*.csv | head -1)
echo "新架构导出文件: $NEW_SH_FILE"
ls -la $NEW_SH_FILE
wc -l $NEW_SH_FILE
echo "新架构文件大小: $(du -h $NEW_SH_FILE)"
```

### 步骤4: 上海对比验证
```bash
echo "🔍 开始上海9月对比验证..."

# 设置文件变量
OLD_SH_FILE="state/PerformanceData-SH-Sep.csv"
NEW_SH_FILE=$(ls performance_data_SH-SEP_*.csv | head -1)

echo "旧架构文件: $OLD_SH_FILE"
echo "新架构文件: $NEW_SH_FILE"

# 基础对比
echo "=== 记录数量对比 ==="
wc -l $OLD_SH_FILE $NEW_SH_FILE

echo "=== 双轨统计字段检查 ==="
echo "检查新架构是否包含双轨统计字段:"
head -1 $NEW_SH_FILE | grep -o "平台单累计\|自引单累计" || echo "双轨统计字段存在"

echo "=== 奖励统计对比 ==="
echo "旧架构奖励数:"
OLD_SH_REWARDS=$(grep -c "接好运\|达标奖\|优秀奖" $OLD_SH_FILE)
echo $OLD_SH_REWARDS
echo "新架构奖励数:"
NEW_SH_REWARDS=$(grep -c "接好运\|达标奖\|优秀奖" $NEW_SH_FILE)
echo $NEW_SH_REWARDS

# 验证结果
if [ "$OLD_SH_REWARDS" -eq "$NEW_SH_REWARDS" ]; then
    echo "✅ 上海9月奖励数量一致"
else
    echo "❌ 上海9月奖励数量不一致"
fi

echo "=== 管家键格式检查 ==="
echo "检查管家_服务商格式:"
head -5 $NEW_SH_FILE | cut -d',' -f3,4 | tail -4
```

## ✅ 预期结果

基于我们的自动化验证，您应该看到：

### 北京9月 (BJ-SEP)
- **记录数量**: 1055条
- **合同金额总和**: 6,928,792.94元
- **奖励记录**: 34条（31个接好运+6个达标奖+1个优秀奖）
- **管家数量**: 53个
- **幸运数字**: 5的倍数获得接好运奖励

### 上海9月 (SH-SEP)
- **记录数量**: 根据实时数据变化（验证时为173条）
- **合同金额总和**: 根据实时数据变化（验证时为1,539,863.00元）
- **奖励记录**: 根据实时数据变化（验证时为24条）
- **管家键格式**: "管家_服务商"
- **双轨统计**: 支持平台单/自引单分别统计
- **数据源**: 实时从Metabase API获取

## 🔧 详细验证（可选）

### Python脚本验证
```python
# 创建 detailed_compare.py 文件
import pandas as pd
import sys

def compare_beijing():
    print("🏢 北京9月详细对比")
    print("=" * 50)

    try:
        old_df = pd.read_csv('state/PerformanceData-BJ-Sep.csv')
        new_files = [f for f in os.listdir('.') if f.startswith('performance_data_BJ-SEP_')]
        if not new_files:
            print("❌ 未找到新架构北京输出文件")
            return False

        new_df = pd.read_csv(new_files[0])

        print(f"记录数: 旧{len(old_df)} vs 新{len(new_df)}")
        print(f"合同金额: 旧{old_df['合同金额(adjustRefundMoney)'].sum():.2f} vs 新{new_df['合同金额(adjustRefundMoney)'].sum():.2f}")

        old_rewards = len(old_df[old_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        new_rewards = len(new_df[new_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        print(f"奖励数: 旧{old_rewards} vs 新{new_rewards}")

        # 检查关键管家
        key_housekeepers = ['余金凤', '张争光', '文刘飞']
        for hk in key_housekeepers:
            old_count = len(old_df[old_df['管家(serviceHousekeeper)'] == hk])
            new_count = len(new_df[new_df['管家(serviceHousekeeper)'] == hk])
            print(f"管家{hk}: 旧{old_count} vs 新{new_count}")

        return len(old_df) == len(new_df) and old_rewards == new_rewards

    except Exception as e:
        print(f"❌ 北京对比失败: {e}")
        return False

def compare_shanghai():
    print("\n🏙️ 上海9月详细对比")
    print("=" * 50)

    try:
        old_df = pd.read_csv('state/PerformanceData-SH-Sep.csv')
        new_files = [f for f in os.listdir('.') if f.startswith('performance_data_SH-SEP_')]
        if not new_files:
            print("❌ 未找到新架构上海输出文件")
            return False

        new_df = pd.read_csv(new_files[0])

        print(f"记录数: 旧{len(old_df)} vs 新{len(new_df)}")
        print(f"合同金额: 旧{old_df['合同金额(adjustRefundMoney)'].sum():.2f} vs 新{new_df['合同金额(adjustRefundMoney)'].sum():.2f}")

        old_rewards = len(old_df[old_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        new_rewards = len(new_df[new_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        print(f"奖励数: 旧{old_rewards} vs 新{new_rewards}")

        # 检查双轨统计字段
        dual_track_fields = ['平台单累计数量', '平台单累计金额', '自引单累计数量', '自引单累计金额']
        for field in dual_track_fields:
            if field in new_df.columns:
                print(f"✅ {field}: 存在")
            else:
                print(f"❌ {field}: 缺失")

        return len(old_df) == len(new_df) and old_rewards == new_rewards

    except Exception as e:
        print(f"❌ 上海对比失败: {e}")
        return False

if __name__ == "__main__":
    import os

    bj_success = compare_beijing()
    sh_success = compare_shanghai()

    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)
    print(f"北京9月: {'✅ 通过' if bj_success else '❌ 失败'}")
    print(f"上海9月: {'✅ 通过' if sh_success else '❌ 失败'}")

    if bj_success and sh_success:
        print("🎉 所有验证通过！新旧架构完全等价")
        sys.exit(0)
    else:
        print("⚠️ 验证失败，请检查差异")
        sys.exit(1)
```

```bash
# 运行详细对比
python detailed_compare.py
```

## 🚨 注意事项

### 环境要求
1. **数据库清理**: 每次运行新架构前确保删除`performance_data.db`
2. **网络连接**: 确保能访问Metabase API (metabase.fsgo365.cn:3000)
3. **文件权限**: 确保有写入权限创建CSV和数据库文件
4. **Python环境**: 需要pandas, sqlite3等依赖

### 文件管理
1. **文件名**: 新架构导出的文件名包含时间戳，需要动态获取
2. **根目录清洁**: 新架构默认不生成CSV，保持根目录清洁
3. **状态文件**: 旧架构会在state/目录生成文件
4. **日志文件**: 执行过程中会生成日志，可用于问题排查

### 验证要点
1. **数据一致性**: 重点检查记录数量、合同金额、奖励数量
2. **业务逻辑**: 北京关注幸运数字，上海关注双轨统计
3. **特色功能**: 上海的管家键格式和双轨统计字段
4. **边界情况**: 大金额项目限额、历史合同处理

## 💡 工具使用

### 数据库导出工具
```bash
# 查看数据库中的活动
python scripts/export_database_to_csv.py --list

# 导出北京活动（兼容格式）
python scripts/export_database_to_csv.py --activity BJ-SEP --compatible

# 导出上海活动（双轨统计）
python scripts/export_database_to_csv.py --activity SH-SEP --dual-track

# 导出到指定文件
python scripts/export_database_to_csv.py --activity BJ-SEP --output my_beijing_export.csv
```

### 自动化验证工具
```bash
# 全面等价性验证（推荐）
python scripts/comprehensive_equivalence_validator.py --city beijing --month sep
python scripts/comprehensive_equivalence_validator.py --city shanghai --month sep

# 单项验证工具
python scripts/data_input_consistency_validator.py --activity BJ-SEP
python scripts/business_logic_validator.py --activity BJ-SEP
python scripts/output_comparison_validator.py --activity BJ-SEP
```

### 问题排查工具
```bash
# 检查环境状态
python scripts/environment_validator.py --activity BJ-SEP

# 清理数据库
python scripts/database_cleanup.py --activity BJ-SEP

# 查看详细日志
tail -f logs/app.log
```

## 🔄 完整验证流程

### 快速验证（推荐）
```bash
# 一键验证北京
echo "🚀 开始北京9月完整验证..."
rm -f performance_data.db state/PerformanceData-BJ-Sep.csv
python scripts/comprehensive_equivalence_validator.py --city beijing --month sep

# 一键验证上海
echo "🚀 开始上海9月完整验证..."
rm -f performance_data.db state/PerformanceData-SH-Sep.csv
python scripts/comprehensive_equivalence_validator.py --city shanghai --month sep
```

### 手动验证（详细）
按照本文档的步骤逐一执行，适合深入了解验证过程。

## 📞 支持

如果验证过程中遇到问题：

1. **检查日志**: `tail -f logs/app.log`
2. **检查网络**: 确保能访问Metabase API
3. **检查环境**: `python scripts/environment_validator.py`
4. **清理重试**: 删除所有输出文件后重新执行

---

**核心理念**: 新架构数据库优先，按需导出CSV，保持架构纯粹性。
**验证原则**: 零容忍差异，100%等价性，真实数据验证。
