# 手工测试指南

**版本**: v2.0  
**更新日期**: 2025-09-22  
**目标**: 在本地环境验证新旧架构等价性

## 🚀 快速开始

### 方法1: 一键测试（推荐）
```bash
# 测试所有城市
python quick_manual_test.py --all

# 只测试北京
python quick_manual_test.py --beijing

# 只测试上海
python quick_manual_test.py --shanghai
```

### 方法2: 使用自动化验证工具
```bash
# 北京验证
python scripts/comprehensive_equivalence_validator.py --city beijing --month sep

# 上海验证
python scripts/comprehensive_equivalence_validator.py --city shanghai --month sep
```

## 📋 手动步骤验证

如果需要详细了解验证过程，请参考 `docs/manual_validation_guide.md`

### 北京9月验证步骤
```bash
# 1. 清理环境
rm -f performance_data.db state/PerformanceData-BJ-Sep.csv performance_data_BJ-SEP_*.csv

# 2. 执行旧架构
python -c "
import sys; sys.path.insert(0, '.')
from jobs import signing_and_sales_incentive_sep_beijing
signing_and_sales_incentive_sep_beijing()
"

# 3. 执行新架构
python -c "
import sys; sys.path.insert(0, '.')
from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
result = signing_and_sales_incentive_sep_beijing_v2()
print(f'处理了{len(result)}条记录')
"

# 4. 导出新架构数据
python scripts/export_database_to_csv.py --activity BJ-SEP --compatible

# 5. 对比验证
python scripts/manual_validation_helper.py
```

### 上海9月验证步骤
```bash
# 1. 清理环境
rm -f performance_data.db state/PerformanceData-SH-Sep.csv performance_data_SH-SEP_*.csv

# 2. 执行旧架构
python -c "
import sys; sys.path.insert(0, '.')
from jobs import signing_and_sales_incentive_sep_shanghai
signing_and_sales_incentive_sep_shanghai()
"

# 3. 执行新架构
python -c "
import sys; sys.path.insert(0, '.')
from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
result = signing_and_sales_incentive_sep_shanghai_v2()
print(f'处理了{len(result)}条记录')
"

# 4. 导出新架构数据
python scripts/export_database_to_csv.py --activity SH-SEP --dual-track

# 5. 对比验证
python scripts/manual_validation_helper.py
```

## ✅ 预期结果

### 北京9月 (BJ-SEP)
- **记录数量**: 1055条
- **合同金额**: 6,928,792.94元
- **奖励记录**: 34条（31个接好运+6个达标奖+1个优秀奖）
- **管家数量**: 53个

### 上海9月 (SH-SEP)
- **记录数量**: 173条
- **合同金额**: 1,539,863.00元
- **奖励记录**: 24条
- **特色功能**: 双轨统计、管家_服务商键格式

## 🛠️ 工具说明

### 主要文件
- `quick_manual_test.py` - 一键测试脚本
- `scripts/manual_validation_helper.py` - 详细对比工具
- `docs/manual_validation_guide.md` - 完整手工验证指南

### 验证工具
- `scripts/comprehensive_equivalence_validator.py` - 全面等价性验证
- `scripts/export_database_to_csv.py` - 数据库导出工具
- `scripts/environment_validator.py` - 环境检查工具

## 🚨 注意事项

### 环境要求
- Python 3.7+
- 网络连接（访问Metabase API）
- 项目依赖已安装

### 常见问题
1. **网络问题**: 确保能访问 metabase.fsgo365.cn:3000
2. **权限问题**: 确保有写入权限创建文件
3. **环境问题**: 确保在项目根目录运行
4. **依赖问题**: 确保pandas, sqlite3等依赖已安装

### 故障排除
```bash
# 检查环境
python scripts/environment_validator.py --activity BJ-SEP

# 查看日志
tail -f logs/app.log

# 清理重试
rm -f performance_data.db state/PerformanceData-*.csv performance_data_*.csv
```

## 📞 支持

如果遇到问题：
1. 查看 `docs/manual_validation_guide.md` 获取详细指导
2. 检查日志文件 `logs/app.log`
3. 确认网络连接和环境配置
4. 使用环境验证工具检查状态

## 🎯 验证原则

- **零容忍差异**: 任何差异都必须分析
- **100%等价性**: 新旧架构必须完全一致
- **真实数据**: 使用生产环境数据验证
- **完整覆盖**: 验证所有业务逻辑和特色功能

---

**核心目标**: 确保新架构可以安全替代旧架构，保证业务连续性和数据准确性。
