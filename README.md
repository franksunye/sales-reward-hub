# 签约激励系统

自动化的签约激励系统，支持新旧架构并行运行，确保100%等价性。

## 🎯 项目状态

- ✅ **北京9月等价性验证**: 100%完成，新旧架构完全等价
- 🔄 **上海9月等价性验证**: 准备中
- 🏗️ **新架构**: 数据库优先，模块化设计，高性能
- 🔧 **旧架构**: 保持兼容，用于对比验证

## 🚀 快速开始

### 新架构（推荐）
```bash
# 北京9月签约激励
python -c "from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2; signing_and_sales_incentive_sep_beijing_v2()"

# 导出结果到CSV
python scripts/export_database_to_csv.py --activity BJ-SEP --compatible
```

### 旧架构（对比验证）
```bash
# 北京9月签约激励
python -c "from jobs import signing_and_sales_incentive_sep_beijing; signing_and_sales_incentive_sep_beijing()"
```

### 手动验证
```bash
# 查看详细验证指南
cat docs/manual_validation_guide.md
```

## 📁 项目结构

```
├── modules/core/             # 新架构核心模块
│   ├── beijing_jobs.py      # 北京任务（新架构）
│   ├── shanghai_jobs.py     # 上海任务（新架构）
│   ├── data_models.py       # 数据模型
│   ├── storage.py           # 数据存储抽象层
│   └── processing_pipeline.py # 处理管道
├── jobs.py                   # 旧架构任务定义
├── scripts/                  # 验证和工具脚本
│   ├── export_database_to_csv.py # 数据库导出工具
│   ├── individual_sampling_validator.py # 个体抽样验证
│   └── ...
├── docs/                     # 文档
│   ├── manual_validation_guide.md # 手动验证指南
│   └── current_project_status.md  # 项目状态
├── baseline/                 # 基准数据
├── reports/                  # 验证报告
│   └── README_测试说明.md   # 详细测试说明
├── config/                   # 配置文件
├── docs/                     # 文档
├── scripts/                  # 工具脚本
└── state/                    # 状态文件
```

## 🎯 主要功能

- **签约激励计算**: 自动计算管家签约奖励
- **服务监控**: SLA违规监控和通知
- **工单提醒**: 待预约工单自动提醒
- **数据处理**: 合同数据自动化处理

## 📊 测试

详细的测试说明请查看 [tests/README_测试说明.md](tests/README_测试说明.md)

### 快速验证
```bash
# 运行所有核心任务的快速测试
python tests/test_jobs_simple.py
```

## 📝 配置

配置文件位于 `config/` 目录下，包含：
- 环境配置 (.env文件)
- 奖励规则配置
- 通知配置

## 📖 文档

详细文档位于 `docs/` 目录下，包含：
- 业务规则说明
- 配置指南
- 测试方法
- 版本历史

## 🔧 开发

1. **修改代码后**: 运行 `python tests/test_jobs_simple.py` 快速验证
2. **重要变更前**: 在测试环境运行真实任务验证
3. **部署前**: 确保所有测试通过

## 📞 支持

如有问题请查看相关文档或联系开发团队。
