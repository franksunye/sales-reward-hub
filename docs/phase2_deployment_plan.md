# 阶段2：生产部署和迁移执行计划

**计划版本**: v1.0  
**创建日期**: 2025-01-08  
**执行状态**: 🟡 待开始

## 🎯 阶段目标

将已完成的重构架构安全地部署到生产环境，通过影子模式验证后逐步迁移，最终实现全量切换。

## 📅 详细执行计划

### 第1周：影子模式部署

**目标**: 零风险验证新架构在生产环境的稳定性

#### Day 1: 代码合并和环境准备
- [ ] **合并重构分支**
  ```bash
  git checkout stable-maintenance
  git merge refactoring-phase1-core-architecture
  git push origin stable-maintenance
  ```
- [ ] **环境检查**
  - [ ] Python版本兼容性（>=3.7）
  - [ ] 磁盘空间（SQLite数据库）
  - [ ] 依赖库完整性
- [ ] **备份现有系统**
  ```bash
  cp -r modules modules_backup_$(date +%Y%m%d)
  cp jobs.py jobs_backup_$(date +%Y%m%d).py
  ```

#### Day 2-3: 影子模式配置
- [ ] **修改jobs.py实现影子模式**
  ```python
  def signing_and_sales_incentive_jun_beijing():
      """北京6月Job - 影子模式"""
      try:
          # 运行新系统（记录但不影响业务）
          from modules.core.beijing_jobs import signing_and_sales_incentive_jun_beijing_v2
          new_result = signing_and_sales_incentive_jun_beijing_v2()
          log_shadow_result("BJ-JUN", new_result)
          
          # 运行旧系统（保证业务连续性）
          old_result = original_signing_and_sales_incentive_jun_beijing()
          
          # 对比结果
          compare_and_log_differences("BJ-JUN", old_result, new_result)
          return old_result
          
      except Exception as e:
          logging.error(f"影子模式失败，使用旧系统: {e}")
          return original_signing_and_sales_incentive_jun_beijing()
  ```

#### Day 4-5: 监控和数据收集
- [ ] **设置监控指标**
  - 处理时间对比
  - 内存使用对比
  - 输出数据一致性
  - 错误率统计
- [ ] **运行影子模式**
  - 选择1-2个低风险Job进行影子模式测试
  - 收集至少3天的运行数据
- [ ] **分析结果**
  - 性能对比报告
  - 一致性验证报告
  - 问题和风险评估

#### Day 6-7: 影子模式扩展
- [ ] **扩展到更多Job**
  - 北京6月、8月
  - 上海4月
- [ ] **完整性验证**
  - 端到端业务流程测试
  - 通知发送功能验证
  - 异常处理验证

### 第2-3周：渐进式迁移

**目标**: 逐步替换现有Job函数，降低迁移风险

#### 第2周：低风险Job迁移
- [ ] **Day 1: 北京6月完全切换**
  ```python
  # 直接替换import
  from modules.core.beijing_jobs import signing_and_sales_incentive_jun_beijing_v2 as signing_and_sales_incentive_jun_beijing
  ```
- [ ] **Day 2-3: 监控和验证**
  - 业务指标监控
  - 用户反馈收集
  - 性能指标验证
- [ ] **Day 4-5: 北京8月迁移**
  - 同样的切换流程
  - 持续监控验证

#### 第3周：中高风险Job迁移
- [ ] **Day 1-2: 上海4月、8月迁移**
  - 上海Job函数切换
  - 重点验证housekeeper_key格式差异
- [ ] **Day 3-4: 北京9月迁移**
  - 历史合同处理验证
  - 个人序列幸运数字验证
  - 5万上限逻辑验证
- [ ] **Day 5: 上海9月迁移**
  - 双轨统计功能验证
  - 自引单奖励验证
  - 项目地址去重验证

### 第4周：全量迁移和清理

**目标**: 完成全部迁移，清理旧代码

#### Day 1-2: 全量验证
- [ ] **端到端测试**
  - 所有Job函数使用新架构
  - 完整业务流程验证
  - 性能基准测试

#### Day 3-4: 旧代码清理
- [ ] **删除旧函数**
  ```python
  # 删除以下函数
  # - process_data_jun_beijing
  # - process_data_shanghai_apr
  # - process_data_shanghai_sep
  # - process_data_sep_beijing_with_historical_support
  ```
- [ ] **清理配置**
  ```python
  # 删除旧配置变量
  # - PERFORMANCE_AMOUNT_CAP_BJ_FEB
  # - ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB
  # - SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB
  ```

#### Day 5: 文档更新和发布
- [ ] **更新文档**
  - API文档更新
  - 配置说明更新
  - 故障排查指南
- [ ] **版本发布**
  - 创建v2.0版本标签
  - 发布说明文档
  - 团队培训材料

## 📊 监控指标和成功标准

### 关键性能指标(KPI)
- **处理时间**: 新系统 ≤ 旧系统 × 1.2
- **内存使用**: 新系统 ≤ 旧系统 × 1.5
- **错误率**: < 1%
- **数据一致性**: 100%

### 业务连续性指标
- **服务可用性**: 99.9%
- **通知发送成功率**: ≥ 95%
- **数据处理完整性**: 100%

### 迁移成功标准
- [ ] 所有Job函数成功迁移到新架构
- [ ] 性能指标达到预期
- [ ] 无业务中断事件
- [ ] 用户反馈正面
- [ ] 旧代码完全清理

## 🚨 风险控制和应急预案

### 风险等级定义
- 🟢 **低风险**: 影子模式，不影响业务
- 🟡 **中风险**: 单个Job迁移，有回滚方案
- 🔴 **高风险**: 全量迁移，需要充分验证

### 应急回滚流程
1. **立即回滚**（30秒内）
   ```bash
   git checkout stable-maintenance-backup
   systemctl restart application
   ```
2. **问题诊断**（5分钟内）
   - 检查错误日志
   - 验证数据完整性
   - 评估影响范围
3. **修复和重试**（根据问题复杂度）
   - 修复代码问题
   - 重新测试验证
   - 制定重新部署计划

### 关键联系人
- **技术负责人**: Augment Agent
- **业务负责人**: Frank
- **应急联系**: 项目团队

## ✅ 执行检查清单

### 每日检查
- [ ] 系统运行状态正常
- [ ] 性能指标在预期范围内
- [ ] 无错误或异常报告
- [ ] 数据一致性验证通过

### 每周检查
- [ ] 迁移进度符合计划
- [ ] 风险控制措施有效
- [ ] 团队反馈和问题收集
- [ ] 下周计划调整和优化

### 阶段完成检查
- [ ] 所有计划任务完成
- [ ] 成功标准全部达成
- [ ] 文档更新完整
- [ ] 团队培训完成

---

**执行建议**: 严格按照计划执行，每个步骤都要有充分的验证和回滚准备。遇到问题及时沟通，不要强行推进。

**成功关键**: 渐进式迁移 + 充分监控 + 快速回滚能力
