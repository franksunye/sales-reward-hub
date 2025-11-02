# 上海10月活动实施检查清单

## 前置确认事项

### 数据源确认 ✅
- [x] 确认上海10月API端点：复用上海9月的数据源
- [x] 确认包含 `sourceType` 字段（1=自引单，2=平台单）
- [x] 确认包含 `projectAddress` 字段（自引单去重用）
- [x] 确认数据格式与上海9月一致

### 业务规则确认 ✅
- [x] 幸运数字：禁用
- [x] 节节高：基于平台单业绩，5个合同门槛
- [x] 自引单奖励：**禁用**（关键差异）
- [x] 消息格式：**不显示自引单信息**（关键差异）

## 开发任务清单

### 阶段1：配置验证 ✅
- [x] 修改 `modules/config.py` 中的 `SH-2025-10` 配置
  - [x] 设置 `self_referral_rewards.enable: False`
  - [x] 设置 `reward_calculation_strategy.type: "single_track"`
  - [x] 确认奖励阶梯和金额映射
  - [x] 修正注释：单轨激励

### 阶段2：核心代码扩展
- [ ] 扩展 `modules/core/notification_service.py`
  - [ ] 添加 `SH-2025-10` 专用消息模板
  - [ ] 隐藏自引单统计信息显示
  - [ ] 复用上海标准消息格式
- [ ] 扩展 `modules/core/shanghai_jobs.py`
  - [ ] 添加 `signing_and_sales_incentive_oct_shanghai_v2` 函数
  - [ ] 复用现有数据获取逻辑 `_get_shanghai_contract_data`
  - [ ] 设置正确的配置参数

### 阶段3：测试开发
- [ ] 创建单元测试
  - [ ] 测试消息模板生成（不显示自引单）
  - [ ] 测试自引单奖励禁用逻辑
  - [ ] 测试平台单奖励计算
- [ ] 创建集成测试
  - [ ] 完整数据处理流程测试
  - [ ] 通知发送测试
- [ ] 创建手工测试脚本
  - [ ] 真实数据验证脚本

### 阶段4：部署准备
- [ ] 代码审查
- [ ] 文档更新
- [ ] 部署脚本准备

## 关键实现要点

### 1. 配置差异总结
```python
# 上海9月 vs 上海10月的关键差异
"SH-2025-09": {
    "self_referral_rewards": {"enable": True},   # 启用自引单奖励
    "reward_calculation_strategy": {"type": "dual_track"}  # 双轨
}

"SH-2025-10": {
    "self_referral_rewards": {"enable": False},  # 禁用自引单奖励
    "reward_calculation_strategy": {"type": "single_track"}  # 单轨
}
```

### 2. 消息模板差异
```
上海9月消息（显示自引单）：
🌻 个人平台单累计签约第 X 单， 自引单累计签约第 Y 单。
🌻 个人平台单金额累计签约 XXX 元，自引单金额累计签约 YYY元
🌻 个人平台单转化率 Z%，

上海10月消息（不显示自引单）：
🌻 个人平台单累计签约第 X 单。
🌻 个人平台单金额累计签约 XXX 元
🌻 个人平台单转化率 Z%，
（不显示自引单行，不显示"累计计入业绩"信息）
```

### 3. 数据处理逻辑
- **数据收集**：正常收集平台单和自引单数据
- **奖励计算**：只计算平台单奖励，忽略自引单奖励
- **消息生成**：只显示平台单统计，隐藏自引单统计
- **通知发送**：正常发送，但内容简化

## 技术实现细节

### NotificationService扩展
```python
elif self.config.config_key == "SH-2025-10":
    # 上海10月专用消息模板 - 不显示自引单信息，不显示业绩信息
    order_type = record.get("工单类型", "平台单")
    platform_count = record.get("平台单累计数量", 0)
    platform_amount = self._format_amount(record.get("平台单累计金额", 0))
    conversion_rate = self._format_rate(record.get("转化率(conversion)", ""))

    msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {record["管家(serviceHousekeeper)"]} 签约合同（{order_type}） {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {record.get("活动期内第几个合同", 0)} 单，

🌻 个人平台单累计签约第 {platform_count} 单。
🌻 个人平台单金额累计签约 {platform_amount} 元

🌻 个人平台单转化率 {conversion_rate}，

👊 {next_msg} 🎉🎉🎉。
'''
```

### Job函数实现
```python
def signing_and_sales_incentive_oct_shanghai_v2() -> List[PerformanceRecord]:
    """上海10月销售激励任务（重构版）"""
    logging.info("开始执行上海10月销售激励任务（重构版）")
    
    try:
        # 创建标准处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="SH-2025-10",
            activity_code="SH-OCT", 
            city="SH",
            housekeeper_key_format="管家_服务商",
            storage_type="sqlite",
            enable_dual_track=False,  # 不启用双轨统计显示
            db_path="performance_data.db"
        )
        
        # 复用上海数据获取逻辑
        contract_data = _get_shanghai_contract_data()
        
        # 处理数据
        records = pipeline.process_contracts(contract_data)
        
        # 发送通知
        _send_notifications(records, config)
        
        return records
        
    except Exception as e:
        logging.error(f"上海10月销售激励任务执行失败: {e}")
        raise
```

## 测试验证要点

### 1. 功能测试
- [ ] 平台单奖励计算正确
- [ ] 自引单不产生奖励通知
- [ ] 消息模板不包含自引单信息
- [ ] 节节高奖励阈值正确

### 2. 集成测试
- [ ] 完整数据处理流程
- [ ] 通知发送成功
- [ ] 数据库记录正确

### 3. 兼容性测试
- [ ] 不影响上海9月功能
- [ ] 不影响其他城市活动
- [ ] 配置隔离有效

## 部署检查清单

### 代码变更文件
- [ ] `modules/config.py` - 配置修正
- [ ] `modules/core/notification_service.py` - 消息模板扩展
- [ ] `modules/core/shanghai_jobs.py` - Job函数添加
- [ ] `tests/test_shanghai_october_*.py` - 测试文件
- [ ] `scripts/manual_test_shanghai_october.py` - 手工测试脚本

### 部署后验证
- [ ] 运行手工测试脚本
- [ ] 检查消息格式正确性
- [ ] 验证自引单不产生奖励
- [ ] 监控系统运行状态

## 风险控制

### 低风险确认
- ✅ **配置隔离**：SH-2025-10独立配置
- ✅ **代码复用**：基于成熟的上海9月逻辑
- ✅ **最小修改**：仅添加消息模板和Job函数
- ✅ **向后兼容**：不影响现有功能

### 回滚方案
- 如有问题，可快速回滚到上海9月配置
- 独立的Job函数，不影响其他活动
- 配置驱动，可通过配置快速调整

## 上线时间规划

### 开发阶段（预计2-3天）
- Day 1: 代码扩展和基础测试
- Day 2: 集成测试和手工验证
- Day 3: 代码审查和部署准备

### 部署阶段（预计1天）
- 代码合并和部署
- 功能验证和监控
- 问题修复（如有）

## 成功标准

### 功能标准
- [x] 配置正确设置
- [ ] 平台单奖励正常发放
- [ ] 自引单不产生奖励
- [ ] 消息格式符合要求
- [ ] 系统运行稳定

### 业务标准
- [ ] 用户体验良好（消息简洁明了）
- [ ] 激励效果达到预期
- [ ] 无业务逻辑错误
- [ ] 数据统计准确
