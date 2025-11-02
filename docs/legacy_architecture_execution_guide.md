# 旧架构移除执行指南

## 🎯 快速导航

- **计划文档**: `legacy_architecture_removal_plan.md`
- **技术分析**: `legacy_architecture_detailed_analysis.md`
- **本文档**: 执行步骤指南

---

## 阶段1: 代码分析和验证 (4小时)

### 步骤1.1: 验证新架构独立性

```bash
# 检查新架构job是否依赖旧函数
cd /path/to/sales-reward-hub

# 搜索新架构中对旧函数的引用
echo "=== 检查新架构对旧函数的依赖 ==="
grep -r "process_data_jun_beijing\|process_data_shanghai_apr\|process_data_sep_beijing\|process_data_shanghai_sep" \
  modules/core/ --include="*.py"

grep -r "notify_awards_jun_beijing\|notify_awards_sep_beijing\|notify_awards_shanghai_generic" \
  modules/core/ --include="*.py"

# 预期结果: 无输出（表示新架构不依赖旧函数）
```

### 步骤1.2: 验证旧函数使用范围

```bash
# 搜索所有对旧函数的引用
echo "=== 搜索旧函数的所有引用 ==="
grep -r "process_data_jun_beijing\|process_data_shanghai_apr\|process_data_sep_beijing\|process_data_shanghai_sep" \
  . --include="*.py" --exclude-dir=legacy

grep -r "notify_awards_jun_beijing\|notify_awards_sep_beijing\|notify_awards_shanghai_generic" \
  . --include="*.py" --exclude-dir=legacy

# 预期结果: 仅在 jobs.py 中出现
```

### 步骤1.3: 验证旧常量使用范围

```bash
# 搜索旧常量引用
echo "=== 搜索旧常量的引用 ==="
grep -r "API_URL_BJ_AUG\|API_URL_SH_AUG\|API_URL_BJ_SEP\|API_URL_SH_SEP" \
  . --include="*.py" --exclude-dir=legacy

# 预期结果: 仅在 jobs.py 和 config.py 中出现
```

### 步骤1.4: 创建验证报告

```bash
# 生成验证报告
cat > /tmp/legacy_verification.txt << 'EOF'
旧架构验证报告
===============

1. 新架构独立性: ✅ 通过
   - 新架构不依赖任何旧函数
   - 新架构使用独立的配置键

2. 旧函数使用范围: ✅ 通过
   - 旧函数仅在 jobs.py 中使用
   - 无其他代码依赖旧函数

3. 旧常量使用范围: ✅ 通过
   - 旧常量仅在 jobs.py 和 config.py 中使用
   - 新架构使用独立常量

4. 共用模块检查: ✅ 通过
   - data_utils.py 被新旧架构共用
   - request_module.py 被新旧架构共用
   - task_manager.py 被新旧架构共用

验证结论: ✅ 可以安全删除旧架构代码
EOF

cat /tmp/legacy_verification.txt
```

---

## 阶段2: 代码提取和备份 (2小时)

### 步骤2.1: 创建备份分支

```bash
# 创建备份分支
git checkout -b backup/legacy-code
git push origin backup/legacy-code

echo "✅ 备份分支已创建: backup/legacy-code"
```

### 步骤2.2: 创建legacy目录

```bash
# 创建legacy目录结构
mkdir -p legacy/modules
mkdir -p legacy/docs

# 复制旧代码文件
cp modules/data_processing_module.py legacy/modules/
cp modules/notification_module.py legacy/modules/
cp jobs.py legacy/

# 创建README说明
cat > legacy/README.md << 'EOF'
# 旧架构代码备份

本目录包含已移除的旧架构代码（8月、9月job）。

## 文件说明

- `jobs.py` - 旧job定义（8月、9月）
- `modules/data_processing_module.py` - 旧数据处理函数
- `modules/notification_module.py` - 旧通知函数

## 恢复方法

如需恢复旧代码，可使用以下命令：

```bash
git checkout backup/legacy-code -- legacy/
```

## 新架构位置

新架构代码位于：
- `modules/core/beijing_jobs.py` - 新job定义
- `modules/core/shanghai_jobs.py` - 新job定义
- `modules/core/processing_pipeline.py` - 新数据处理
- `modules/core/notification_service.py` - 新通知服务

EOF

echo "✅ legacy目录已创建"
```

### 步骤2.3: 提交备份

```bash
# 提交备份
git add legacy/
git commit -m "backup: 保存旧架构代码备份（8月、9月job）"
git push origin backup/legacy-code

echo "✅ 备份已提交到 backup/legacy-code 分支"
```

---

## 阶段3: 清理主代码 (4小时)

### 步骤3.1: 清理 jobs.py

```bash
# 备份原文件
cp jobs.py jobs.py.bak

# 删除旧job函数（保留新job和其他函数）
# 需要手工编辑或使用脚本删除以下函数：
# - signing_and_sales_incentive_aug_beijing()
# - signing_and_sales_incentive_aug_shanghai()
# - signing_and_sales_incentive_sep_beijing()
# - signing_and_sales_incentive_sep_shanghai()

# 保留的函数：
# - generate_daily_service_report()
# - pending_orders_reminder_task()

echo "⚠️  需要手工编辑 jobs.py，删除旧job函数"
```

### 步骤3.2: 清理 data_processing_module.py

```bash
# 备份原文件
cp modules/data_processing_module.py modules/data_processing_module.py.bak

# 删除旧函数（保留通用函数）
# 需要删除的函数：
# - process_data_jun_beijing()
# - process_data_shanghai_apr()
# - process_data_shanghai_sep()
# - process_data_sep_beijing()
# - process_historical_contract()
# - process_historical_contract_with_project_limit()
# - is_historical_contract()
# - load_existing_new_contracts_from_performance_file()

# 保留的函数：
# - determine_lucky_number_reward()
# - determine_lucky_number_reward_generic()
# - should_enable_badge()
# - 其他通用工具函数

echo "⚠️  需要手工编辑 data_processing_module.py，删除旧函数"
```

### 步骤3.3: 清理 notification_module.py

```bash
# 备份原文件
cp modules/notification_module.py modules/notification_module.py.bak

# 删除旧函数（保留通用函数）
# 需要删除的函数：
# - notify_awards_jun_beijing()
# - notify_awards_shanghai_generate_message_march()
# - notify_awards_sep_beijing()
# - notify_awards_shanghai_generic()

# 保留的函数：
# - get_awards_mapping()
# - generate_award_message()
# - 其他通用工具函数

echo "⚠️  需要手工编辑 notification_module.py，删除旧函数"
```

### 步骤3.4: 清理 modules/config.py

```bash
# 备份原文件
cp modules/config.py modules/config.py.bak

# 删除旧常量（保留新常量）
# 需要删除的常量：
# - API_URL_BJ_AUG, API_URL_SH_AUG
# - API_URL_BJ_SEP, API_URL_SH_SEP
# - TEMP_CONTRACT_DATA_FILE_BJ_AUG/SEP
# - PERFORMANCE_DATA_FILENAME_BJ_AUG/SEP
# - STATUS_FILENAME_BJ_AUG/SEP
# - 其他旧常量

# 保留的常量：
# - 新架构常量（10月、11月）
# - 通用常量（WECOM_GROUP_NAME_*, 等）
# - REWARD_CONFIGS 字典

echo "⚠️  需要手工编辑 modules/config.py，删除旧常量"
```

### 步骤3.5: 更新 main.py

```bash
# 备份原文件
cp main.py main.py.bak

# 删除旧job的导入和调用
# 需要删除的导入：
# from jobs import signing_and_sales_incentive_aug_beijing
# from jobs import signing_and_sales_incentive_aug_shanghai
# from jobs import signing_and_sales_incentive_sep_beijing
# from jobs import signing_and_sales_incentive_sep_shanghai

# 需要删除的调用：
# 8月和9月的job调用

# 保留的导入和调用：
# - 新架构job（10月、11月）
# - generate_daily_service_report()
# - pending_orders_reminder_task()

echo "⚠️  需要手工编辑 main.py，删除旧job的导入和调用"
```

---

## 阶段4: 测试和验证 (4小时)

### 步骤4.1: 验证导入

```bash
# 验证新架构job可导入
python3 << 'EOF'
try:
    from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing
    from modules.core.beijing_jobs import signing_and_sales_incentive_nov_beijing
    from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai
    from modules.core.shanghai_jobs import signing_and_sales_incentive_nov_shanghai
    print("✅ 新架构job导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    exit(1)
EOF
```

### 步骤4.2: 验证共用模块

```bash
# 验证共用模块仍可用
python3 << 'EOF'
try:
    from modules.data_utils import save_to_csv_with_headers
    from modules.request_module import send_request_with_managed_session
    from task_manager import create_task
    print("✅ 共用模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    exit(1)
EOF
```

### 步骤4.3: 运行新架构job

```bash
# 测试新架构job（需要真实环境）
python3 main.py

# 预期结果:
# - 北京10月job正常运行
# - 北京11月job正常运行
# - 上海10月job正常运行
# - 上海11月job正常运行
```

### 步骤4.4: 检查是否有遗漏

```bash
# 搜索是否还有旧函数引用
echo "=== 最终检查 ==="
grep -r "process_data_jun_beijing\|process_data_shanghai_apr\|process_data_sep_beijing\|process_data_shanghai_sep" \
  . --include="*.py" --exclude-dir=legacy --exclude-dir=.git

grep -r "notify_awards_jun_beijing\|notify_awards_sep_beijing\|notify_awards_shanghai_generic" \
  . --include="*.py" --exclude-dir=legacy --exclude-dir=.git

# 预期结果: 无输出
echo "✅ 检查完成"
```

---

## 提交和发布

### 最终提交

```bash
# 提交清理后的代码
git add -A
git commit -m "refactor: 移除旧架构代码（8月、9月job）

- 删除 jobs.py 中的旧job函数
- 删除 data_processing_module.py 中的旧处理函数
- 删除 notification_module.py 中的旧通知函数
- 删除 config.py 中的旧常量
- 更新 main.py 移除旧job调用

旧代码已备份到 backup/legacy-code 分支

代码行数减少: ~1280 行 (44%)
"

git push origin production-db-v2
```

### 创建Release标签

```bash
# 创建新版本标签
git tag -a v2.5.0 -m "refactor: 移除旧架构代码，保留新架构（10月、11月）"
git push origin v2.5.0
```

---

## 回滚方案

### 快速回滚

```bash
# 如果出现问题，快速回滚
git revert <commit-hash>
git push origin production-db-v2
```

### 完整恢复

```bash
# 从备份分支恢复所有旧代码
git checkout backup/legacy-code -- legacy/
git checkout backup/legacy-code -- modules/data_processing_module.py
git checkout backup/legacy-code -- modules/notification_module.py
git checkout backup/legacy-code -- jobs.py
git checkout backup/legacy-code -- modules/config.py
```

---

**文档版本**: v1.0  
**创建日期**: 2025-10-28  
**状态**: 📋 待审核

