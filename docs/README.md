# 销售激励系统 - 项目文档中心

**更新日期**: 2025-01-08
**当前分支**: `deployment-shadow-mode`
**项目状态**: 🎉 **重构完成，准备部署**

## 📚 文档导航

### 🎯 立即行动（最新）
- **[下一步行动指南](next_actions_guide.md)** - 立即可执行的影子模式部署指南
- **[阶段2部署计划](phase2_deployment_plan.md)** - 详细的生产部署执行计划

### 📊 项目状态（最新）
- **[项目状态报告](refactoring_status_report_2025_01_08.md)** - 重构进展和成就总结
- **[重构计划](practical_refactoring_plan.md)** - 完整的重构方案和进展更新

### 🏗️ 技术文档
- **[部署指南](../modules/core/DEPLOYMENT_GUIDE.md)** - 新架构部署指南
- **[验证报告](../modules/core/tests/comprehensive_equivalence_report.md)** - 等价性验证结果

### 📋 业务文档
- **[业务规则](01_business_rules.md)** - 业务规则和奖励计算逻辑
- **[配置指南](06_configuration_guide.md)** - 配置指南和最佳实践
- **[测试方法](05_testing_approach.md)** - 测试方法和策略
- **[项目路线图](04_roadmap.md)** - 项目路线图

### 📋 历史文档
- **[最终重构计划](final_refactoring_plan.md)** - 原始重构设计方案
- **[重构反思](refactoring_reflection_and_next_steps.md)** - 重构过程总结

### 项目管理
- [`project_management/`](project_management/) - 项目管理文档和标准规范

## 🌿 分支管理策略

### 当前分支结构
```
deployment-shadow-mode  ← 当前分支（用于影子模式部署）
├── stable-maintenance  ← 生产稳定版本
├── refactoring-phase1-core-architecture  ← 重构开发分支
└── main  ← 主分支
```

### 分支用途说明
- **`deployment-shadow-mode`**: 影子模式部署分支，包含完整的重构代码和原有代码
- **`stable-maintenance`**: 生产稳定版本，当前运行的代码
- **`refactoring-phase1-core-architecture`**: 重构开发分支，包含新架构代码
- **`main`**: 主分支，项目主线

## 🎯 当前重点

### ✅ 已完成
- 核心架构重建100%完成
- 全面等价性验证100%通过
- 生产部署方案就绪

### 🚀 下一步
- **立即执行**: 影子模式部署
- **短期目标**: 渐进式迁移
- **中期目标**: 全量切换和旧代码清理

## 📖 快速开始

### 1. 了解项目状态
阅读 [项目状态报告](refactoring_status_report_2025_01_08.md)

### 2. 查看行动计划
阅读 [下一步行动指南](next_actions_guide.md)

### 3. 执行部署
按照 [阶段2部署计划](phase2_deployment_plan.md) 执行

### 4. 技术细节
参考 [部署指南](../modules/core/DEPLOYMENT_GUIDE.md)

---

**使用建议**: 从 [下一步行动指南](next_actions_guide.md) 开始，它提供了立即可执行的具体步骤。

## 📁 归档文档

### 版本文档
- [`versions/v1.0.1/`](versions/v1.0.1/) - v1.0.1版本相关文档
  - 系统架构、配置指南、测试方法
  - 升级指南和分支版本说明

### 已完成项目
- [`completed/`](completed/) - 已完成的项目文档归档
  - 热修复项目文档
  - 升级计划文档
  - 历史项目管理文档

## 🚀 项目概述

销售激励系统是一个自动化的奖励计算和通知平台，主要功能包括：

- **数据获取**：从Metabase API自动获取合同数据
- **奖励计算**：基于配置的规则计算管家奖励
- **SLA监控**：监控服务商SLA违规情况并发送通知
- **通知发送**：自动向相关人员发送各类通知

## 🛠️ 技术栈

- **Python 3.8+** - 核心开发语言
- **SQLite** - 任务管理和数据存储
- **Schedule** - 任务调度
- **企业微信API** - 通知发送

## ⚡ 快速启动

```bash
# 启动主程序
python main.py

# 指定环境启动
python main.py --env dev

# 运行特定任务
python main.py --task beijing-may --run-once
```

---

**文档版本**: v2.0 | **更新日期**: 2025-08-14 | **维护者**: Frank & AI助手
