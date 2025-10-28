# 旧架构详细技术分析

## 1. 代码行数统计

### 1.1 旧架构代码分布

| 文件 | 总行数 | 旧代码行数 | 新代码行数 | 删除比例 |
|------|--------|----------|----------|---------|
| `modules/data_processing_module.py` | 1600 | ~800 | ~800 | 50% |
| `modules/notification_module.py` | 479 | ~300 | ~179 | 63% |
| `jobs.py` | 353 | ~150 | ~203 | 42% |
| `modules/config.py` | ~500 | ~30 | ~470 | 6% |
| **总计** | **2932** | **~1280** | **~1652** | **44%** |

### 1.2 预期清理后的代码量

```
删除前: 2932 行
删除后: ~1652 行
减少: ~1280 行 (44%)
```

---

## 2. 模块依赖关系分析

### 2.1 旧架构依赖图

```
jobs.py (旧job)
├── data_processing_module.py (旧函数)
│   ├── config.py (旧常量)
│   └── data_utils.py (共用)
├── notification_module.py (旧函数)
│   ├── config.py (旧常量)
│   ├── data_utils.py (共用)
│   └── task_manager.py (共用)
└── request_module.py (共用)
```

### 2.2 新架构依赖图

```
modules/core/beijing_jobs.py (新job)
├── modules/core/processing_pipeline.py
├── modules/core/notification_service.py
├── modules/core/storage.py
├── modules/core/reward_calculator.py
├── modules/core/config_adapter.py
└── modules/config.py (新常量)

modules/core/shanghai_jobs.py (新job)
├── modules/core/processing_pipeline.py
├── modules/core/notification_service.py
├── modules/core/storage.py
├── modules/core/reward_calculator.py
├── modules/core/config_adapter.py
└── modules/config.py (新常量)
```

### 2.3 共用模块（保留）

```
✅ modules/data_utils.py
   - save_to_csv_with_headers()
   - archive_file()
   - read_contract_data()
   - collect_unique_contract_ids_from_file()
   - write_performance_data()
   - get_all_records_from_csv()
   - 等等

✅ modules/request_module.py
   - send_request_with_managed_session()

✅ modules/config.py (部分)
   - 新架构常量（BJ-2025-10, BJ-2025-11, SH-2025-10, SH-2025-11）
   - 通用常量（WECOM_GROUP_NAME_*, 等）

✅ task_manager.py
   - create_task()

✅ message_sender.py
   - 消息发送相关
```

---

## 3. 具体删除清单

### 3.1 jobs.py 中的删除项

**删除的函数** (~150行):
```python
# 8月北京
def signing_and_sales_incentive_aug_beijing():
    # ~40行

# 8月上海
def signing_and_sales_incentive_aug_shanghai():
    # ~40行

# 9月北京
def signing_and_sales_incentive_sep_beijing():
    # ~35行

# 9月上海
def signing_and_sales_incentive_sep_shanghai():
    # ~35行
```

**保留的函数** (~203行):
```python
✅ generate_daily_service_report()
✅ pending_orders_reminder_task()
✅ 其他辅助函数
```

### 3.2 data_processing_module.py 中的删除项

**删除的函数** (~800行):
```python
# 8月北京处理
process_data_jun_beijing()

# 8月上海处理
process_data_shanghai_apr()

# 9月上海处理
process_data_shanghai_sep()

# 9月北京处理
process_data_sep_beijing()

# 历史合同处理
process_historical_contract()
process_historical_contract_with_project_limit()
is_historical_contract()

# 其他辅助函数
load_existing_new_contracts_from_performance_file()
[以及其他相关函数]
```

**保留的函数** (~800行):
```python
✅ determine_lucky_number_reward()
✅ determine_lucky_number_reward_generic()
✅ should_enable_badge()
✅ 其他通用工具函数
```

### 3.3 notification_module.py 中的删除项

**删除的函数** (~300行):
```python
# 8月北京通知
notify_awards_jun_beijing()

# 8月上海通知
notify_awards_shanghai_generate_message_march()

# 9月北京通知
notify_awards_sep_beijing()

# 9月上海通知
notify_awards_shanghai_generic()

# 其他辅助函数
[以及其他相关函数]
```

**保留的函数** (~179行):
```python
✅ get_awards_mapping()
✅ generate_award_message()
✅ 其他通用工具函数
```

### 3.4 modules/config.py 中的删除项

**删除的常量** (~30个):
```python
# 8月北京
API_URL_BJ_AUG
TEMP_CONTRACT_DATA_FILE_BJ_AUG
PERFORMANCE_DATA_FILENAME_BJ_AUG
STATUS_FILENAME_BJ_AUG

# 8月上海
API_URL_SH_AUG
TEMP_CONTRACT_DATA_FILE_SH_AUG
PERFORMANCE_DATA_FILENAME_SH_AUG
STATUS_FILENAME_SH_AUG

# 9月北京
API_URL_BJ_SEP
TEMP_CONTRACT_DATA_FILE_BJ_SEP
PERFORMANCE_DATA_FILENAME_BJ_SEP
STATUS_FILENAME_BJ_SEP

# 9月上海
API_URL_SH_SEP
TEMP_CONTRACT_DATA_FILE_SH_SEP
PERFORMANCE_DATA_FILENAME_SH_SEP
STATUS_FILENAME_SH_SEP

# 其他旧常量
[以及其他相关常量]
```

**保留的常量**:
```python
✅ 新架构常量（10月、11月）
✅ 通用常量（WECOM_GROUP_NAME_*, 等）
✅ 配置字典（REWARD_CONFIGS）
```

---

## 4. 验证策略

### 4.1 删除前验证

```bash
# 1. 搜索所有旧函数引用
grep -r "process_data_jun_beijing\|process_data_shanghai_apr" --include="*.py" .
grep -r "process_data_sep_beijing\|process_data_shanghai_sep" --include="*.py" .
grep -r "notify_awards_jun_beijing\|notify_awards_sep_beijing" --include="*.py" .
grep -r "notify_awards_shanghai_generic" --include="*.py" .

# 2. 搜索所有旧常量引用
grep -r "API_URL_BJ_AUG\|API_URL_SH_AUG" --include="*.py" .
grep -r "API_URL_BJ_SEP\|API_URL_SH_SEP" --include="*.py" .

# 3. 检查导入语句
grep -r "from jobs import" --include="*.py" .
grep -r "from modules.data_processing_module import" --include="*.py" .
grep -r "from modules.notification_module import" --include="*.py" .
```

### 4.2 删除后验证

```bash
# 1. 确保新架构job可导入
python -c "from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing"
python -c "from modules.core.beijing_jobs import signing_and_sales_incentive_nov_beijing"
python -c "from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai"
python -c "from modules.core.shanghai_jobs import signing_and_sales_incentive_nov_shanghai"

# 2. 确保共用函数仍可用
python -c "from modules.data_utils import save_to_csv_with_headers"
python -c "from modules.request_module import send_request_with_managed_session"

# 3. 运行新架构job
python main.py  # 测试10月、11月job
```

---

## 5. 备份策略

### 5.1 创建备份分支

```bash
# 创建备份分支
git checkout -b backup/legacy-code

# 创建legacy目录
mkdir -p legacy

# 复制旧代码
cp modules/data_processing_module.py legacy/
cp modules/notification_module.py legacy/
cp jobs.py legacy/

# 提交备份
git add legacy/
git commit -m "backup: 保存旧架构代码备份"

# 推送备份分支
git push origin backup/legacy-code
```

### 5.2 恢复策略

```bash
# 如果需要恢复
git checkout backup/legacy-code -- legacy/
git checkout backup/legacy-code -- modules/data_processing_module.py
git checkout backup/legacy-code -- modules/notification_module.py
git checkout backup/legacy-code -- jobs.py
```

---

## 6. 时间估算

| 阶段 | 任务 | 时间 |
|------|------|------|
| 1 | 代码分析和验证 | 4小时 |
| 2 | 代码提取和备份 | 2小时 |
| 3 | 清理主代码 | 4小时 |
| 4 | 测试和验证 | 4小时 |
| **总计** | | **14小时** |

---

## 7. 风险缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 误删新架构代码 | 低 | 高 | 详细代码审查 + 备份 |
| 遗漏旧函数引用 | 中 | 中 | 自动化搜索 + 手工验证 |
| 新架构job失败 | 低 | 高 | 完整测试 + 回滚方案 |
| 配置常量冲突 | 低 | 中 | 详细检查 + 版本控制 |

---

**文档版本**: v1.0  
**创建日期**: 2025-10-28  
**状态**: 📋 待审核

