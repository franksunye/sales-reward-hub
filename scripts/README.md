# 脚本工具说明

## 清空旧系统数据

### 用途
清空旧系统的所有数据文件，为新系统部署做准备。

### 使用方法

#### 1. 预览模式（推荐先运行）
```bash
python scripts/clear_old_system_data.py
```
显示将要删除的文件，不实际删除。

#### 2. 执行清理
```bash
python scripts/clear_old_system_data.py --confirm
```
实际删除所有旧系统数据文件。

#### 3. 保留归档文件
```bash
python scripts/clear_old_system_data.py --confirm --keep-archive
```
清理数据但保留归档目录。

#### 4. 分类清理
```bash
# 只清理北京地区数据
python scripts/clear_old_system_data.py --confirm --category beijing

# 只清理数据库文件
python scripts/clear_old_system_data.py --confirm --category database

# 只清理测试文件
python scripts/clear_old_system_data.py --confirm --category test
```

### 清理的文件类型

#### 北京地区数据
- `state/ContractData-BJ-*.csv` - 合同数据
- `state/PerformanceData-BJ-*.csv` - 业绩数据
- `state/send_status_bj_*.json` - 发送状态

#### 上海地区数据
- `state/ContractData-SH-*.csv` - 合同数据
- `state/PerformanceData-SH-*.csv` - 业绩数据
- `state/send_status_sh_*.json` - 发送状态

#### 系统文件
- `metabase_session.json` - Metabase会话
- `state/pending_orders_reminder_status.json` - 待预约提醒状态
- `state/daily_service_report_record.*` - 日报记录
- `state/sla_violations.json` - SLA违规记录

#### 数据库文件
- `performance_data.db` - 新系统数据库
- `tasks.db` - 任务数据库

#### 测试文件
- `modules/core/performance_data_*.csv` - 测试输出
- `modules/core/tests/performance_data_*.csv` - 测试数据

#### 归档文件
- `archive/` - 整个归档目录

### 安全提示
- 建议先运行预览模式查看要删除的文件
- 重要数据请提前备份
- 清理后无法恢复，请谨慎操作

### 示例输出
```
🔍 预览模式 - 显示将要删除的文件
🗂️  清理 beijing 文件...
  [DRY RUN] 将删除: state/PerformanceData-BJ-Sep.csv
  [DRY RUN] 将删除: state/send_status_bj_sep.json
🗂️  清理归档目录...
  [DRY RUN] 将删除: archive/state/ContractData-BJ-Sep_202509151257.csv
🔍 预览完成 - 使用 --confirm 参数实际执行清理
```
