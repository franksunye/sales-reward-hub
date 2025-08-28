# 全局配置参数弃用计划

## 📋 概述

随着奖励系统的通用化完成，以下全局配置参数已经可以弃用：

- `PERFORMANCE_AMOUNT_CAP`
- `ENABLE_PERFORMANCE_AMOUNT_CAP`

这些参数是通用化之前的临时解决方案，现在已被配置驱动的架构替代。

## 🔍 弃用原因

### 1. 架构不一致
- 全局变量与配置化架构不符
- 不同城市使用不同的配置方式
- 维护复杂度高

### 2. 功能重复
- 配置功能已在 `REWARD_CONFIGS` 中实现
- 新架构更灵活、可扩展

### 3. 代码混乱
- 新旧两套配置系统并存
- 容易产生配置冲突

## 📊 当前使用情况

### ✅ 已替换的地方
- `determine_rewards_generic` 函数：完全使用配置
- `process_data_shanghai_apr` 函数：已改为使用配置
- 导入语句：已移除

### ⚠️ 仍在使用的地方
- `determine_rewards_shanghai_apr` 函数：已弃用，仅用于测试
- 测试文件：等价性测试中使用
- 文档：配置指南中提及

## 🗑️ 弃用计划

### 阶段一：标记弃用（已完成）
- [x] 添加 `@deprecated` 注释
- [x] 移除生产代码中的使用
- [x] 更新导入语句

### 阶段二：更新文档（1周内）
- [ ] 更新配置指南文档
- [ ] 添加迁移说明
- [ ] 更新项目文档

### 阶段三：清理测试（2周内）
- [ ] 更新测试用例，使用新配置
- [ ] 移除对全局变量的依赖
- [ ] 验证所有测试通过

### 阶段四：完全移除（1个月后）
- [ ] 删除全局变量定义
- [ ] 清理相关注释
- [ ] 最终验证

## 🔄 迁移指南

### 旧配置方式
```python
# 全局配置（已弃用）
PERFORMANCE_AMOUNT_CAP = 40000
ENABLE_PERFORMANCE_AMOUNT_CAP = False

# 在代码中使用
if config.ENABLE_PERFORMANCE_AMOUNT_CAP:
    amount = housekeeper_data['performance_amount']
else:
    amount = housekeeper_data['total_amount']
```

### 新配置方式
```python
# 配置化方式（推荐）
"SH-2025-04": {
    "performance_limits": {
        "enable_cap": False,
        "single_contract_cap": 40000
    }
}

# 在代码中使用
performance_limits = reward_config.get("performance_limits", {})
enable_cap = performance_limits.get("enable_cap", False)
if enable_cap:
    amount = housekeeper_data['performance_amount']
else:
    amount = housekeeper_data['total_amount']
```

## 📁 影响的文件

### 配置文件
- `modules/config.py` - 已添加弃用标记

### 代码文件
- `modules/data_processing_module.py` - 已更新

### 测试文件
- `tests/test_shanghai_apr_equivalence.py` - 需要更新
- `tests/test_rewards.py` - 需要更新

### 文档文件
- `docs/06_configuration_guide.md` - 需要更新
- `docs/project_management/` - 需要更新

## ⚠️ 注意事项

1. **向后兼容**：在完全移除前保持兼容性
2. **测试覆盖**：确保新配置的测试覆盖率
3. **团队通知**：及时通知团队成员配置变更
4. **文档同步**：保持文档与代码同步

## 🎯 预期收益

### 代码质量
- 统一配置架构
- 减少配置冲突
- 提高可维护性

### 开发效率
- 简化配置管理
- 减少学习成本
- 提高开发速度

### 系统稳定性
- 减少配置错误
- 提高系统一致性
- 降低维护风险

## 📝 执行记录

| 日期 | 阶段 | 操作 | 状态 |
|------|------|------|------|
| 2025-01-XX | 阶段一 | 添加弃用标记 | ✅ 完成 |
| 2025-01-XX | 阶段一 | 更新生产代码 | ✅ 完成 |
| 2025-01-XX | 阶段一 | 移除导入语句 | ✅ 完成 |
| TBD | 阶段二 | 更新文档 | ⏳ 待执行 |
| TBD | 阶段三 | 清理测试 | ⏳ 待执行 |
| TBD | 阶段四 | 完全移除 | ⏳ 待执行 |

---

**总结**：全局配置参数 `PERFORMANCE_AMOUNT_CAP` 和 `ENABLE_PERFORMANCE_AMOUNT_CAP` 已经可以安全弃用，建议按照此计划分阶段清理。
