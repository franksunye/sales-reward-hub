# 9月份Job测试指南

**目标**: 分两步验证9月份Job新架构 - 先单独测试，再影子模式对比

## 🎯 测试策略

### 第1步: 单独执行测试
验证新架构的9月份Job可以独立正常运行

### 第2步: 影子模式对比
在确认单独执行正常后，配置影子模式进行新旧系统对比

## 📋 第1步: 单独执行测试

### 快速测试
```bash
# 测试北京9月Job
python test_september_jobs_standalone.py --beijing-only

# 测试上海9月Job  
python test_september_jobs_standalone.py --shanghai-only

# 测试两个Job
python test_september_jobs_standalone.py
```

### 直接调用测试
```bash
# 北京9月Job
cd modules/core
python beijing_jobs.py

# 上海9月Job
cd modules/core  
python shanghai_jobs.py
```

### 预期结果
- ✅ 无错误执行完成
- ✅ 输出处理记录数
- ✅ 显示执行时间
- ✅ 生成详细日志

### 验证重点
#### 北京9月Job
- [ ] 历史合同处理功能正常
- [ ] 个人序列幸运数字计算正确
- [ ] 5万上限逻辑生效
- [ ] 奖励类型分布合理

#### 上海9月Job
- [ ] 双轨统计功能正常
- [ ] 自引单奖励计算正确
- [ ] 项目地址去重生效
- [ ] 平台单vs自引单统计正确

## 📋 第2步: 影子模式配置

### 前提条件
- ✅ 第1步单独测试全部通过
- ✅ 确认新架构功能正常
- ✅ 准备好旧系统代码备份

### 配置步骤

#### 2.1 生成影子模式代码
```bash
# 生成影子模式配置代码
python setup_september_shadow_mode.py

# 预览模式（不修改文件）
python setup_september_shadow_mode.py --dry-run
```

#### 2.2 手动配置jobs.py
1. **备份原有函数**
   ```python
   # 将现有的函数内容复制到备份函数中
   def original_signing_and_sales_incentive_sep_beijing():
       # 原有的北京9月Job实现
       pass
   
   def original_signing_and_sales_incentive_sep_shanghai():
       # 原有的上海9月Job实现  
       pass
   ```

2. **替换为影子模式版本**
   - 使用生成的影子模式代码替换原有函数
   - 确保import路径正确
   - 保留所有错误处理

#### 2.3 测试影子模式
```bash
# 测试北京9月影子模式
python -c "from jobs import signing_and_sales_incentive_sep_beijing; signing_and_sales_incentive_sep_beijing()"

# 测试上海9月影子模式
python -c "from jobs import signing_and_sales_incentive_sep_shanghai; signing_and_sales_incentive_sep_shanghai()"
```

### 影子模式监控

#### 关键日志信息
```
🔄 [北京9月影子模式] 开始执行
🆕 [北京9月] 启动新系统...
✅ [北京9月] 新系统完成: 150 条记录, 耗时: 2.34秒
🔄 [北京9月] 启动旧系统...
✅ [北京9月] 旧系统完成: 150 条记录, 耗时: 3.45秒
📊 [北京9月] 性能对比: 新系统/旧系统 = 0.68
✅ [北京9月] 影子模式验证通过
```

#### 成功标准
- [ ] 新旧系统都正常执行
- [ ] 记录数完全一致
- [ ] 性能对比合理（新系统 ≤ 旧系统 × 1.2）
- [ ] 验证逻辑通过
- [ ] 无业务中断

#### 异常处理
- 新系统失败时自动使用旧系统
- 完整的错误日志记录
- 业务流程不受影响

## 🚨 风险控制

### 安全保障
- ✅ **零业务风险**: 影子模式始终返回旧系统结果
- ✅ **自动回退**: 新系统失败时自动使用旧系统
- ✅ **完整备份**: 原有代码完整备份
- ✅ **快速回滚**: 30秒内可恢复原状

### 回滚方案
如果发现问题：
1. **立即回滚**
   ```python
   # 注释掉新系统调用
   # new_result = signing_and_sales_incentive_sep_beijing_v2()
   
   # 直接返回旧系统结果
   return original_signing_and_sales_incentive_sep_beijing()
   ```

2. **完全回滚**
   ```bash
   # 恢复备份文件
   cp jobs_backup_YYYYMMDD_HHMMSS.py jobs.py
   ```

## 📊 验证清单

### 第1步完成标准
- [ ] 北京9月Job单独执行成功
- [ ] 上海9月Job单独执行成功
- [ ] 处理记录数合理
- [ ] 执行时间可接受
- [ ] 关键业务逻辑正确

### 第2步完成标准
- [ ] 影子模式配置成功
- [ ] 新旧系统并行运行
- [ ] 结果一致性验证通过
- [ ] 性能对比满足要求
- [ ] 连续运行稳定

## 📅 建议时间安排

### Day 1: 单独测试
- **上午**: 运行单独测试脚本
- **下午**: 验证结果，修复问题（如有）

### Day 2: 影子模式配置
- **上午**: 配置影子模式
- **下午**: 测试影子模式运行

### Day 3-7: 监控验证
- **每日**: 检查影子模式运行状态
- **收集**: 性能和一致性数据
- **分析**: 验证结果和优化建议

## 🎯 下一步计划

影子模式验证成功后：
1. **扩展到其他Job**: 6月、8月Job迁移
2. **全量迁移**: 完全切换到新架构
3. **旧代码清理**: 删除旧实现
4. **文档更新**: 更新技术文档

---

**开始建议**: 先运行 `python test_september_jobs_standalone.py` 进行第1步测试
