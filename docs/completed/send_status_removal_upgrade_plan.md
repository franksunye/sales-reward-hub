# Send Status 机制移除升级计划（合同通知专项）

## 1. 项目概述

### 1.1 升级目标
移除合同通知功能中冗余的send_status文件机制，优化消息发送状态管理，确保生成消息和发送消息状态的准确标识。

### 1.2 背景分析
当前合同通知系统存在三重状态跟踪机制：
- CSV文件的`'是否发送通知'`字段（业务层去重）
- send_status JSON文件（技术层去重）
- task_manager数据库（任务执行状态）

**核心问题**：存在消息生成与实际发送的时间差，导致状态不一致风险：
- 任务创建后立即更新CSV和send_status为"已发送"
- 但实际发送是异步的，如果系统重启可能导致消息未实际发送但状态已标记为发送

### 1.3 升级范围
- **包含功能**：仅限合同通知功能
- **排除功能**：技师状态变更通知（使用独立的send_status机制，不在本次升级范围）
- **影响文件**：notification_module.py, file_utils.py, config.py, jobs.py, task_manager.py, task_scheduler.py
- **数据库变更**：tasks表添加metadata字段
- **数据文件**：合同相关的send_status_*.json文件（如send_status_bj_aug.json等）

## 2. 风险评估与质量保证策略

### 2.1 关键风险识别

#### 高风险项
1. **消息重复发送**：移除去重机制可能导致重复通知
2. **消息丢失**：逻辑错误可能导致应发送的消息未发送
3. **状态不一致**：生成消息与实际发送的时间差导致状态标识错误
4. **系统恢复问题**：重启后pending任务的正确处理

#### 中风险项
1. **配置文件清理**：移除配置项可能影响其他引用
2. **历史数据处理**：现有合同相关send_status文件的处理
3. **数据库结构变更**：tasks表添加metadata字段的兼容性

#### 低风险项
1. **技师状态变更功能**：该功能使用独立的send_status机制，不受本次升级影响

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

### 3.1 阶段一：准备和数据库升级（1-2天）

#### 任务清单
- [ ] 完整代码审查，识别合同通知中所有send_status使用点
- [ ] 创建合同通知功能的基准测试用例
- [ ] 备份现有合同相关send_status文件
- [ ] 确认技师状态变更功能不受影响
- [ ] 设计task_manager数据库扩展方案
- [ ] 实施数据库结构升级（添加metadata字段）
- [ ] 创建任务元数据管理函数

#### 交付物
- 合同通知send_status使用点清单
- 基准测试套件
- 影响范围确认报告
- 数据库升级脚本
- 任务元数据管理函数

### 3.2 阶段二：消息发送机制优化（2-3天）

#### 优化方案：延迟状态更新
实现真正的生成消息与发送消息状态分离：

```python
# 优化后的逻辑 - 生成阶段
def notify_awards_aug_beijing(performance_data_filename):
    records = get_all_records_from_csv(performance_data_filename)

    for record in records:
        contract_id = record['合同ID(_id)']

        # 只检查CSV字段，移除send_status检查
        if record['是否发送通知'] == 'N':
            # 检查是否已有该合同的pending任务
            if not has_pending_task_for_contract(contract_id):
                # 创建任务时包含合同元数据
                create_task_with_contract_id(
                    'send_wecom_message',
                    WECOM_GROUP_NAME_BJ_AUG,
                    msg,
                    contract_id,
                    performance_data_filename
                )

                if record['激活奖励状态'] == '1':
                    jiangli_msg = generate_award_message(record, awards_mapping, "BJ")
                    create_task_with_contract_id(
                        'send_wechat_message',
                        CAMPAIGN_CONTACT_BJ_AUG,
                        jiangli_msg,
                        contract_id,
                        performance_data_filename
                    )
            # 关键：不在这里更新CSV状态

# 优化后的逻辑 - 发送阶段
def execute_task_with_status_update(task):
    try:
        # 1. 发送消息
        if task['task_type'] == 'send_wechat_message':
            send_wechat_message(task['recipient'], task['message'])
        elif task['task_type'] == 'send_wecom_message':
            send_wecom_message(task['recipient'], task['message'])

        # 2. 发送成功后才更新CSV状态
        if task['metadata']:
            metadata = json.loads(task['metadata'])
            update_csv_notification_status(
                metadata['csv_file'],
                metadata['contract_id'],
                'Y'
            )

        # 3. 更新任务状态
        update_task(task['id'], 'completed')

    except Exception as e:
        update_task(task['id'], 'failed')
        logging.error(f"消息发送失败: {e}")
```

#### 任务清单
- [ ] 扩展task_manager支持任务元数据
- [ ] 实现has_pending_task_for_contract函数
- [ ] 实现create_task_with_contract_id函数
- [ ] 实现update_csv_notification_status函数
- [ ] 修改task_scheduler支持状态回写
- [ ] 修改所有合同通知函数（notify_awards_*系列）
- [ ] 移除合同通知函数中的send_status相关参数和调用
- [ ] 保留技师状态变更功能不变
- [ ] 创建合同通知专项测试
- [ ] 验证防重复生成逻辑正确性

### 3.3 阶段三：清理和优化（1天）

#### 清理范围
1. **配置清理**
   - 清理config.py中合同相关的STATUS_FILENAME_*配置
   - 保留技师状态变更的STATUS_FILENAME_TS配置
   - 删除历史合同send_status文件

2. **代码清理**
   - 移除合同通知函数中的send_status相关导入和调用
   - 保留file_utils.py中的send_status函数（技师功能仍需使用）
   - 清理合同通知函数参数中的status_filename
   - 更新相关函数文档

3. **系统优化**
   - 优化任务查询性能
   - 添加任务状态监控
   - 完善错误处理和重试机制

#### 任务清单
- [ ] 清理合同相关的send_status配置
- [ ] 删除历史合同send_status数据文件
- [ ] 优化任务查询和状态管理
- [ ] 添加任务执行监控和告警
- [ ] 更新代码文档
- [ ] 执行完整回归测试

## 4. 测试计划

### 4.1 单元测试
- [ ] 任务元数据管理功能测试
- [ ] has_pending_task_for_contract函数测试
- [ ] create_task_with_contract_id函数测试
- [ ] update_csv_notification_status函数测试
- [ ] 合同通知防重复生成逻辑测试
- [ ] 技师状态变更功能不受影响验证

### 4.2 集成测试
- [ ] 完整的合同通知流程测试（生成→发送→状态更新）
- [ ] 重复合同数据处理测试
- [ ] 系统重启后pending任务恢复测试
- [ ] 发送失败重试机制测试
- [ ] 异常情况处理测试
- [ ] 技师状态变更功能正常运行验证

### 4.3 性能测试
- [ ] 大量数据处理性能对比
- [ ] 数据库查询性能测试
- [ ] 任务元数据查询性能测试

### 4.4 状态一致性测试
- [ ] 消息生成与发送状态一致性验证
- [ ] 系统异常中断后状态恢复测试
- [ ] 并发任务处理状态一致性测试

### 4.5 用户验收测试
- [ ] 8月份合同通知功能验证
- [ ] 技师状态变更通知正常运行验证
- [ ] 消息发送准确性验证
- [ ] 无重复消息发送验证
- [ ] 消息发送状态准确性验证

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
| 阶段一 | 第1-2天 | 开发团队 | 完成分析、准备和数据库升级 |
| 阶段二 | 第3-5天 | 开发团队 | 消息发送机制优化完成 |
| 阶段三 | 第6天 | 开发团队 | 清理、优化和测试完成 |
| 验收 | 第7天 | 业务团队 | 用户验收通过 |

## 8. 成功标准

### 8.1 功能标准
- [ ] 所有合同通知功能正常工作
- [ ] 技师状态变更功能不受影响
- [ ] 无消息重复发送
- [ ] 无消息丢失
- [ ] 消息生成与发送状态准确标识
- [ ] 系统重启后任务正确恢复
- [ ] 系统性能无下降

### 8.2 代码质量标准
- [ ] 合同通知代码简化，可维护性提升
- [ ] 移除冗余的合同send_status配置和文件
- [ ] 保留必要的技师状态变更send_status机制
- [ ] 实现真正的生成消息与发送消息状态分离
- [ ] 任务元数据管理功能完善
- [ ] 测试覆盖率≥90%
- [ ] 文档更新完整

### 8.3 业务标准
- [ ] 8月份合同通知正常
- [ ] 技师状态变更通知正常
- [ ] 用户体验无变化
- [ ] 运维复杂度降低
- [ ] 消息发送状态可追溯性提升

### 8.4 技术标准
- [ ] 数据库结构升级成功
- [ ] 任务状态管理机制完善
- [ ] 错误处理和重试机制健壮
- [ ] 系统监控和告警完善

---

## 9. 附录：技术实现细节

### 9.1 数据库升级脚本
```sql
-- 添加metadata字段到tasks表
ALTER TABLE tasks ADD COLUMN metadata TEXT;

-- 创建索引优化查询性能
CREATE INDEX idx_tasks_metadata ON tasks(metadata);
CREATE INDEX idx_tasks_status_type ON tasks(status, task_type);
```

### 9.2 核心函数设计
```python
# 检查合同是否有pending任务
def has_pending_task_for_contract(contract_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM tasks
        WHERE status = 'pending'
        AND metadata LIKE ?
    """, (f'%"contract_id": "{contract_id}"%',))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# 创建带合同ID的任务
def create_task_with_contract_id(task_type, recipient, message, contract_id, csv_file):
    metadata = json.dumps({
        'contract_id': contract_id,
        'csv_file': csv_file,
        'created_by': 'contract_notification'
    })
    task = Task(task_type, recipient, message, metadata)
    task.save()
    return task

# 更新CSV通知状态
def update_csv_notification_status(csv_file, contract_id, status):
    records = get_all_records_from_csv(csv_file)
    updated = False

    for record in records:
        if record['合同ID(_id)'] == contract_id:
            record['是否发送通知'] = status
            updated = True
            break

    if updated:
        write_performance_data_to_csv(csv_file, records, list(records[0].keys()))
        logging.info(f"Updated notification status for contract {contract_id} to {status}")
```

---

**文档版本**: v3.0
**创建日期**: 2025-08-14
**更新日期**: 2025-08-14
**负责人**: Frank & AI Assistant
**审核状态**: 待审核
**更新说明**: 整合消息发送机制优化方案，实现生成消息与发送消息状态的准确分离
