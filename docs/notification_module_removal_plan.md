# modules/notification_module.py 删除执行计划

**计划日期**: 2025-10-28  
**预计工作量**: 1.5小时  
**风险等级**: 🟢 **低**

---

## 1. 执行步骤

### 步骤1: 提取共用函数到 data_utils.py

**需要提取的函数**:
```python
def get_awards_mapping(config_key)
def generate_award_message(record, awards_mapping, city="BJ", config_key=None)
def preprocess_rate(rate)
def preprocess_amount(amount)
```

**操作**:
1. 复制这4个函数到 `modules/data_utils.py` 末尾
2. 保留原有的导入和依赖
3. 确保 `should_enable_badge()` 已在 `data_utils.py` 中

**预计时间**: 15分钟

---

### 步骤2: 更新导入语句

**需要更新的文件**:

#### 文件1: `modules/core/notification_service.py`
```python
# 旧
from modules.notification_module import get_awards_mapping
from modules.notification_module import generate_award_message
from modules.notification_module import preprocess_rate

# 新
from modules.data_utils import get_awards_mapping, generate_award_message, preprocess_rate
```

#### 文件2: `modules/service_provider_sla_monitor.py`
```python
# 旧
from modules.notification_module import post_text_to_webhook

# 新
# 需要检查是否真的使用了这个函数
```

#### 文件3: `jobs.py`
```python
# 旧
from modules.notification_module import *

# 新
# 删除这行（不再需要）
```

**预计时间**: 15分钟

---

### 步骤3: 验证导入

**命令**:
```bash
# 检查是否还有对旧模块的导入
grep -r "from modules.notification_module import" --include="*.py" .

# 检查是否还有对旧函数的调用
grep -r "notify_awards_beijing_generic\|notify_awards_shanghai_generic\|post_text_to_webhook" --include="*.py" modules/core/
```

**预期结果**: 无输出（表示没有遗漏）

**预计时间**: 10分钟

---

### 步骤4: 删除旧文件

**操作**:
```bash
rm modules/notification_module.py
```

**预计时间**: 1分钟

---

### 步骤5: 运行测试

**测试命令**:
```bash
# 1. 验证新架构job可导入
python -c "from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing; print('✅ 北京10月job导入成功')"
python -c "from modules.core.beijing_jobs import signing_and_sales_incentive_nov_beijing; print('✅ 北京11月job导入成功')"
python -c "from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai; print('✅ 上海10月job导入成功')"
python -c "from modules.core.shanghai_jobs import signing_and_sales_incentive_nov_shanghai; print('✅ 上海11月job导入成功')"

# 2. 验证共用函数可导入
python -c "from modules.data_utils import get_awards_mapping, generate_award_message, preprocess_rate; print('✅ 共用函数导入成功')"

# 3. 验证通知服务可导入
python -c "from modules.core.notification_service import NotificationService; print('✅ NotificationService导入成功')"

# 4. 验证SLA监控可导入
python -c "from modules.service_provider_sla_monitor import process_sla_violations; print('✅ SLA监控导入成功')"

# 5. 验证旧模块已删除
python -c "from modules.notification_module import get_awards_mapping" 2>&1 | grep -q "No module named" && echo "✅ 旧模块已删除" || echo "❌ 旧模块仍存在"
```

**预计时间**: 15分钟

---

### 步骤6: 提交代码

**提交信息**:
```
refactor: 删除旧架构模块 modules/notification_module.py

- 将共用函数提取到 modules/data_utils.py:
  * get_awards_mapping()
  * generate_award_message()
  * preprocess_rate()
  * preprocess_amount()
- 更新所有导入语句
- 删除 modules/notification_module.py (~392行)
- 代码行数减少 ~392行 (36%)

验证:
- ✅ 新架构job可正常导入
- ✅ 共用函数可正常导入
- ✅ 通知服务可正常导入
- ✅ SLA监控可正常导入
- ✅ 旧模块已删除
```

**预计时间**: 10分钟

---

## 2. 详细操作指南

### 2.1 提取函数到 data_utils.py

从 `modules/notification_module.py` 中复制以下函数到 `modules/data_utils.py` 末尾:

1. `get_awards_mapping()` (第15-37行)
2. `generate_award_message()` (第39-150行)
3. `preprocess_rate()` (第152-...行)
4. `preprocess_amount()` (第...行)

---

### 2.2 更新导入语句

**文件1**: `modules/core/notification_service.py`
- 第162行: 更新 `get_awards_mapping` 导入
- 第326行: 更新 `generate_award_message` 导入
- 第359行: 更新 `preprocess_rate` 导入

**文件2**: `modules/service_provider_sla_monitor.py`
- 检查 `post_text_to_webhook` 是否真的被使用
- 如果使用，需要提取或重新实现

**文件3**: `jobs.py`
- 删除 `from modules.notification_module import *`

---

## 3. 验证清单

- [ ] 4个共用函数已添加到 `modules/data_utils.py`
- [ ] `modules/core/notification_service.py` 导入已更新
- [ ] `modules/service_provider_sla_monitor.py` 导入已更新
- [ ] `jobs.py` 导入已更新
- [ ] 没有其他文件导入旧模块
- [ ] 新架构job可正常导入
- [ ] 共用函数可正常导入
- [ ] 通知服务可正常导入
- [ ] SLA监控可正常导入
- [ ] 旧模块已删除
- [ ] 代码已提交

---

## 4. 回滚方案

如果出现问题，可以从备份分支恢复:

```bash
# 恢复旧文件
git checkout backup/legacy-code -- modules/notification_module.py

# 恢复导入语句
git checkout HEAD~1 -- modules/core/notification_service.py modules/service_provider_sla_monitor.py jobs.py modules/data_utils.py
```

---

## 5. 时间表

| 步骤 | 预计时间 | 实际时间 |
|------|---------|---------|
| 步骤1: 提取函数 | 15分钟 | |
| 步骤2: 更新导入 | 15分钟 | |
| 步骤3: 验证导入 | 10分钟 | |
| 步骤4: 删除文件 | 1分钟 | |
| 步骤5: 运行测试 | 15分钟 | |
| 步骤6: 提交代码 | 10分钟 | |
| **总计** | **66分钟** | |

---

## 6. 注意事项

⚠️ **重要**:
1. 确保备份分支 `backup/legacy-code` 存在
2. 确保所有测试通过
3. 确保没有其他文件依赖旧模块
4. 提交前运行完整测试

✅ **建议**:
1. 在单独的分支上执行此操作
2. 创建PR进行代码审查
3. 获得批准后再合并到主分支

