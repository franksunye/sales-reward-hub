# 北京9月签约激励Job升级设计文档

## 文档信息
- **升级目标**: 北京9月签约激励活动功能升级
- **基础版本**: 北京8月活动 (signing_and_sales_incentive_aug_beijing)
- **新Job名称**: `signing_and_sales_incentive_sep_beijing()`
- **创建日期**: 2025-01-02
- **版本**: v1.0
- **开发方法**: TDD (测试驱动开发)

## 1. 升级需求概述

### 1.1 业务需求变更
1. **工单金额上限调整**: 合同金额>5万时按5万计入业绩
2. **幸运数字机制重构**: 改为基于个人签约顺序，第5、10、15个等（5的倍数）合同获得58元奖励
3. **节节高门槛提升**: 10个合同后解锁，奖励金额翻倍
4. **徽章机制禁用**: 取消精英管家和新人徽章及双倍激励

### 1.2 技术原则
- **复用优先**: 最大化复用现有代码和逻辑
- **配置驱动**: 通过配置控制业务差异
- **最小改动**: 不影响上海功能，保持向后兼容
- **KISS原则**: 保持简单，避免过度设计

## 2. 技术设计方案

### 2.1 配置驱动设计

#### 2.1.1 新增配置项 "BJ-2025-09"
```python
"BJ-2025-09": {
    "lucky_number": "5",  # 基于个人合同顺序的倍数
    "lucky_rewards": {
        "base": {"name": "接好运", "threshold": 0},
        "high": {"name": "接好运", "threshold": 999999999}  # 统一奖励，不区分金额
    },
    "lucky_number_mode": "personal_sequence",  # 新增：幸运数字模式
    "performance_limits": {
        "single_project_limit": 50000,  # 调整为5万
        "enable_cap": True,
        "single_contract_cap": 50000
    },
    "tiered_rewards": {
        "min_contracts": 10,  # 提升至10个合同
        "tiers": [
            {"name": "达标奖", "threshold": 80000},
            {"name": "优秀奖", "threshold": 180000},
            {"name": "精英奖", "threshold": 280000}
        ]
    },
    "awards_mapping": {
        "接好运": "58",  # 统一58元
        "达标奖": "400",  # 翻倍
        "优秀奖": "800",  # 翻倍
        "精英奖": "1600"  # 翻倍
    },
    "badge_config": {
        "enable_elite_badge": False,
        "enable_rising_star_badge": False
    }
}
```

### 2.2 核心函数升级

#### 2.2.1 幸运数字逻辑通用化
```python
def determine_lucky_number_reward_generic(
    contract_number: int,
    current_contract_amount: float,
    housekeeper_contract_count: int,
    config_key: str
) -> tuple:
    """
    通用幸运数字奖励确定函数
    
    Args:
        contract_number: 合同编号（用于传统模式）
        current_contract_amount: 当前合同金额
        housekeeper_contract_count: 管家个人合同数量（用于个人顺序模式）
        config_key: 配置键
    
    Returns:
        tuple: (reward_type, reward_name)
    """
    reward_config = config.REWARD_CONFIGS.get(config_key, {})
    lucky_number = reward_config.get("lucky_number", "")
    lucky_mode = reward_config.get("lucky_number_mode", "contract_number")
    
    if not lucky_number:
        return "", ""
    
    # 根据模式选择判断逻辑
    if lucky_mode == "personal_sequence":
        # 个人签约顺序模式：判断是否为指定倍数
        target_multiple = int(lucky_number)
        if housekeeper_contract_count % target_multiple == 0:
            return "幸运数字", "接好运"
    else:
        # 传统模式：基于合同编号末位
        if lucky_number in str(contract_number % 10):
            lucky_rewards = reward_config.get("lucky_rewards", {})
            high_threshold = lucky_rewards.get("high", {}).get("threshold", 10000)
            if current_contract_amount >= high_threshold:
                return "幸运数字", lucky_rewards.get("high", {}).get("name", "接好运万元以上")
            else:
                return "幸运数字", lucky_rewards.get("base", {}).get("name", "接好运")
    
    return "", ""
```

#### 2.2.2 徽章配置支持
```python
def should_enable_badge(config_key: str, badge_type: str) -> bool:
    """
    检查是否启用指定徽章
    
    Args:
        config_key: 配置键
        badge_type: 徽章类型 ("elite" 或 "rising_star")
    
    Returns:
        bool: 是否启用徽章
    """
    reward_config = config.REWARD_CONFIGS.get(config_key, {})
    badge_config = reward_config.get("badge_config", {})
    
    if badge_type == "elite":
        return badge_config.get("enable_elite_badge", True)  # 默认启用
    elif badge_type == "rising_star":
        return badge_config.get("enable_rising_star_badge", False)  # 默认禁用
    
    return False
```

### 2.3 新增包装函数

#### 2.3.1 数据处理函数
```python
def process_data_sep_beijing(contract_data, existing_contract_ids, housekeeper_award_lists):
    """
    北京9月数据处理函数（包装函数）
    复用process_data_jun_beijing逻辑，使用新配置
    """
    # 临时修改配置以使用新的奖励计算逻辑
    return process_data_jun_beijing_with_config(
        contract_data, 
        existing_contract_ids, 
        housekeeper_award_lists,
        config_key="BJ-2025-09"
    )
```

#### 2.3.2 通知发送函数
```python
def notify_awards_sep_beijing(performance_data_filename, status_filename):
    """北京9月通知函数（包装函数）"""
    return notify_awards_beijing_generic(
        performance_data_filename,
        status_filename,
        "BJ-2025-09",
        enable_rising_star_badge=False  # 9月份禁用新星徽章
    )
```

#### 2.3.3 主Job函数
```python
def signing_and_sales_incentive_sep_beijing():
    """北京2025年9月签约激励Job"""
    contract_data_filename = TEMP_CONTRACT_DATA_FILE_BJ_SEP
    performance_data_filename = PERFORMANCE_DATA_FILENAME_BJ_SEP
    status_filename = STATUS_FILENAME_BJ_SEP
    api_url = API_URL_BJ_SEP

    logging.info('BEIJING 2025 9月, Job started ...')

    response = send_request_with_managed_session(api_url)
    logging.info('BEIJING 2025 9月, Request sent')

    rows = response['data']['rows']
    contract_data = convert_to_dict_list(rows, CONTRACT_DATA_HEADERS)
    write_contract_data(contract_data_filename, contract_data, CONTRACT_DATA_HEADERS)

    existing_contract_ids = get_existing_contract_ids(performance_data_filename)
    housekeeper_award_lists = get_unique_housekeeper_award_list(performance_data_filename)

    # 使用9月专用数据处理逻辑
    processed_data = process_data_sep_beijing(contract_data, existing_contract_ids, housekeeper_award_lists)
    logging.info('BEIJING 2025 9月, Data processed')

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池','计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '备注', '登记时间']

    write_performance_data(performance_data_filename, processed_data, performance_data_headers)

    # 使用9月专用通知逻辑
    notify_awards_sep_beijing(performance_data_filename, status_filename)

    archive_file(contract_data_filename)
    logging.info('BEIJING 2025 9月, Data archived')
    logging.info('BEIJING 2025 9月, Job ended')
```

## 3. 配置文件变更

### 3.1 config.py新增配置
```python
## 北京地区，2025年9月活动
API_URL_BJ_SEP = METABASE_URL + "/api/card/1802/query"  # 新的API端点

# 北京销售激励活动 JOB signing_and_sales_incentive_sep_beijing
TEMP_CONTRACT_DATA_FILE_BJ_SEP = 'state/ContractData-BJ-Sep.csv'
PERFORMANCE_DATA_FILENAME_BJ_SEP = 'state/PerformanceData-BJ-Sep.csv'
STATUS_FILENAME_BJ_SEP = 'state/send_status_bj_sep.json'

# 通知配置
WECOM_GROUP_NAME_BJ_SEP = '（北京）修链服务运营'
CAMPAIGN_CONTACT_BJ_SEP = '王爽'
```

## 4. TDD开发计划

### 4.1 测试用例设计

#### 4.1.1 幸运数字测试
```python
def test_personal_sequence_lucky_number():
    """测试基于个人顺序的幸运数字奖励"""
    # 测试第5个合同获得奖励
    # 测试第10个合同获得奖励
    # 测试非5倍数合同不获得奖励
    pass

def test_lucky_number_unified_reward():
    """测试统一奖励金额（不区分1万上下）"""
    # 测试5000元合同获得58元奖励
    # 测试15000元合同获得58元奖励
    pass
```

#### 4.1.2 节节高奖励测试
```python
def test_tiered_rewards_new_threshold():
    """测试新的节节高门槛和奖励"""
    # 测试9个合同不获得节节高奖励
    # 测试10个合同且8万元获得400元达标奖
    # 测试18万元获得800元优秀奖
    # 测试28万元获得1600元精英奖
    pass
```

#### 4.1.3 徽章禁用测试
```python
def test_badge_disabled():
    """测试徽章功能禁用"""
    # 测试精英管家不显示徽章
    # 测试精英管家不获得双倍奖励
    # 测试新星徽章不显示
    pass
```

#### 4.1.4 工单金额上限测试
```python
def test_project_amount_limit():
    """测试5万元工单金额上限"""
    # 测试6万元合同按5万计入
    # 测试多个合同累计上限处理
    pass
```

### 4.2 开发步骤

1. **第一阶段：配置和基础函数**
   - 添加BJ-2025-09配置
   - 实现幸运数字通用化函数
   - 实现徽章配置检查函数
   - 编写单元测试

2. **第二阶段：数据处理逻辑**
   - 修改奖励计算逻辑支持新配置
   - 实现包装函数
   - 编写数据处理测试

3. **第三阶段：通知和集成**
   - 修改通知逻辑支持徽章配置
   - 实现完整Job函数
   - 编写集成测试

4. **第四阶段：验证和部署**
   - 端到端测试
   - 性能测试
   - 部署验证

## 5. 风险控制

### 5.1 向后兼容性
- 所有现有函数保持不变
- 新功能通过配置开关控制
- 上海功能完全不受影响

### 5.2 测试覆盖
- 单元测试覆盖率>90%
- 集成测试覆盖关键业务场景
- 回归测试确保现有功能正常

### 5.3 部署策略
- 先在测试环境验证
- 灰度发布，逐步切换
- 保留回滚方案

## 6. 实施时间表

| 阶段 | 任务 | 预计时间 | 交付物 |
|------|------|----------|--------|
| 1 | 配置和基础函数开发 | 1天 | 配置文件、基础函数、单元测试 |
| 2 | 数据处理逻辑开发 | 1天 | 数据处理函数、测试用例 |
| 3 | 通知和集成开发 | 1天 | 通知函数、Job函数、集成测试 |
| 4 | 测试和部署 | 1天 | 完整测试套件、部署文档 |

## 7. 成功标准

### 7.1 功能标准
- [ ] 幸运数字基于个人顺序正确计算
- [ ] 节节高门槛和奖励金额正确
- [ ] 徽章功能完全禁用
- [ ] 工单金额上限正确处理

### 7.2 质量标准
- [ ] 测试覆盖率>90%
- [ ] 所有测试用例通过
- [ ] 代码审查通过
- [ ] 性能无回归

### 7.3 兼容性标准
- [ ] 上海功能正常运行
- [ ] 北京8月功能正常运行
- [ ] 配置向后兼容

---

*本文档遵循TDD原则和KISS设计理念，确保升级的可靠性和可维护性。*
