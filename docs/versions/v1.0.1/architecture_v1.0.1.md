# 系统架构 v1.0.1-stable

## 系统概述
v1.0.1-stable版本采用简单直接的架构，以文件存储为主，城市特定的处理逻辑。

## 程序入口

### 主程序 (main.py)
- **启动方式**: `python main.py`
- **核心功能**: 
  - 基于当前月份自动选择任务
  - 定时任务调度 (每3分钟)
  - 日报任务调度 (每天11点)
  - 任务调度器线程管理

### 任务调度逻辑
```python
if current_month == 4:
    # 4月执行上海和北京4月任务
elif current_month == 5:
    # 5月执行上海和北京5月任务
```

## 核心模块

### 1. 任务系统 (jobs.py)
当前活跃任务：
- `signing_and_sales_incentive_may_beijing()` - 北京5月活动
- `signing_and_sales_incentive_apr_beijing()` - 北京4月活动
- `signing_and_sales_incentive_may_shanghai()` - 上海5月活动
- `check_technician_status()` - 技师状态检查
- `generate_daily_service_report()` - SLA监控报告

### 2. 数据处理模块 (data_processing_module.py)
**城市特定处理函数**：
- `process_data_may_beijing()` - 北京5月数据处理
- `process_data_apr_beijing()` - 北京4月数据处理  
- `process_data_shanghai_apr()` - 上海数据处理

**核心功能**：
- 合同数据转换
- 重复合同检查
- 奖励计算逻辑
- 业绩金额上限处理

### 3. 配置系统 (config.py)
**硬编码配置**：
```python
# 敏感信息直接配置
METABASE_USERNAME = 'wangshuang@xlink.bj.cn'
METABASE_PASSWORD = 'xlink123456'
WEBHOOK_URL_DEFAULT = 'https://qyapi.weixin.qq.com/...'

# 奖励规则配置
REWARD_CONFIGS = {
    "BJ-2025-05": {...},
    "SH-2025-05": {...}
}
```

### 4. 通知系统 (notification_module.py)
**城市特定通知函数**：
- `notify_awards_may_beijing()` - 北京5月通知
- `notify_awards_apr_beijing()` - 北京4月通知
- `notify_awards_shanghai_generate_message_march()` - 上海通知

### 5. 数据处理工具 (data_utils.py)
- CSV文件读写
- 数据归档
- 状态文件管理
- 时间处理函数
- 数据格式化函数
- 消息格式化函数

## 数据流架构

### 核心数据流
```
Metabase API → 临时CSV → 数据处理 → 业绩CSV → 通知发送
```

### 文件存储结构
```
state/
├── ContractData-BJ-Apr.csv      # 北京4月合同数据
├── ContractData-BJ-May.csv      # 北京5月合同数据
├── ContractData-SH-May.csv      # 上海5月合同数据
├── PerformanceData-BJ-Apr.csv   # 北京4月业绩数据
├── PerformanceData-BJ-May.csv   # 北京5月业绩数据
├── PerformanceData-SH-May.csv   # 上海5月业绩数据
└── send_status_*.json           # 发送状态记录
```

## 奖励计算逻辑

### 幸运数字奖励
```python
def determine_lucky_number_reward(contract_number, amount, lucky_number):
    if lucky_number in str(contract_number % 10):
        if amount >= 10000:
            return "幸运数字", "接好运万元以上"
        else:
            return "幸运数字", "接好运"
```

### 节节高奖励
- **北京**: 3档奖励 (达标奖、优秀奖、精英奖)
- **上海**: 4档奖励 (基础奖、达标奖、优秀奖、精英奖)

## 任务调度

### Schedule调度
```python
# 主任务每3分钟执行
schedule.every(3).minutes.do(run_jobs_serially)

# 日报任务每天11点执行
schedule.every().day.at("11:00").do(daily_service_report_task)
```

### 任务调度器 (task_scheduler.py)
- 异步消息发送
- 任务状态管理
- 错误处理和重试

## 技术特点

### 优势
- **简单直接**: 逻辑清晰，易于理解
- **稳定可靠**: 生产环境验证
- **文件存储**: 数据可视化，便于调试
- **城市特定**: 针对性强，逻辑明确

### 限制
- **硬编码配置**: 敏感信息暴露
- **重复代码**: 城市间逻辑重复
- **扩展性**: 新增城市需要修改代码
- **文件依赖**: 依赖文件系统状态

## 部署信息

### 环境要求
- Windows Server (生产环境)
- Python 3.8+
- 文件系统读写权限

### 启动方式
```bash
# 生产环境
python main.py

# 开发测试 (修改main.py中的注释)
# 取消注释特定任务进行单独测试
```

### 监控和维护
- 日志文件: `logs/app.log`
- 业绩数据: `state/PerformanceData-*.csv`
- 发送状态: `state/send_status_*.json`
- 错误处理: 自动重试机制

---

**架构版本**: v1.0.1-stable | **更新日期**: 2025-05-17 | **状态**: 生产稳定
