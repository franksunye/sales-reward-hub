# 销售激励系统 - 文档中心

**更新日期**: 2025-09-22  
**当前分支**: `deployment-shadow-mode`  
**项目状态**: 🔍 **新旧架构等价性验证中**

## 📋 核心文档

### 🎯 验证和部署
- **[验证主计划](validation_master_plan.md)** - 新旧架构等价性验证的完整计划
- **[验证执行指南](validation_execution_guide.md)** - 具体的验证执行步骤和工具使用
- **[执行摘要](validation_executive_summary.md)** - 验证工作的核心发现和建议

### 📊 项目状态
- **[当前项目状态](current_project_status.md)** - 项目最新进展和状态

## 🛠️ 验证工具

### 主要验证脚本
- `../scripts/comprehensive_equivalence_validator.py` - 全面等价性验证工具
- `../scripts/new_architecture_validator.py` - 新架构验证工具
- `../scripts/simple_new_arch_test.py` - 简化的新架构测试工具

### 分析工具
- `../scripts/config_consistency_validator.py` - 配置一致性验证
- `../scripts/code_redundancy_analyzer.py` - 代码冗余分析
- `../scripts/document_organizer.py` - 文档整理工具

## 📈 验证报告

最新的验证报告保存在 `../reports/` 目录下。

## 📁 归档文档

### 历史验证报告
- `archived/validation_reports/` - 已完成的验证报告
  - 北京架构等价性验证报告
  - 上海架构等价性验证报告
  - 历史合同修复报告

### 历史计划文档
- `archived/old_plans/` - 历史计划文档
  - 集成测试主计划
  - 阶段1验证计划（北京、上海）

## 🎯 当前重点

### ✅ 已完成
- 新架构开发完成
- 配置一致性分析完成
- 代码冗余分析完成
- 文档整理完成

### 🚀 进行中
- 新架构功能验证
- 北京9月等价性验证
- 上海9月等价性验证

### 📅 下一步
- 跨城市兼容性验证
- 最终部署准备
- 生产环境切换

## 📖 快速开始

### 1. 了解验证计划
阅读 [验证主计划](validation_master_plan.md)

### 2. 执行验证
按照 [验证执行指南](validation_execution_guide.md) 分步执行

### 3. 查看验证结果
参考 [执行摘要](validation_executive_summary.md) 了解核心发现

## 🏗️ 系统架构

### 旧架构
- 单体函数处理：`jobs.py` 中的各个job函数
- 传统数据处理模块：`modules/data_processing_module.py`
- 配置管理：`modules/config.py`

### 新架构
- 模块化设计：`modules/core/` 目录下的各个模块
- 数据模型：`modules/core/data_models.py`
- 处理管道：`modules/core/pipeline_factory.py`
- 奖励计算器：`modules/core/reward_calculator.py`
- 配置适配器：`modules/core/config_adapter.py`

## 🔧 技术栈

- **Python 3.7+** - 核心开发语言
- **SQLite** - 数据存储
- **pandas** - 数据处理（旧架构）
- **企业微信API** - 通知发送

---

**维护者**: Frank & Augment Agent  
**文档版本**: v3.0 (清理后版本)
