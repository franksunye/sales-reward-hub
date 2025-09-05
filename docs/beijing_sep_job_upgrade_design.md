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
5. **历史合同与新增合同区分处理**: 基于pcContractdocNum字段区分历史合同和新增合同，实现差异化处理

### 1.2 历史合同与新增合同处理规则

#### 1.2.1 数据源字段说明
- **pcContractdocNum字段**: 合同历史标识字段
  - 有数值：表示活动期内的历史合同
  - 为空：表示活动期内的新增合同

#### 1.2.2 处理规则差异
| 合同类型 | 签约播报 | 计入管家累计单数 | 计入管家累计金额 | 计入业绩金额 | 奖励计算 |
|----------|----------|------------------|------------------|--------------|----------|
| 新增合同 | ✓ 播报 | ✓ 计入 | ✓ 计入 | ✓ 计入 | ✓ 参与 |
| 历史合同 | ✗ 不播报 | ✗ 不计入 | ✗ 不计入 | ✓ 仅计入此字段 | ✗ 不参与 |

#### 1.2.3 业务逻辑示例
以您提供的数据为例：
- **YHWX-BJ-DKS-2025080122**: 新增合同（pcContractdocNum为空）
  - 需要播报
  - 管家累计签约1单，累计签约金额7680元
  - 计入业绩金额7680元
  - 参与幸运数字和节节高奖励计算
- **其他5个合同**: 历史合同（pcContractdocNum有值）
  - 不播报
  - 不计入管家累计单数和金额
  - 仅计入业绩金额字段
  - 不参与奖励计算

### 1.3 技术原则
- **复用优先**: 最大化复用现有代码和逻辑
- **配置驱动**: 通过配置控制业务差异
- **最小改动**: 不影响上海功能，保持向后兼容
- **KISS原则**: 保持简单，避免过度设计
- **数据完整性**: 确保历史合同和新增合同数据处理的准确性

## 2. 技术设计方案

### 2.1 历史合同处理设计

#### 2.1.1 数据结构扩展
在现有数据处理流程中增加历史合同标识：

```python
# 合同数据结构扩展
CONTRACT_DATA_HEADERS = [
    # ... 现有字段 ...
    'pcContractdocNum'  # 新增：历史合同标识字段
]

# 性能数据结构扩展
PERFORMANCE_DATA_HEADERS = [
    # ... 现有字段 ...
    '是否历史合同',  # 新增：标识合同类型
    '合同类型说明'   # 新增：合同类型描述
]
```

#### 2.1.2 合同类型判断逻辑
```python
def is_historical_contract(contract_data: dict) -> bool:
    """
    判断是否为历史合同

    Args:
        contract_data: 合同数据字典

    Returns:
        bool: True表示历史合同，False表示新增合同
    """
    pc_contract_doc_num = contract_data.get('pcContractdocNum', '')
    # pcContractdocNum有值表示历史合同，为空表示新增合同
    return bool(pc_contract_doc_num and str(pc_contract_doc_num).strip())

def get_contract_type_description(is_historical: bool) -> str:
    """获取合同类型描述"""
    return "活动期内历史合同" if is_historical else "活动期内新增合同"
```

#### 2.1.3 差异化处理逻辑
```python
def process_contract_by_type(contract_data: dict, is_historical: bool) -> dict:
    """
    根据合同类型进行差异化处理

    Args:
        contract_data: 合同数据
        is_historical: 是否为历史合同

    Returns:
        dict: 处理后的合同数据
    """
    processed_data = contract_data.copy()

    if is_historical:
        # 历史合同处理逻辑
        processed_data.update({
            '是否发送通知': 'N',  # 不发送通知
            '奖励类型': '',       # 不参与奖励
            '奖励名称': '',       # 不参与奖励
            '备注': '历史合同-不播报不计入累计'
        })
    else:
        # 新增合同处理逻辑（按现有逻辑处理）
        processed_data.update({
            '是否发送通知': 'Y',  # 发送通知
            '备注': '新增合同-正常处理'
        })

    return processed_data
```

### 2.2 配置驱动设计

#### 2.2.1 新增配置项 "BJ-2025-09"
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

### 2.3 核心函数升级

#### 2.3.1 数据处理函数增强
```python
def process_data_sep_beijing_with_historical_support(
    contract_data: list,
    existing_contract_ids: set,
    housekeeper_award_lists: dict
) -> list:
    """
    北京9月数据处理函数（支持历史合同处理）

    Args:
        contract_data: 合同数据列表
        existing_contract_ids: 已存在的合同ID集合
        housekeeper_award_lists: 管家奖励列表

    Returns:
        list: 处理后的性能数据列表
    """
    processed_data = []

    for contract in contract_data:
        # 判断是否为历史合同
        is_historical = is_historical_contract(contract)

        # 根据合同类型进行差异化处理
        if is_historical:
            # 历史合同：仅计入业绩金额，不参与其他计算
            processed_contract = process_historical_contract(contract)
        else:
            # 新增合同：按正常逻辑处理（参与所有计算）
            processed_contract = process_new_contract(
                contract, existing_contract_ids, housekeeper_award_lists
            )

        processed_data.append(processed_contract)

    return processed_data

def process_historical_contract(contract_data: dict) -> dict:
    """
    处理历史合同
    - 不播报
    - 不计入管家累计单数和金额
    - 仅计入业绩金额
    - 不参与奖励计算
    """
    return {
        # ... 基础字段 ...
        '活动期内第几个合同': 0,  # 不计入个人合同序号
        '管家累计金额': 0,        # 不计入累计金额
        '管家累计单数': 0,        # 不计入累计单数
        '计入业绩金额': contract_data.get('adjustRefundMoney', 0),  # 仅计入业绩
        '奖励类型': '',           # 不参与奖励
        '奖励名称': '',           # 不参与奖励
        '是否发送通知': 'N',      # 不发送通知
        '是否历史合同': 'Y',      # 标记为历史合同
        '合同类型说明': '活动期内历史合同',
        '备注': '历史合同-仅计入业绩金额'
    }

def process_new_contract(
    contract_data: dict,
    existing_contract_ids: set,
    housekeeper_award_lists: dict
) -> dict:
    """
    处理新增合同（按现有逻辑）
    - 正常播报
    - 计入管家累计单数和金额
    - 计入业绩金额
    - 参与奖励计算
    """
    # 调用现有的数据处理逻辑
    processed_contract = process_data_jun_beijing_with_config(
        [contract_data], existing_contract_ids, housekeeper_award_lists,
        config_key="BJ-2025-09"
    )[0]

    # 添加合同类型标识
    processed_contract.update({
        '是否历史合同': 'N',
        '合同类型说明': '活动期内新增合同'
    })

    return processed_contract
```

#### 2.3.2 幸运数字逻辑通用化
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

### 2.4 新增包装函数

#### 2.4.1 数据处理函数
```python
def process_data_sep_beijing(contract_data, existing_contract_ids, housekeeper_award_lists):
    """
    北京9月数据处理函数（包装函数）
    支持历史合同和新增合同的差异化处理
    """
    return process_data_sep_beijing_with_historical_support(
        contract_data,
        existing_contract_ids,
        housekeeper_award_lists
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

#### 2.4.3 主Job函数
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

    performance_data_headers = ['活动编号', '合同ID(_id)', '活动城市(province)', '工单编号(serviceAppointmentNum)', 'Status', '管家(serviceHousekeeper)', '合同编号(contractdocNum)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '差额(difference)', 'State', '创建时间(createTime)', '服务商(orgName)', '签约时间(signedDate)', 'Doorsill', '款项来源类型(tradeIn)', '转化率(conversion)', '平均客单价(average)','活动期内第几个合同','管家累计金额','管家累计单数','奖金池','计入业绩金额','激活奖励状态', '奖励类型', '奖励名称', '是否发送通知', '是否历史合同', '合同类型说明', '备注', '登记时间']

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

### 4.1 测试策略（三层保障）

#### 4.1.1 **回归测试**（最高优先级）
确保现有功能完全不受影响：

```python
class TestRegressionSuite:
    """回归测试套件 - 确保现有功能不变"""

    def test_beijing_aug_unchanged(self):
        """测试北京8月功能完全不变"""
        # 测试BJ-2025-08配置不变
        config = REWARD_CONFIGS["BJ-2025-08"]
        assert config["lucky_number"] == "8"
        assert config["tiered_rewards"]["min_contracts"] == 6

        # 测试幸运数字8逻辑不变
        reward_type, reward_name = determine_lucky_number_reward(18, 15000, "8")
        assert reward_type == "幸运数字"
        assert reward_name == "接好运万元以上"

        # 测试精英徽章功能正常
        # 测试原有奖励计算逻辑

    def test_shanghai_functionality_unchanged(self):
        """测试上海所有功能不受影响"""
        # 测试SH-2025-04配置
        # 测试SH-2025-09配置
        # 测试上海特有逻辑

    def test_config_isolation(self):
        """测试配置完全隔离"""
        # 验证各配置项独立性
        # 验证不会相互影响
```

#### 4.1.2 **新功能测试**
验证北京9月新功能：

```python
class TestBeijingSepFeatures:
    """北京9月新功能测试"""

    def test_historical_contract_identification(self):
        """测试历史合同识别"""
        # 测试pcContractdocNum有值的历史合同
        historical_contract = {'pcContractdocNum': 'YHWX-BJ-DKS-2025080121'}
        assert is_historical_contract(historical_contract) == True

        # 测试pcContractdocNum为空的新增合同
        new_contract = {'pcContractdocNum': ''}
        assert is_historical_contract(new_contract) == False

        # 测试pcContractdocNum不存在的新增合同
        new_contract_no_field = {}
        assert is_historical_contract(new_contract_no_field) == False

    def test_historical_contract_processing(self):
        """测试历史合同处理逻辑"""
        historical_contract = {
            'contractdocNum': 'YHWX-BJ-DKS-2025080121',
            'adjustRefundMoney': 15000,
            'pcContractdocNum': 'YHWX-BJ-DKS-2025080121'
        }

        processed = process_historical_contract(historical_contract)

        # 验证历史合同处理结果
        assert processed['活动期内第几个合同'] == 0
        assert processed['管家累计金额'] == 0
        assert processed['管家累计单数'] == 0
        assert processed['计入业绩金额'] == 15000  # 仅计入业绩金额
        assert processed['奖励类型'] == ''
        assert processed['奖励名称'] == ''
        assert processed['是否发送通知'] == 'N'
        assert processed['是否历史合同'] == 'Y'

    def test_new_contract_processing(self):
        """测试新增合同处理逻辑"""
        new_contract = {
            'contractdocNum': 'YHWX-BJ-DKS-2025080122',
            'adjustRefundMoney': 7680,
            'pcContractdocNum': ''
        }

        # 新增合同应按正常逻辑处理
        # 包括计入累计、参与奖励计算等

    def test_mixed_contract_processing(self):
        """测试混合合同数据处理"""
        contract_data = [
            # 历史合同
            {'contractdocNum': 'YHWX-BJ-DKS-2025080121', 'adjustRefundMoney': 15000, 'pcContractdocNum': 'YHWX-BJ-DKS-2025080121'},
            {'contractdocNum': 'YHWX-BJ-DKS-2025080123', 'adjustRefundMoney': 12000, 'pcContractdocNum': 'YHWX-BJ-DKS-2025080123'},
            # 新增合同
            {'contractdocNum': 'YHWX-BJ-DKS-2025080122', 'adjustRefundMoney': 7680, 'pcContractdocNum': ''}
        ]

        processed_data = process_data_sep_beijing(contract_data, set(), {})

        # 验证只有新增合同参与累计计算
        new_contracts = [d for d in processed_data if d['是否历史合同'] == 'N']
        historical_contracts = [d for d in processed_data if d['是否历史合同'] == 'Y']

        assert len(new_contracts) == 1
        assert len(historical_contracts) == 2
        assert new_contracts[0]['管家累计金额'] == 7680
        assert new_contracts[0]['管家累计单数'] == 1

    def test_personal_sequence_lucky_number(self):
        """测试基于个人顺序的幸运数字（仅新增合同参与）"""
        # 测试第5个新增合同获得奖励
        reward_type, reward_name = determine_lucky_number_reward_generic(
            contract_number=123,
            current_contract_amount=8000,
            housekeeper_contract_count=5,  # 第5个新增合同
            config_key="BJ-2025-09"
        )
        assert reward_type == "幸运数字"
        assert reward_name == "接好运"

        # 测试第10个合同获得奖励
        # 测试第4个合同不获得奖励

    def test_lucky_number_unified_reward(self):
        """测试统一58元奖励（不区分金额）"""
        # 5000元合同获得58元
        # 15000元合同也获得58元

    def test_tiered_rewards_new_threshold(self):
        """测试新的节节高门槛和奖励（仅基于新增合同）"""
        # 9个新增合同不获得节节高
        # 10个新增合同+8万元获得400元达标奖
        # 18万元获得800元优秀奖
        # 28万元获得1600元精英奖

    def test_badge_completely_disabled(self):
        """测试徽章功能完全禁用"""
        # 精英管家不显示徽章
        # 精英管家不获得双倍奖励
        # 新星徽章不显示

    def test_project_amount_limit_5w(self):
        """测试5万元工单上限"""
        # 6万元合同按5万计入
        # 多合同累计上限处理
```

#### 4.1.3 **集成测试**
端到端验证：

```python
class TestIntegrationSuite:
    """集成测试套件"""

    def test_multiple_configs_coexist(self):
        """测试多个配置共存"""
        # BJ-2025-08和BJ-2025-09同时存在
        # 各自功能独立正确

    def test_end_to_end_beijing_sep(self):
        """测试北京9月完整流程"""
        # 数据获取→处理→奖励计算→通知发送

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 现有job调用方式不变
        # 现有配置完全兼容
```

### 4.2 TDD开发步骤（测试先行）

#### **第一阶段：回归测试建立**
```bash
# 1. 创建回归测试基线
python -m pytest tests/test_regression_baseline.py -v
# 确保现有功能100%正确

# 2. 建立配置隔离测试
python -m pytest tests/test_config_isolation.py -v
# 确保新配置不影响现有配置
```

#### **第二阶段：配置和基础函数（TDD）**
```python
# 1. 先写测试
def test_bj_2025_09_config_exists():
    """测试新配置存在且正确"""
    config = REWARD_CONFIGS.get("BJ-2025-09")
    assert config is not None
    assert config["lucky_number"] == "5"
    assert config["lucky_number_mode"] == "personal_sequence"

# 2. 再写实现
# 添加BJ-2025-09配置到config.py

# 3. 测试通过后继续
def test_lucky_number_generic_function():
    """测试幸运数字通用函数"""
    # 先写测试用例
    # 再实现函数
    # 确保测试通过
```

#### **第三阶段：数据处理逻辑（TDD）**
```python
# 1. 先写数据处理测试
def test_process_data_sep_beijing():
    """测试北京9月数据处理"""
    # 模拟输入数据
    # 预期输出结果
    # 验证奖励计算正确

# 2. 实现数据处理函数
# 3. 运行回归测试确保不破坏现有功能
python -m pytest tests/test_regression_suite.py -v
```

#### **第四阶段：通知和集成（TDD）**
```python
# 1. 先写通知测试
def test_notify_awards_sep_beijing():
    """测试北京9月通知功能"""
    # 验证徽章禁用
    # 验证消息格式
    # 验证奖励金额

# 2. 实现通知函数
# 3. 端到端集成测试
def test_full_beijing_sep_job():
    """完整job流程测试"""
    # 数据获取→处理→通知→归档
```

### 4.3 测试执行策略

#### **每次提交前必须执行**：
```bash
# 1. 回归测试（必须100%通过）
python -m pytest tests/test_regression_suite.py -v --tb=short

# 2. 配置隔离测试（必须100%通过）
python -m pytest tests/test_config_isolation.py -v --tb=short

# 3. 新功能测试（逐步完善）
python -m pytest tests/test_beijing_sep_features.py -v --tb=short

# 4. 集成测试（最终验证）
python -m pytest tests/test_integration_suite.py -v --tb=short
```

#### **测试覆盖率要求**：
```bash
# 整体覆盖率>90%
python -m pytest --cov=modules --cov-report=html --cov-report=term

# 关键模块100%覆盖
python -m pytest --cov=modules.data_processing_module --cov-fail-under=100
python -m pytest --cov=modules.notification_module --cov-fail-under=100
```

## 5. 向后兼容性保障

### 5.1 **零影响原则**
确保新功能对现有系统零影响：

#### 5.1.1 代码层面保障
```python
# ✅ 正确做法：新增函数，不修改现有函数
def determine_lucky_number_reward_generic(...):  # 新增
    """通用幸运数字函数，支持多种模式"""
    pass

def determine_lucky_number_reward(...):  # 保持不变
    """原有函数完全不动"""
    pass

# ❌ 错误做法：修改现有函数
def determine_lucky_number_reward(...):  # 不要修改！
    """不要在现有函数中添加新逻辑"""
    pass
```

#### 5.1.2 配置层面保障
```python
# ✅ 配置完全隔离
REWARD_CONFIGS = {
    "BJ-2025-08": {...},  # 完全不变
    "SH-2025-04": {...},  # 完全不变
    "SH-2025-09": {...},  # 完全不变
    "BJ-2025-09": {...}   # 新增配置
}

# ✅ 默认值保持兼容
def should_enable_badge(config_key, badge_type):
    badge_config = reward_config.get("badge_config", {})
    return badge_config.get("enable_elite_badge", True)  # 默认True保持兼容
```

### 5.2 **回归测试矩阵**

#### 5.2.1 现有功能验证清单
```python
# 北京8月功能验证
✓ 幸运数字8逻辑正确
✓ 精英徽章显示正确
✓ 新星徽章显示正确
✓ 双倍奖励计算正确
✓ 6个合同门槛正确
✓ 原有奖励金额正确

# 上海功能验证
✓ 上海8月功能正常
✓ 上海9月双轨功能正常
✓ 上海特有奖励规则正常
✓ 上海通知格式正常

# 配置系统验证
✓ 各配置项完全独立
✓ 配置加载正确
✓ 奖励映射正确
```

#### 5.2.2 自动化回归测试
```bash
# 每次代码变更后自动运行
./scripts/run_regression_tests.sh

# 测试内容：
# 1. 所有现有job功能测试
# 2. 配置隔离测试
# 3. 数据处理正确性测试
# 4. 通知发送格式测试
```

### 5.3 **部署安全策略**

#### 5.3.1 分阶段部署
```
阶段1: 配置部署（只添加配置，不启用）
├── 部署新配置文件
├── 运行回归测试
└── 确认现有功能正常

阶段2: 代码部署（部署新函数，不调用）
├── 部署新增函数
├── 运行完整测试套件
└── 确认所有功能正常

阶段3: 功能启用（启用新job）
├── 在main.py中启用新job
├── 监控运行状态
└── 准备回滚方案
```

#### 5.3.2 回滚预案
```python
# 紧急回滚方案
if emergency_rollback:
    # 1. 注释掉新job调用
    # signing_and_sales_incentive_sep_beijing()  # 注释掉

    # 2. 恢复配置文件
    git checkout HEAD~1 -- modules/config.py

    # 3. 重启服务
    # 现有功能立即恢复正常
```

### 5.4 **质量保证措施**

#### 5.4.1 代码审查检查点
- [ ] 是否修改了现有函数？（不允许）
- [ ] 是否修改了现有配置？（不允许）
- [ ] 回归测试是否100%通过？（必须）
- [ ] 新功能测试是否覆盖完整？（必须）
- [ ] 是否有性能回归？（不允许）

#### 5.4.2 测试覆盖要求
```
回归测试覆盖率: 100%（现有功能）
新功能测试覆盖率: >95%
集成测试覆盖率: >90%
端到端测试: 必须包含
```

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

## 8. 历史合同处理需求补充

### 8.1 需求背景
根据2025年1月3日的需求补充，数据源将增加`pcContractdocNum`字段用于区分历史合同和新增合同。

### 8.2 数据源变更
- **新增字段**: `pcContractdocNum`（合同历史标识）
- **字段含义**:
  - 有数值：活动期内的历史合同
  - 为空：活动期内的新增合同

### 8.3 业务规则示例
以提供的数据为例：
```
YHWX-BJ-DKS-2025080122: 新增合同（pcContractdocNum为空）
- 需要播报
- 管家累计签约1单，累计签约金额7680元
- 计入业绩金额7680元
- 参与奖励计算

其他5个合同: 历史合同（pcContractdocNum有值）
- 不播报
- 不计入管家累计单数和金额
- 仅计入业绩金额字段
- 不参与奖励计算
```

### 8.4 实施状态
- **已完成**: 文档中1-7章节的所有需求已代码实现完成
- **待实施**: 本章节（第8章）的历史合同处理需求尚未开始实施
- **优先级**: 高优先级，需要在9月活动启动前完成

### 8.5 技术实施要点
1. **数据结构扩展**: 在合同数据头部增加`pcContractdocNum`字段
2. **处理逻辑分离**: 历史合同和新增合同采用不同的处理流程
3. **累计计算调整**: 只有新增合同参与管家累计单数和金额计算
4. **奖励计算调整**: 只有新增合同参与幸运数字和节节高奖励计算
5. **通知发送调整**: 只有新增合同发送签约播报通知

### 8.6 测试验证重点
1. **合同类型识别准确性**: 确保正确识别历史合同和新增合同
2. **数据处理差异化**: 验证两种合同类型的处理逻辑完全不同
3. **累计计算正确性**: 确保只有新增合同影响管家累计数据
4. **奖励计算正确性**: 确保只有新增合同参与奖励计算
5. **通知发送正确性**: 确保只有新增合同触发通知

---

*本文档遵循TDD原则和KISS设计理念，确保升级的可靠性和可维护性。*
*历史合同处理需求已于2025年1月3日补充，待实施。*
