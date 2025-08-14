# 销售激励系统项目文档

## 版本说明

当前项目有两个主要版本：

### 📋 v1.0.1-stable (生产稳定版)
- **状态**: 生产环境运行中
- **特点**: 文件存储、硬编码配置、城市特定处理
- **文档**: [v1.0.1文档索引](#v101-stable-文档)

### 🚀 v2.0.0 (重构版)
- **状态**: 测试验证中
- **特点**: 双存储模式、环境变量、通用化架构
- **文档**: [v2.0文档索引](#v20-文档)

---

## v1.0.1-stable 文档

### 核心文档
- [`README_v1.0.1.md`](README_v1.0.1.md) - 稳定版概述和快速启动
- [`architecture_v1.0.1.md`](architecture_v1.0.1.md) - 系统架构和模块说明
- [`configuration_v1.0.1.md`](configuration_v1.0.1.md) - 配置指南和安全注意事项
- [`testing_v1.0.1.md`](testing_v1.0.1.md) - 测试方法和故障排除

### 升级指南
- [`upgrade_guide_v1_to_v2.md`](upgrade_guide_v1_to_v2.md) - v1.0.1到v2.0升级指南

## v2.0 文档

### 核心文档
- [`00_backlog.md`](00_backlog.md) - 当前待办事项
- [`03_system_architecture.md`](03_system_architecture.md) - v2.0系统架构
- [`06_configuration_guide.md`](06_configuration_guide.md) - v2.0配置指南
- [`05_testing_approach.md`](05_testing_approach.md) - v2.0测试方法

### 业务文档
- [`01_business_rules.md`](01_business_rules.md) - 业务规则和奖励计算逻辑

### 项目管理
- [`project_management/`](project_management/) - 项目管理文档和已完成项目归档

## 项目概述

销售激励系统是一个自动化的奖励计算和通知平台，主要功能包括：

1. **数据获取**：从Metabase API自动获取合同数据
2. **奖励计算**：基于配置的规则计算管家奖励
3. **SLA监控**：监控服务商SLA违规情况并发送通知
4. **通知发送**：自动向相关人员发送各类通知

## 技术栈

- **Python 3.8+** - 核心开发语言
- **CSV文件** - 数据存储 (v1.0.1)
- **SQLite** - 任务管理和数据存储 (v2.0)
- **Schedule** - 任务调度
- **企业微信API** - 通知发送

## 快速启动

### v1.0.1-stable (当前生产版本)
```bash
# 启动主程序
python main.py
```

### v2.0.0 (测试版本)
```bash
# 配置环境变量后启动
python main.py --env dev

# 或指定特定任务
python main.py --task beijing-may --run-once
```

## 版本选择指南

### 使用 v1.0.1-stable 如果：
- 需要生产环境稳定运行
- 偏好文件存储方式
- 不需要复杂的配置管理
- 希望快速部署和维护

### 升级到 v2.0.0 如果：
- 需要更好的安全性（环境变量）
- 希望使用数据库存储
- 需要更灵活的配置管理
- 计划扩展到更多城市/活动

---

**文档版本**: 双版本支持 | **更新日期**: 2025-05-17 | **维护者**: Frank & AI助手
