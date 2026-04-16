# 签约激励系统

自动化的签约激励系统，支持新旧架构并行运行，确保100%等价性。

## 🎯 项目状态

- ✅ **北京9月等价性验证**: 100%完成，新旧架构完全等价
- 🔄 **上海9月等价性验证**: 准备中
- 🏗️ **新架构**: 数据库优先，模块化设计，高性能
- 🔧 **旧架构**: 保持兼容，用于对比验证

## 🚀 快速开始

### 环境准备
```bash
cp .env.example .env
pip install -r requirements.txt
```

数据库模式切换：
- 本地开发：`DB_SOURCE=local`（默认，使用 `LOCAL_DB_PATH`）
- 线上生产：`DB_SOURCE=cloud`（使用 `TURSO_DB_URL` + `TURSO_AUTH_TOKEN`）

### 新架构（推荐）
```bash
# 北京签约播报（常驻，按月累计）
python -c "from modules.core.beijing_jobs import signing_broadcast_beijing_v2; signing_broadcast_beijing_v2()"

# 导出结果到CSV
python scripts/export_database_to_csv.py --activity BJ-SIGN-BROADCAST-2026-03 --compatible
```

### 旧架构（对比验证）
```bash
# 北京9月签约激励
python -c "from jobs import signing_and_sales_incentive_sep_beijing; signing_and_sales_incentive_sep_beijing()"
```

### 手动验证
```bash
# 查看当前活跃文档入口
cat docs/BACKLOG.md
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
├── scripts/                  # 运行脚本和工具
│   ├── run_scheduled_task.py # 本地定时任务入口
│   ├── local_webhook_sink.py # 本地 webhook 接收器
│   └── ...
├── tests/                    # 测试与手工验证
│   ├── unit/                 # 自动化单元测试
│   └── manual/               # 手工验证脚本
├── docs/                     # 文档
│   ├── BACKLOG.md            # 当前活跃文档入口
│   └── ARCHIVE_NOTICE.md     # 历史归档说明
└── state/                    # 状态文件
```

## 🎯 主要功能

- **北京签约播报**: 自动播报签约数据（仅播报，无奖励）
- **服务监控**: SLA违规监控和通知
- **工单提醒**: 待预约工单自动提醒
- **数据处理**: 合同数据自动化处理

## 📊 测试

自动化测试放在 `tests/unit/`，手工验证脚本放在 `tests/manual/`。

### 快速验证
```bash
# 运行所有自动化单测
python -m unittest discover -s tests/unit -p 'test_*.py'

# 运行单个测试文件
python -m unittest tests.unit.test_project_settlement_smartsheet_job

# 运行手工验证脚本
python tests/manual/beijing_november.py
```

## 📝 配置

配置文件位于 `config/` 目录下，包含：
- 环境配置 (.env文件)
- 奖励规则配置
- 通知配置

## 📖 文档

当前活跃文档入口是 `docs/BACKLOG.md`。`docs/` 目录中其余内容默认按历史归档资料处理；如需查找旧设计、旧实现或阶段性报告，请先看 `docs/ARCHIVE_NOTICE.md` 的说明。

## 🔧 开发

1. **修改代码后**: 先运行 `python -m unittest discover -s tests/unit -p 'test_*.py'`
2. **重要变更前**: 再运行对应的 `tests/manual/` 验证脚本
3. **部署前**: 确保相关测试和手工验证都通过

## 🤖 GitHub Actions 定时任务

当前由 Cloudflare Worker 统一保留一个 cron 心跳，再按北京时间路由触发 GitHub Actions workflow。

当前工作流：
- `.github/workflows/beijing-signing-broadcast.yml`
- `.github/workflows/project-settlement-smartsheet.yml`
- `.github/workflows/pending-orders-reminder.yml`
- `.github/workflows/daily-service-report.yml`

默认计划：
- 北京时间 `08:00-23:30` 每 30 分钟：执行北京签约播报
- 北京时间 `08:00-23:30` 每 30 分钟：执行项目结算电子表格同步
- 北京时间 `08:30`：额外执行待预约工单提醒
- 北京时间 `09:00`：额外执行 SLA 日报

请在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 配置：
- `TURSO_DB_URL`
- `TURSO_AUTH_TOKEN`
- `METABASE_USERNAME`
- `METABASE_PASSWORD`
- `WECOM_WEBHOOK_DEFAULT`
- `WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK`
- `CONTACT_PHONE_NUMBER`
- `API_URL_BJ_SIGN_BROADCAST`（可选，不填则使用默认值）
- `API_URL_PROJECT_SETTLEMENT_SMARTSHEET`（可选，不填则使用默认值）
- `METABASE_URL`（可选，不填则使用默认值）

## 📞 支持

如有问题请查看相关文档或联系开发团队。
