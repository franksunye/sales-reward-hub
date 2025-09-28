# 更新日志

## [v2.1.0-stable-before-bj-oct] - 2025-01-28

### 版本说明
这是北京2025年10月销售激励活动开发前的稳定版本，包含完整的新架构实现和北京9月、上海9月的功能。

### 主要特性
- ✅ 新架构核心模块完整实现
- ✅ 北京9月销售激励活动（支持历史合同、幸运数字、节节高）
- ✅ 上海9月销售激励活动（双轨统计、自引单奖励、项目地址去重）
- ✅ 统一的配置驱动奖励计算系统
- ✅ 模块化的数据处理管道
- ✅ 抽象化的存储层（SQLite + CSV）
- ✅ 标准化的通知服务

### 技术架构
- **核心模块**: `modules/core/` 包含所有新架构组件
- **配置驱动**: 通过 `REWARD_CONFIGS` 实现业务差异化
- **数据模型**: 标准化的 `ContractData`、`PerformanceRecord` 等
- **处理管道**: `DataProcessingPipeline` 统一处理流程
- **存储抽象**: `PerformanceDataStore` 支持多种存储方式

### 已验证功能
- [x] 北京9月活动完整流程
- [x] 上海9月活动完整流程
- [x] 双轨统计准确性
- [x] 幸运数字计算正确性
- [x] 节节高奖励逻辑
- [x] 消息通知系统
- [x] 数据库存储一致性

### 文档完整性
- [x] 技术架构文档
- [x] 北京上海业务对比文档
- [x] 手动验证指南
- [x] 任务消息验证计划
- [x] 性能修复总结

## [即将发布] v2.2.0-bj-oct - 北京10月活动

### 计划新增功能
- 🔄 北京10月销售激励活动
- 🔄 混合奖励策略（幸运数字基于平台单，节节高基于总业绩）
- 🔄 双轨统计显示（平台单和自引单分别统计）
- 🔄 专用消息模板（结合北京和上海特色）
- 🔄 无自引单独立奖励（简化激励逻辑）

### 技术改进
- 🔄 扩展 `RewardCalculator` 支持 `platform_only` 幸运数字
- 🔄 扩展 `NotificationService` 支持北京10月消息模板
- 🔄 新增 `signing_and_sales_incentive_oct_beijing_v2` Job函数
- 🔄 完善配置验证和错误处理

### 开发分支
- **功能分支**: `feature/beijing-october-2025`
- **基于版本**: `v2.1.0-stable-before-bj-oct`
- **目标分支**: `production-db-v2`

---

## 版本管理说明

### 分支策略
- `main`: 主分支，保持与最新稳定版本同步
- `production-db-v2`: 生产分支，包含新架构的稳定版本
- `feature/beijing-october-2025`: 北京10月活动开发分支
- `stable-maintenance`: 维护分支，用于紧急修复

### 标签规范
- `v{major}.{minor}.{patch}`: 正式发布版本
- `v{version}-stable-{description}`: 稳定版本标记
- `v{version}-{feature}`: 功能版本标记
- `milestone-{description}`: 里程碑标记

### 发布流程
1. 功能开发在 `feature/*` 分支
2. 通过 Pull Request 合并到 `production-db-v2`
3. 代码审查和测试验证
4. 创建发布标签
5. 部署到生产环境

---

**维护者**: 技术团队  
**最后更新**: 2025-01-28  
**下次更新**: 北京10月功能发布后
