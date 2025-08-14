# Send Status 机制移除升级计划

## 1. 项目概述

### 1.1 升级目标
移除冗余的send_status文件机制，简化系统架构，保持现有功能完整性。

### 1.2 背景分析
当前系统存在三重状态跟踪机制：
- CSV文件的`'是否发送通知'`字段（业务层去重）
- send_status JSON文件（技术层去重）
- task_manager数据库（任务执行状态）

由于task_manager已接管消息发送管理，send_status机制已成为冗余。

### 1.3 升级范围
- **包含功能**：合同通知、技师状态变更通知
- **影响文件**：notification_module.py, file_utils.py, config.py, jobs.py
- **数据文件**：所有send_status_*.json文件

## 2. 风险评估与质量保证策略

### 2.1 关键风险识别

#### 高风险项
1. **消息重复发送**：移除去重机制可能导致重复通知
2. **消息丢失**：逻辑错误可能导致应发送的消息未发送
3. **技师状态变更功能中断**：该功能完全依赖send_status

#### 中风险项
1. **配置文件清理**：移除配置项可能影响其他引用
2. **历史数据处理**：现有send_status文件的处理

### 2.2 质量保证策略

#### 测试策略
1. **功能等价性测试**：确保重构前后功能完全一致
2. **边界条件测试**：重复数据、异常情况处理
3. **集成测试**：完整的端到端流程验证
4. **回归测试**：确保其他功能不受影响

#### 安全措施
1. **分阶段实施**：逐步移除，每阶段验证
2. **备份机制**：保留原始代码和数据文件
3. **回滚计划**：快速恢复机制
4. **监控机制**：升级后的功能监控

## 3. 详细实施计划

### 3.1 阶段一：准备和分析（1-2天）

#### 任务清单
- [ ] 完整代码审查，识别所有send_status使用点
- [ ] 创建当前功能的基准测试用例
- [ ] 备份现有send_status文件
- [ ] 分析技师状态变更功能的替代方案

#### 交付物
- 代码使用点清单
- 基准测试套件
- 技师状态变更重构方案

### 3.2 阶段二：技师状态变更功能重构（2-3天）

#### 重构方案
将技师状态变更的去重逻辑迁移到task_manager：

```python
# 新的实现方案
def notify_technician_status_changes(status_changes, status_filename=None):
    for change in status_changes:
        change_id = change[0]
        
        # 检查是否已存在相同change_id的已完成任务
        if not is_change_already_processed(change_id):
            create_task('send_wechat_message', company_name, message, 
                       business_id=change_id, business_type='technician_status')
            post_text_to_webhook(message)

def is_change_already_processed(change_id):
    # 查询task_manager数据库
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM tasks 
        WHERE business_id = ? AND business_type = 'technician_status' 
        AND status = 'completed'
    """, (change_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0
```

#### 任务清单
- [ ] 扩展task_manager数据库schema（添加business_id, business_type字段）
- [ ] 实现新的去重逻辑
- [ ] 创建技师状态变更专项测试
- [ ] 验证功能等价性

### 3.3 阶段三：合同通知功能简化（1-2天）

#### 简化方案
移除send_status检查，只依赖CSV字段：

```python
# 简化后的逻辑
def notify_awards_aug_beijing(performance_data_filename, status_filename=None):
    records = get_all_records_from_csv(performance_data_filename)
    updated = False

    for record in records:
        contract_id = record['合同ID(_id)']
        
        # 只检查CSV字段，移除send_status检查
        if record['是否发送通知'] == 'N':
            # 创建任务
            create_task('send_wecom_message', WECOM_GROUP_NAME_BJ_AUG, msg)
            
            if record['激活奖励状态'] == '1':
                jiangli_msg = generate_award_message(record, awards_mapping, "BJ")
                create_task('send_wechat_message', CAMPAIGN_CONTACT_BJ_AUG, jiangli_msg)
            
            # 只更新CSV字段
            record['是否发送通知'] = 'Y'
            updated = True

    if updated:
        write_performance_data_to_csv(performance_data_filename, records, list(records[0].keys()))
```

#### 任务清单
- [ ] 修改所有合同通知函数
- [ ] 移除send_status相关参数和调用
- [ ] 创建合同通知专项测试
- [ ] 验证去重逻辑正确性

### 3.4 阶段四：清理和优化（1天）

#### 清理范围
1. **文件清理**
   - 移除file_utils.py中的send_status相关函数
   - 清理config.py中的STATUS_FILENAME_*配置
   - 删除历史send_status文件

2. **代码清理**
   - 移除所有send_status相关导入
   - 清理函数参数中的status_filename
   - 更新函数文档

#### 任务清单
- [ ] 移除send_status相关函数和配置
- [ ] 清理历史数据文件
- [ ] 更新代码文档
- [ ] 执行完整回归测试

## 4. 测试计划

### 4.1 单元测试
- [ ] 技师状态变更去重逻辑测试
- [ ] 合同通知去重逻辑测试
- [ ] task_manager扩展功能测试

### 4.2 集成测试
- [ ] 完整的合同通知流程测试
- [ ] 完整的技师状态变更流程测试
- [ ] 重复数据处理测试
- [ ] 异常情况处理测试

### 4.3 性能测试
- [ ] 大量数据处理性能对比
- [ ] 数据库查询性能测试

### 4.4 用户验收测试
- [ ] 8月份活动通知功能验证
- [ ] 技师状态变更通知验证
- [ ] 消息发送准确性验证

## 5. 回滚计划

### 5.1 回滚触发条件
- 发现消息重复发送
- 发现消息丢失
- 功能异常或性能问题
- 用户验收失败

### 5.2 回滚步骤
1. 停止当前系统
2. 恢复原始代码版本
3. 恢复send_status文件
4. 重启系统并验证
5. 分析问题原因

### 5.3 回滚验证
- [ ] 原有功能完全恢复
- [ ] 数据一致性检查
- [ ] 消息发送功能正常

## 6. 监控和验证

### 6.1 升级后监控指标
- 消息发送成功率
- 重复消息数量
- 系统响应时间
- 错误日志数量

### 6.2 验证周期
- **第1天**：密集监控，每小时检查
- **第1周**：每日检查关键指标
- **第1月**：每周例行检查

## 7. 时间安排

| 阶段 | 时间 | 负责人 | 关键里程碑 |
|------|------|--------|------------|
| 阶段一 | 第1-2天 | 开发团队 | 完成分析和准备 |
| 阶段二 | 第3-5天 | 开发团队 | 技师功能重构完成 |
| 阶段三 | 第6-7天 | 开发团队 | 合同功能简化完成 |
| 阶段四 | 第8天 | 开发团队 | 清理和测试完成 |
| 验收 | 第9天 | 业务团队 | 用户验收通过 |

## 8. 成功标准

### 8.1 功能标准
- [ ] 所有现有通知功能正常工作
- [ ] 无消息重复发送
- [ ] 无消息丢失
- [ ] 系统性能无下降

### 8.2 代码质量标准
- [ ] 代码简化，可维护性提升
- [ ] 无冗余配置和文件
- [ ] 测试覆盖率≥90%
- [ ] 文档更新完整

### 8.3 业务标准
- [ ] 8月份活动通知正常
- [ ] 技师状态变更通知正常
- [ ] 用户体验无变化
- [ ] 运维复杂度降低

---

**文档版本**: v1.0  
**创建日期**: 2025-08-14  
**负责人**: Frank & AI Assistant  
**审核状态**: 待审核
