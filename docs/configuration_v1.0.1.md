# 配置指南 v1.0.1-stable

## 配置概述
v1.0.1-stable版本使用硬编码配置，所有配置项直接写在 `modules/config.py` 文件中。

## 核心配置项

### 敏感信息配置
```python
# 数据源配置
METABASE_URL = 'http://metabase.fsgo365.cn:3000'
METABASE_USERNAME = 'wangshuang@xlink.bj.cn'
METABASE_PASSWORD = 'xlink123456'

# 企业微信通知
WEBHOOK_URL_DEFAULT = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=689cebff-3328-4150-9741-fed8b8ce4713'
WEBHOOK_URL_CONTACT_TIMEOUT = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=80ab1f45-2526-4b41-a639-c580ccde3e2f'

# 联系信息
PHONE_NUMBER = '15327103039'
```

### 奖励规则配置
```python
REWARD_CONFIGS = {
    "BJ-2025-05": {
        "lucky_number": "6",
        "lucky_rewards": {
            "base": {"name": "接好运", "threshold": 0},
            "high": {"name": "接好运万元以上", "threshold": 10000}
        },
        "performance_limits": {
            "single_project_limit": 100000,
            "enable_cap": True,
            "single_contract_cap": 100000
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
}
```

### API地址配置
```python
# 北京地区API
API_URL_BJ_APR = METABASE_URL + "/api/card/1616/query"  # 4月
API_URL_BJ_MAY = METABASE_URL + "/api/card/1693/query"  # 5月

# 上海地区API
API_URL_SH_MAY = METABASE_URL + "/api/card/1617/query"  # 5月

# 技师状态检查
API_URL_TS = "http://metabase.fsgo365.cn:3000/api/card/719/query"

# 日报服务
API_URL_DAILY_SERVICE_REPORT = METABASE_URL + "/api/card/1514/query"
```

### 文件路径配置
```python
# 北京4月
TEMP_CONTRACT_DATA_FILE_BJ_APR = 'state/ContractData-BJ-Apr.csv'
PERFORMANCE_DATA_FILENAME_BJ_APR = 'state/PerformanceData-BJ-Apr.csv'
STATUS_FILENAME_BJ_APR = 'state/send_status_bj_apr.json'

# 北京5月
TEMP_CONTRACT_DATA_FILE_BJ_MAY = 'state/ContractData-BJ-May.csv'
PERFORMANCE_DATA_FILENAME_BJ_MAY = 'state/PerformanceData-BJ-May.csv'
STATUS_FILENAME_BJ_MAY = 'state/send_status_bj_may.json'

# 上海5月
TEMP_CONTRACT_DATA_FILE_SH_MAY = 'state/ContractData-SH-May.csv'
PERFORMANCE_DATA_FILENAME_SH_MAY = 'state/PerformanceData-SH-May.csv'
STATUS_FILENAME_SH_MAY = 'state/send_status_sh_may.json'
```

### 任务调度配置
```python
# 主任务执行间隔（分钟）
RUN_JOBS_SERIALLY_SCHEDULE = 3

# 任务调度器检查间隔（秒）
TASK_CHECK_INTERVAL = 10
```

## 业务配置

### 徽章功能配置
```python
# 是否启用徽章管理
ENABLE_BADGE_MANAGEMENT = True
BADGE_EMOJI = "\U0001F396"  # 奖章
BADGE_NAME = f"【{BADGE_EMOJI}精英管家】"

# 精英管家列表
ELITE_HOUSEKEEPER = ["胡林波", "余金凤", "文刘飞", "李卓", "吕世军"]
```

### SLA监控配置
```python
SLA_CONFIG = {
    "FORCE_MONDAY": False,  # 测试时设为 True，正式环境设为 False
}

# SLA违规记录文件
SLA_VIOLATIONS_RECORDS_FILE = './state/sla_violations.json'
```

### 奖金池配置
```python
# 上海地区奖金池比例
BONUS_POOL_RATIO = 0.002  # 0.2%

# 北京地区奖金池比例
BONUS_POOL_RATIO_BJ_FEB = 0.002  # 0.2%
```

## 配置修改指南

### 添加新活动
1. 在 `REWARD_CONFIGS` 中添加新配置：
```python
"BJ-2025-06": {
    "lucky_number": "8",
    "lucky_rewards": {...},
    "tiered_rewards": {...}
}
```

2. 添加对应的API和文件配置：
```python
API_URL_BJ_JUN = METABASE_URL + "/api/card/XXXX/query"
TEMP_CONTRACT_DATA_FILE_BJ_JUN = 'state/ContractData-BJ-Jun.csv'
PERFORMANCE_DATA_FILENAME_BJ_JUN = 'state/PerformanceData-BJ-Jun.csv'
```

3. 在 `jobs.py` 中添加对应任务函数

4. 在 `main.py` 中添加月份判断逻辑

### 修改奖励规则
```python
# 修改阈值
REWARD_CONFIGS["BJ-2025-05"]["tiered_rewards"]["tiers"][0]["threshold"] = 90000

# 修改幸运数字
REWARD_CONFIGS["BJ-2025-05"]["lucky_number"] = "8"

# 修改最低合同数
REWARD_CONFIGS["BJ-2025-05"]["tiered_rewards"]["min_contracts"] = 7
```

### 修改通知配置
```python
# 修改企业微信群名称
WECOM_GROUP_NAME_BJ_MAY = '新的群名称'

# 修改联系人
CAMPAIGN_CONTACT_BJ_MAY = '新联系人'

# 修改Webhook地址
WEBHOOK_URL_DEFAULT = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=新的key'
```

## 安全注意事项

### 敏感信息暴露
⚠️ **当前版本的安全风险**：
- Metabase用户名密码明文存储
- 企业微信Webhook地址暴露
- 联系电话等个人信息暴露

### 建议的安全措施
1. **限制代码访问权限**
2. **定期更换密码和密钥**
3. **不要将配置文件提交到公共代码仓库**
4. **考虑升级到v2.0版本使用环境变量**

## 故障排除

### 常见配置问题
1. **API地址错误**: 检查Metabase卡片ID是否正确
2. **文件路径问题**: 确保state目录存在且有写权限
3. **Webhook失效**: 检查企业微信机器人配置
4. **奖励规则错误**: 检查阈值和数字配置

### 配置验证
```python
# 在Python中验证配置
from modules.config import *
print(f"Metabase URL: {METABASE_URL}")
print(f"Webhook URL: {WEBHOOK_URL_DEFAULT}")
print(f"Reward configs: {list(REWARD_CONFIGS.keys())}")
```

---

**配置版本**: v1.0.1-stable | **更新日期**: 2025-05-17 | **状态**: 生产稳定
