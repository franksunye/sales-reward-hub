# 销售激励系统项目文档

## 📚 核心文档

### 🔧 重构计划
- [`final_refactoring_plan.md`](final_refactoring_plan.md) - **系统重构计划（最终版）**
  - 高层架构设计图（C4模型）
  - 深度问题分析和解决方案
  - 4阶段实施计划和质量保障

### 业务文档
- [`01_business_rules.md`](01_business_rules.md) - 业务规则和奖励计算逻辑
- [`06_configuration_guide.md`](06_configuration_guide.md) - 配置指南和最佳实践

### 开发文档
- [`04_roadmap.md`](04_roadmap.md) - 开发路线图和计划
- [`05_testing_approach.md`](05_testing_approach.md) - 测试方法和策略

### 项目管理
- [`project_management/`](project_management/) - 项目管理文档和标准规范

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
