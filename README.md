# 签约激励系统

一个自动化的签约激励和服务监控系统，用于处理合同数据、计算奖励并发送通知。

## 🚀 快速开始

### 运行主程序
```bash
python main.py
```

### 快速测试
```bash
# 运行快速Mock测试（3秒内完成）
python tests/test_jobs_simple.py
```

## 📁 项目结构

```
├── main.py                   # 主程序入口
├── jobs.py                   # 任务定义
├── modules/                  # 核心模块
│   ├── config.py            # 配置管理
│   ├── data_processing_module.py  # 数据处理
│   ├── notification_module.py     # 通知发送
│   └── ...
├── tests/                    # 测试文件
│   ├── test_jobs_simple.py  # 快速集成测试
│   ├── test_data/           # Mock测试数据
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
