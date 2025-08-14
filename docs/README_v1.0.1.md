# 销售激励系统 v1.0.1-stable

销售激励系统稳定版本，用于管理销售签约奖励活动的自动化计算和通知。

## 版本状态 (v1.0.1-stable)

✅ **生产稳定**：已在生产环境稳定运行  
✅ **文件存储**：使用CSV文件存储业绩数据  
✅ **城市特定**：每个城市有独立的处理逻辑  
✅ **功能完整**：支持奖励计算和通知发送  

## 核心功能

1. **数据获取**：从Metabase API自动获取合同数据
2. **奖励计算**：基于规则计算管家奖励（幸运数字奖、节节高奖）
3. **通知发送**：自动发送奖励通知到企业微信和微信
4. **技师监控**：监控技师状态变化
5. **SLA监控**：监控服务商违规情况

## 技术栈

- **Python 3.8+** - 核心开发语言
- **CSV文件** - 数据存储
- **Schedule** - 任务调度
- **企业微信API** - 通知发送

## 快速启动

```bash
# 启动主程序
python main.py

# 或使用批处理文件
start.bat
```

## 当前活动配置

系统支持以下活动：
- **北京2025年4月** (BJ-2025-04) - 幸运数字8，节节高奖励
- **北京2025年5月** (BJ-2025-05) - 幸运数字6，节节高奖励  
- **上海2025年5月** (SH-2025-05) - 幸运数字6，四档奖励体系

## 系统架构

### 主要模块
- `main.py` - 主程序入口和任务调度
- `jobs.py` - 定时任务定义
- `modules/data_processing_module.py` - 数据处理逻辑
- `modules/notification_module.py` - 通知发送
- `modules/config.py` - 配置管理

### 数据流程
```
Metabase API → CSV文件 → 数据处理 → 奖励计算 → 通知发送
```

## 配置说明

### 奖励配置
在 `modules/config.py` 中的 `REWARD_CONFIGS` 定义各城市奖励规则：

```python
"BJ-2025-05": {
    "lucky_number": "6",
    "lucky_rewards": {
        "base": {"name": "接好运", "threshold": 0},
        "high": {"name": "接好运万元以上", "threshold": 10000}
    },
    "tiered_rewards": {
        "min_contracts": 6,
        "tiers": [
            {"name": "达标奖", "threshold": 80000},
            {"name": "优秀奖", "threshold": 120000},
            {"name": "精英奖", "threshold": 160000}
        ]
    }
}
```

### 敏感信息配置
当前版本敏感信息直接配置在 `config.py` 中：
- Metabase用户名密码
- 企业微信Webhook地址
- 联系电话等

## 文件结构

```
├── main.py              # 主程序入口
├── jobs.py              # 定时任务定义
├── modules/             # 核心功能模块
│   ├── config.py        # 配置管理
│   ├── data_processing_module.py  # 数据处理
│   ├── notification_module.py     # 通知发送
│   └── file_utils.py    # 文件操作
├── state/               # 数据文件存储
├── logs/                # 日志文件
└── docs/                # 项目文档
```

## 测试方法

### 手动测试
```bash
# 在main.py中取消注释相应行进行单独测试
# signing_and_sales_incentive_may_beijing()
# signing_and_sales_incentive_apr_beijing()
# signing_and_sales_incentive_may_shanghai()
```

### 数据查看
- 业绩数据：`state/PerformanceData-*.csv`
- 日志文件：`logs/app.log`
- 发送状态：`state/send_status_*.json`

## 升级准备

### 从v1.0.1升级到v2.0的准备工作：

1. **环境变量迁移**：将敏感信息迁移到环境变量
2. **数据库支持**：可选择启用数据库存储模式
3. **通用化处理**：使用配置驱动的通用处理函数
4. **功能验证**：确保新旧版本功能等价

### 建议的升级路径：
1. 在测试环境验证v2.0功能
2. 准备环境变量配置
3. 进行数据迁移测试
4. 逐步切换到新版本

---

**版本**: v1.0.1-stable | **更新**: 2025-05-17 | **状态**: 生产稳定
