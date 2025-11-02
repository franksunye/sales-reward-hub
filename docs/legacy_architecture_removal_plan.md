# 旧架构移除计划 (Legacy Architecture Removal Plan)

## 📋 执行摘要

**目标**: 移除8月和9月的旧架构代码，保留新架构（10月及以后）

**风险等级**: 🟡 **中等** - 需要谨慎验证，但影响范围明确

**预计工作量**: 3-5个工作日

**关键原则**: 
- ✅ 保留所有新架构代码（10月、11月）
- ✅ 保留所有配置和数据文件
- ✅ 保留所有测试脚本
- ❌ 移除旧架构特定的函数和模块

---

## 1. 旧架构范围分析

### 1.1 旧架构使用的Job函数

| Job函数 | 位置 | 架构 | 状态 | 依赖模块 |
|--------|------|------|------|---------|
| `signing_and_sales_incentive_aug_beijing()` | jobs.py | 旧 | ❌ 不再使用 | data_processing_module, notification_module |
| `signing_and_sales_incentive_aug_shanghai()` | jobs.py | 旧 | ❌ 不再使用 | data_processing_module, notification_module |
| `signing_and_sales_incentive_sep_beijing()` | jobs.py | 旧 | ❌ 不再使用 | data_processing_module, notification_module |
| `signing_and_sales_incentive_sep_shanghai()` | jobs.py | 旧 | ❌ 不再使用 | data_processing_module, notification_module |

### 1.2 旧架构依赖的模块

#### 核心模块（仅旧架构使用）
```
modules/
├── data_processing_module.py      # 旧数据处理逻辑
├── notification_module.py         # 旧通知逻辑
└── data_utils.py                  # 旧工具函数（部分）
```

#### 配置常量（仅旧架构使用）
```
modules/config.py 中的旧常量：
- API_URL_BJ_AUG, API_URL_SH_AUG
- API_URL_BJ_SEP, API_URL_SH_SEP
- TEMP_CONTRACT_DATA_FILE_BJ_AUG/SEP
- PERFORMANCE_DATA_FILENAME_BJ_AUG/SEP
- STATUS_FILENAME_BJ_AUG/SEP
- 等等（共约30+个常量）
```

---

## 2. 详细的代码分析

### 2.1 data_processing_module.py 中的旧函数

**仅旧架构使用的函数** (~800行):
- `process_data_jun_beijing()` - 8月北京
- `process_data_shanghai_apr()` - 8月上海
- `process_data_shanghai_sep()` - 9月上海
- `process_data_sep_beijing()` - 9月北京
- `process_historical_contract()` - 历史合同处理
- `process_historical_contract_with_project_limit()` - 工单限额处理
- `is_historical_contract()` - 历史合同判断
- 以及其他辅助函数

**新架构也使用的函数** (~200行):
- `determine_lucky_number_reward_generic()` - 通用幸运数字
- `should_enable_badge()` - 徽章判断
- 其他通用工具函数

### 2.2 notification_module.py 中的旧函数

**仅旧架构使用的函数** (~300行):
- `notify_awards_jun_beijing()` - 8月北京通知
- `notify_awards_shanghai_generate_message_march()` - 8月上海通知
- `notify_awards_sep_beijing()` - 9月北京通知
- `notify_awards_shanghai_generic()` - 9月上海通知

**新架构也使用的函数** (~50行):
- `get_awards_mapping()` - 获取奖励映射
- `generate_award_message()` - 生成奖励消息

### 2.3 data_utils.py 中的函数

**所有函数都被新旧架构共用**:
- `save_to_csv_with_headers()` - CSV保存
- `archive_file()` - 文件归档
- `read_contract_data()` - 读取合同数据
- `collect_unique_contract_ids_from_file()` - 收集合同ID
- `write_performance_data()` - 写入性能数据
- 等等

**结论**: ✅ **data_utils.py 保留**（新架构仍在使用）

---

## 3. 移除计划（分阶段）

### 阶段1: 代码分析和验证 (1天)

**任务**:
1. [ ] 确认所有旧架构函数的完整列表
2. [ ] 验证新架构不依赖任何旧函数
3. [ ] 检查是否有其他文件导入旧函数
4. [ ] 创建详细的依赖关系图

**验证脚本**:
```bash
# 搜索所有对旧函数的引用
grep -r "process_data_jun_beijing\|process_data_shanghai_apr\|process_data_sep_beijing" --include="*.py" .
grep -r "notify_awards_jun_beijing\|notify_awards_sep_beijing" --include="*.py" .
```

### 阶段2: 代码提取和备份 (1天)

**任务**:
1. [ ] 从 `data_processing_module.py` 提取旧函数到 `legacy_data_processing.py`
2. [ ] 从 `notification_module.py` 提取旧函数到 `legacy_notification.py`
3. [ ] 创建 `legacy/` 目录存放所有旧代码
4. [ ] 提交备份分支 `backup/legacy-code`

**文件结构**:
```
legacy/
├── data_processing_module.py    # 旧数据处理函数
├── notification_module.py       # 旧通知函数
├── jobs.py                      # 旧job定义
└── README.md                    # 说明文档
```

### 阶段3: 清理主代码 (1-2天)

**任务**:
1. [ ] 从 `modules/data_processing_module.py` 删除旧函数
2. [ ] 从 `modules/notification_module.py` 删除旧函数
3. [ ] 从 `jobs.py` 删除旧job函数
4. [ ] 从 `modules/config.py` 删除旧常量
5. [ ] 更新 `main.py` 移除旧job调用

**具体删除项**:

#### modules/data_processing_module.py
- 删除 ~800行旧函数
- 保留 ~200行通用函数
- 保留所有导入和初始化

#### modules/notification_module.py
- 删除 ~300行旧函数
- 保留 ~50行通用函数
- 保留所有导入和初始化

#### jobs.py
- 删除 4个旧job函数（~150行）
- 保留 `generate_daily_service_report()` 和 `pending_orders_reminder_task()`

#### modules/config.py
- 删除 ~30个旧常量
- 保留所有新架构常量

### 阶段4: 测试和验证 (1-2天)

**任务**:
1. [ ] 运行所有新架构job（10月、11月）
2. [ ] 验证新架构功能完整
3. [ ] 检查是否有导入错误
4. [ ] 运行现有测试套件
5. [ ] 手工测试关键功能

**测试清单**:
- [ ] 北京10月job正常运行
- [ ] 北京11月job正常运行
- [ ] 上海10月job正常运行
- [ ] 上海11月job正常运行
- [ ] 日常服务报告job正常运行
- [ ] 待预约工单提醒job正常运行

---

## 4. 风险评估

### 4.1 低风险项

✅ **旧job函数删除**
- 已完全停用
- 无其他代码依赖
- 可快速回滚

✅ **旧配置常量删除**
- 仅旧job使用
- 新架构使用独立配置
- 可快速回滚

### 4.2 中等风险项

⚠️ **data_processing_module.py 清理**
- 需要确保通用函数保留
- 需要验证新架构不依赖旧函数
- 建议保留备份

⚠️ **notification_module.py 清理**
- 需要确保通用函数保留
- 需要验证新架构不依赖旧函数
- 建议保留备份

### 4.3 回滚方案

**快速回滚**:
```bash
# 如果出现问题，可以快速回滚
git revert <commit-hash>
```

**完整回滚**:
```bash
# 从备份分支恢复
git checkout backup/legacy-code -- legacy/
```

---

## 5. 执行检查清单

### 前置检查
- [ ] 所有新架构job已验证可用
- [ ] 没有其他代码依赖旧函数
- [ ] 已创建备份分支
- [ ] 已通知相关人员

### 执行步骤
- [ ] 阶段1: 代码分析完成
- [ ] 阶段2: 备份代码完成
- [ ] 阶段3: 清理代码完成
- [ ] 阶段4: 测试验证完成

### 后续维护
- [ ] 更新README文档
- [ ] 更新项目架构文档
- [ ] 清理过期的测试脚本
- [ ] 更新CI/CD配置

---

## 6. 预期收益

### 代码质量
- 📉 代码行数减少 ~1200行
- 📉 模块复杂度降低
- 📈 代码可维护性提升

### 开发效率
- ⏱️ 减少代码审查时间
- ⏱️ 减少新开发者学习成本
- ⏱️ 减少bug修复范围

### 系统性能
- 💾 减少内存占用
- 🚀 加快模块加载速度
- 🔧 简化依赖管理

---

## 7. 后续建议

1. **文档更新**
   - 更新README.md，移除旧架构说明
   - 更新项目架构文档
   - 添加迁移指南

2. **代码规范**
   - 建立新架构编码规范
   - 禁止添加旧架构代码
   - 建立代码审查流程

3. **监控告警**
   - 监控新架构job执行
   - 设置异常告警
   - 定期检查日志

---

## 附录: 旧函数完整列表

### data_processing_module.py (删除)
```
process_data_jun_beijing()
process_data_shanghai_apr()
process_data_shanghai_sep()
process_data_sep_beijing()
process_historical_contract()
process_historical_contract_with_project_limit()
is_historical_contract()
load_existing_new_contracts_from_performance_file()
[以及其他辅助函数]
```

### notification_module.py (删除)
```
notify_awards_jun_beijing()
notify_awards_shanghai_generate_message_march()
notify_awards_sep_beijing()
notify_awards_shanghai_generic()
[以及其他辅助函数]
```

### jobs.py (删除)
```
signing_and_sales_incentive_aug_beijing()
signing_and_sales_incentive_aug_shanghai()
signing_and_sales_incentive_sep_beijing()
signing_and_sales_incentive_sep_shanghai()
```

### modules/config.py (删除常量)
```
API_URL_BJ_AUG, API_URL_SH_AUG
API_URL_BJ_SEP, API_URL_SH_SEP
TEMP_CONTRACT_DATA_FILE_BJ_AUG/SEP
PERFORMANCE_DATA_FILENAME_BJ_AUG/SEP
STATUS_FILENAME_BJ_AUG/SEP
[以及其他相关常量]
```

---

**文档版本**: v1.0  
**创建日期**: 2025-10-28  
**状态**: 📋 待审核

