# modules/data_processing_module.py 删除执行计划

**计划日期**: 2025-10-28  
**预计工作量**: 1小时  
**风险等级**: 🟢 **低**

---

## 1. 执行步骤

### 步骤1: 提取共用函数到 data_utils.py

**需要提取的函数**:
```python
def should_enable_badge(config_key: str, badge_type: str) -> bool:
    """检查是否启用指定徽章"""
    ...
```

**操作**:
1. 复制 `should_enable_badge()` 函数（第86-105行）
2. 添加到 `modules/data_utils.py` 末尾
3. 保留原有的导入和依赖

**预计时间**: 5分钟

---

### 步骤2: 更新导入语句

**需要更新的文件**:

#### 文件1: `modules/core/notification_service.py`
```python
# 旧
from modules.data_processing_module import should_enable_badge

# 新
from modules.data_utils import should_enable_badge
```

#### 文件2: `modules/notification_module.py`
```python
# 旧
from modules.data_processing_module import should_enable_badge

# 新
from modules.data_utils import should_enable_badge
```

**预计时间**: 5分钟

---

### 步骤3: 验证导入

**命令**:
```bash
# 检查是否还有对旧模块的导入
grep -r "from modules.data_processing_module import" --include="*.py" .

# 检查是否还有对旧函数的调用
grep -r "determine_lucky_number_reward_generic\|determine_self_referral_rewards\|get_self_referral_config\|process_data_" --include="*.py" modules/core/
```

**预期结果**: 无输出（表示没有遗漏）

**预计时间**: 5分钟

---

### 步骤4: 删除旧文件

**操作**:
```bash
rm modules/data_processing_module.py
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

# 2. 验证共用模块可导入
python -c "from modules.data_utils import should_enable_badge; print('✅ should_enable_badge导入成功')"

# 3. 验证通知服务可导入
python -c "from modules.core.notification_service import NotificationService; print('✅ NotificationService导入成功')"

# 4. 验证旧模块已删除
python -c "from modules.data_processing_module import should_enable_badge" 2>&1 | grep -q "No module named" && echo "✅ 旧模块已删除" || echo "❌ 旧模块仍存在"
```

**预计时间**: 10分钟

---

### 步骤6: 提交代码

**提交信息**:
```
refactor: 删除旧架构模块 modules/data_processing_module.py

- 将 should_enable_badge() 函数提取到 modules/data_utils.py
- 更新所有导入语句
- 删除 modules/data_processing_module.py (~1600行)
- 代码行数减少 ~1600行 (44%)

验证:
- ✅ 新架构job可正常导入
- ✅ 共用函数可正常导入
- ✅ 旧模块已删除
```

**预计时间**: 5分钟

---

## 2. 详细操作指南

### 2.1 提取函数到 data_utils.py

**操作**:
1. 打开 `modules/data_utils.py`
2. 跳转到文件末尾
3. 添加以下代码:

```python
def should_enable_badge(config_key: str, badge_type: str) -> bool:
    """
    检查是否启用指定徽章

    Args:
        config_key: 配置键
        badge_type: 徽章类型 ("elite" 或 "rising_star")

    Returns:
        bool: 是否启用徽章
    """
    from modules import config
    
    reward_config = config.REWARD_CONFIGS.get(config_key, {})
    badge_config = reward_config.get("badge_config", {})

    if badge_type == "elite":
        return badge_config.get("enable_elite_badge", True)  # 默认启用
    elif badge_type == "rising_star":
        return badge_config.get("enable_rising_star_badge", False)  # 默认禁用

    return False
```

---

### 2.2 更新导入语句

**文件1**: `modules/core/notification_service.py` (第341行)
```python
# 查找
from modules.data_processing_module import should_enable_badge

# 替换为
from modules.data_utils import should_enable_badge
```

**文件2**: `modules/notification_module.py` (第55行)
```python
# 查找
from modules.data_processing_module import should_enable_badge

# 替换为
from modules.data_utils import should_enable_badge
```

---

## 3. 验证清单

- [ ] `should_enable_badge()` 已添加到 `modules/data_utils.py`
- [ ] `modules/core/notification_service.py` 导入已更新
- [ ] `modules/notification_module.py` 导入已更新
- [ ] 没有其他文件导入旧模块
- [ ] 新架构job可正常导入
- [ ] 共用函数可正常导入
- [ ] 旧模块已删除
- [ ] 代码已提交

---

## 4. 回滚方案

如果出现问题，可以从备份分支恢复:

```bash
# 恢复旧文件
git checkout backup/legacy-code -- modules/data_processing_module.py

# 恢复导入语句
git checkout HEAD~1 -- modules/core/notification_service.py modules/notification_module.py modules/data_utils.py
```

---

## 5. 预期结果

### 代码统计
```
删除前: 1600行 (modules/data_processing_module.py)
删除后: 0行
减少: ~1600行
```

### 文件变化
```
删除: modules/data_processing_module.py
修改: modules/data_utils.py (+25行)
修改: modules/core/notification_service.py (1行)
修改: modules/notification_module.py (1行)
```

### 总体影响
```
代码行数减少: ~1574行
模块数减少: 1个
复杂度降低: 显著
```

---

## 6. 时间表

| 步骤 | 预计时间 | 实际时间 |
|------|---------|---------|
| 步骤1: 提取函数 | 5分钟 | |
| 步骤2: 更新导入 | 5分钟 | |
| 步骤3: 验证导入 | 5分钟 | |
| 步骤4: 删除文件 | 1分钟 | |
| 步骤5: 运行测试 | 10分钟 | |
| 步骤6: 提交代码 | 5分钟 | |
| **总计** | **31分钟** | |

---

## 7. 注意事项

⚠️ **重要**:
1. 确保备份分支 `backup/legacy-code` 存在
2. 确保所有测试通过
3. 确保没有其他文件依赖旧模块
4. 提交前运行完整测试

✅ **建议**:
1. 在单独的分支上执行此操作
2. 创建PR进行代码审查
3. 获得批准后再合并到主分支

