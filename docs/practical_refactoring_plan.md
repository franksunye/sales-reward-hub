# 实用重构执行方案

## 概述

基于深度代码分析，本方案采用**"重建+迁移+SQLite集成"**策略，分4个阶段执行，每个阶段都可独立验证和回滚。

## 深度问题分析（基于完整代码研读）

### 1. 北京月份演进的"伪复用"灾难

#### 1.1 北京6月→8月→9月的复用陷阱
**北京8月的"假复用"**:
```python
# jobs.py:39 - 8月直接复用6月函数，但配置不匹配
processed_data = process_data_jun_beijing(contract_data, existing_contract_ids, housekeeper_award_lists)
# 使用6月的配置 "BJ-2025-06"，但实际是8月活动
# 注释说"当月的数据处理逻辑"，实际是6月逻辑
```

**北京9月的"包装地狱"**:
```python
# modules/data_processing_module.py:1575-1582 - 全局篡改包装
def process_data_sep_beijing(contract_data, existing_contract_ids, housekeeper_award_lists):
    # 检查是否有历史合同字段，如果有则使用新的处理逻辑
    has_historical_field = any('pcContractdocNum' in contract for contract in contract_data)
    if has_historical_field:
        return process_data_sep_beijing_with_historical_support(...)  # 新逻辑
    else:
        # 全局篡改 + 复用6月逻辑
        globals()['determine_rewards_jun_beijing_generic'] = determine_rewards_sep_beijing_generic
        config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000  # 临时改为5万
        try:
            result = process_data_jun_beijing(...)  # 复用6月函数
            for record in result:
                record['活动编号'] = 'BJ-SEP'  # 事后修改活动编号
        finally:
            # 恢复全局状态
```

**问题根源**: 6月函数硬编码了太多假设（50万上限、"BJ-JUN"活动编号等），为了复用而不是重构，导致9月逻辑极其复杂。

#### 1.2 北京9月的双重逻辑分支
**一个函数内部两套完全不同的处理路径**:
- 有历史合同字段 → `process_data_sep_beijing_with_historical_support`
- 无历史合同字段 → 全局篡改 + 复用6月逻辑

**结果**: 维护噩梦，测试困难，逻辑分散

### 2. 上海月份演进的"复制粘贴"问题

#### 2.1 上海4月→8月→9月的重复演进
**上海8月的"伪复用"**:
```python
# jobs.py:80 - 8月复用4月函数
processed_data = process_data_shanghai_apr(contract_data, existing_contract_ids, housekeeper_award_lists)
# 注释说"奖励规则与4月保持一致"，但实际是8月活动
# 通知也复用3月旧版: notify_awards_shanghai_generate_message_march
```

**上海9月的"全新实现"**:
```python
# modules/data_processing_module.py:613-735 - 完全独立的函数
def process_data_shanghai_sep(contract_data, existing_contract_ids, housekeeper_award_lists):
    # 650-656行: 扩展了双轨统计字段
    housekeeper_contracts[housekeeper_key] = {
        'count': 0, 'total_amount': 0, 'performance_amount': 0, 'awarded': housekeeper_award,
        'platform_count': 0, 'platform_amount': 0,      # 新增平台单统计
        'self_referral_count': 0, 'self_referral_amount': 0,  # 新增自引单统计
        'self_referral_projects': set(),  # 新增项目地址去重
        'self_referral_rewards': 0        # 新增自引单奖励计数
    }
```

**问题**:
- 4月和9月的数据结构完全不兼容
- 无法共享任何数据处理逻辑
- 每次新增功能都要重写整个函数

#### 2.2 上海的housekeeper_key不一致
**关键差异**: 上海使用`"管家_服务商"`作为key，北京使用`"管家"`
```python
# 上海4月/9月: data_processing_module.py:464
unique_housekeeper_key = f"{housekeeper}_{service_provider}"

# 北京6月/8月/9月: data_processing_module.py:326
housekeeper = contract['管家(serviceHousekeeper)']  # 直接使用管家名
```

**影响**: 导致奖励计算函数虽然通用，但数据结构层面无法统一

### 3. 配置系统的"新旧并存"混乱

#### 3.1 新配置系统 vs 旧全局变量
**新系统**: `REWARD_CONFIGS` 统一配置（config.py:9-162）
**旧系统**: 散落的全局变量仍在使用
```python
# 旧变量仍在使用
PERFORMANCE_AMOUNT_CAP_BJ_FEB = 500000  # line:257
ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB = True  # line:259
SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB = 500000  # line:255
```

**问题**: 北京9月通过临时修改旧变量来影响6月函数的行为

#### 3.2 配置键命名不一致
**北京**: "BJ-2025-06", "BJ-2025-09"
**上海**: "SH-2025-04", "SH-2025-09"
**问题**: 8月份活动复用了其他月份的配置，配置键与实际月份不匹配

### 4. 数据字段的"渐进膨胀"问题

#### 4.1 CSV字段的不断增加
**北京6月**: 29个字段
**北京9月**: 32个字段（新增3个历史合同相关字段）
**上海9月**: 37个字段（新增8个双轨统计字段）

#### 4.2 字段处理逻辑分散
**问题**: 每个月份的字段构建逻辑都硬编码在各自的函数中
- 北京6月: data_processing_module.py:391-421 (30行字典构建)
- 上海4月: data_processing_module.py:506-536 (30行字典构建)
- 上海9月: data_processing_module.py:737-778 (40行字典构建)

**影响**:
- 无法复用字段构建逻辑
- 新增字段需要修改多个地方
- 字段顺序和命名容易不一致

### 5. Job函数的"复制粘贴"演进

#### 5.1 Job函数的重复模式
**模式**: 每个新月份都复制上个月份的Job函数，然后修改部分参数
**结果**:
- 8个几乎相同的Job函数（北京3个+上海3个+其他2个）
- 每个函数50-100行，大部分代码重复
- 修改通用逻辑需要改8个地方

#### 5.2 通配符导入的依赖混乱
```python
# jobs.py:4-7
from modules.request_module import send_request_with_managed_session
from modules.data_processing_module import *  # 导入所有
from modules.data_utils import *              # 导入所有
from modules.notification_module import *     # 导入所有
```

**问题**:
- 无法静态分析依赖关系
- IDE无法提供准确的代码补全
- 容易出现命名冲突

### 6. 复杂的累计计算维护
```python
# 每个处理函数都要维护50+行的复杂结构
housekeeper_contracts[housekeeper] = {
    'count': 0, 'total_amount': 0, 'performance_amount': 0, 'awarded': [],
    'platform_count': 0, 'platform_amount': 0,      # 上海9月新增
    'self_referral_count': 0, 'self_referral_amount': 0,  # 上海9月新增
    'self_referral_projects': set(),  # 新增项目地址去重
    'self_referral_rewards': 0        # 新增自引单奖励计数
}
```
**问题**: 手工维护累计状态，复杂度指数增长

### 7. 重复的去重和查询逻辑
```python
# 每个Job都要读取整个CSV文件
existing_contract_ids = collect_unique_contract_ids_from_file(filename)
housekeeper_award_lists = get_housekeeper_award_list(filename)
```
**问题**: 性能差、代码重复、内存占用高

## 高层架构设计（C4模型）

### 1. 系统上下文图（C1 - System Context）

```mermaid
graph TB
    User[运营人员] --> System[签约激励系统]
    System --> Metabase[Metabase数据源]
    System --> WeChat[企微通知]
    System --> WeCom[微信个人通知]
    System --> FileSystem[文件系统]
    System --> Database[(SQLite数据库)]

    User -.-> |查看报表| Metabase
    User -.-> |接收通知| WeChat
    User -.-> |接收奖励消息| WeCom
```

### 2. 容器图（C2 - Container）

```mermaid
graph TB
    subgraph "签约激励系统"
        JobScheduler[任务调度器<br/>Python]
        ProcessingEngine[数据处理引擎<br/>Python]
        NotificationEngine[通知引擎<br/>Python]
        ConfigManager[配置管理器<br/>Python]
        Database[(SQLite数据库)]
        FileStorage[文件存储<br/>CSV/Archive]
    end

    External[外部系统] --> JobScheduler
    JobScheduler --> ProcessingEngine
    ProcessingEngine --> Database
    ProcessingEngine --> NotificationEngine
    ProcessingEngine --> ConfigManager
    NotificationEngine --> WeChat[企微API]
    NotificationEngine --> WeCom[微信API]
    ProcessingEngine --> FileStorage

    Metabase[Metabase API] --> ProcessingEngine
```

### 3. 组件图（C3 - Component）

```mermaid
graph TB
    subgraph "数据处理引擎"
        Pipeline[ProcessingPipeline<br/>处理管道]
        DataStore[PerformanceDataStore<br/>存储抽象层]
        RewardCalc[RewardCalculator<br/>奖励计算器]
        RecordBuilder[RecordBuilder<br/>记录构建器]
    end

    subgraph "存储层"
        SQLiteStore[SQLiteDataStore<br/>SQLite实现]
        CSVStore[CSVDataStore<br/>CSV实现]
        Database[(SQLite数据库)]
        Files[CSV文件]
    end

    subgraph "配置层"
        ConfigManager[ConfigManager<br/>配置管理]
        RewardConfigs[REWARD_CONFIGS<br/>奖励配置]
    end

    Pipeline --> DataStore
    Pipeline --> RewardCalc
    Pipeline --> RecordBuilder
    DataStore --> SQLiteStore
    DataStore --> CSVStore
    SQLiteStore --> Database
    CSVStore --> Files
    RewardCalc --> ConfigManager
    ConfigManager --> RewardConfigs
```

### 4. 核心对象设计（C4 - Code Level）

#### 4.1 领域对象关系图

```mermaid
classDiagram
    class Contract {
        +String id
        +Float amount
        +String housekeeper
        +String service_provider
        +String activity_code
        +OrderType order_type
        +DateTime signed_date
        +String project_address
        +is_historical() bool
        +get_housekeeper_key(format_type) String
        +calculate_performance_amount() Float
    }

    class HousekeeperStats {
        +String housekeeper
        +String activity_code
        +Int count
        +Float total_amount
        +Float performance_amount
        +List~String~ awarded_rewards
        +Int platform_count
        +Float platform_amount
        +Int self_referral_count
        +Float self_referral_amount
        +Set~String~ self_referral_projects
        +update_with_contract(contract) void
        +get_track_stats(order_type) TrackStats
    }

    class Reward {
        +String type
        +String name
        +Float amount
        +String reason
        +String badge_emoji
        +is_badge_reward() bool
        +format_message() String
    }

    class ProcessingConfig {
        +String config_key
        +String activity_code
        +CityCode city
        +String housekeeper_key_format
        +StorageType storage_type
        +Bool enable_dual_track
        +Bool enable_historical_contracts
        +get_reward_config() Dict
        +get_limits() Dict
    }

    class OrderType {
        <<enumeration>>
        PLATFORM
        SELF_REFERRAL
    }

    class CityCode {
        <<enumeration>>
        BEIJING
        SHANGHAI
    }

    class StorageType {
        <<enumeration>>
        SQLITE
        CSV
    }

    Contract --> OrderType
    Contract --> CityCode
    ProcessingConfig --> CityCode
    ProcessingConfig --> StorageType
    HousekeeperStats --> Contract : "aggregates"
    Reward --> Contract : "calculated from"
```

#### 4.2 对象协作图

```mermaid
sequenceDiagram
    participant Pipeline as DataProcessingPipeline
    participant Mapper as ContractMapper
    participant Contract as Contract
    participant Store as PerformanceDataStore
    participant Stats as HousekeeperStats
    participant Calculator as RewardCalculator
    participant Reward as Reward

    Pipeline->>Mapper: map_to_domain(raw_data)
    Mapper->>Contract: new Contract()
    Contract-->>Pipeline: contract

    Pipeline->>Store: contract_exists(id, activity_code)
    Store-->>Pipeline: false

    Pipeline->>Contract: get_housekeeper_key(format)
    Contract-->>Pipeline: housekeeper_key

    Pipeline->>Store: get_housekeeper_stats(key, activity)
    Store-->>Stats: new HousekeeperStats()
    Stats-->>Pipeline: stats

    Pipeline->>Calculator: calculate(contract, stats)
    Calculator->>Reward: new Reward()
    Reward-->>Calculator: reward
    Calculator-->>Pipeline: rewards[]

    Pipeline->>Store: save_contract(contract, rewards)
    Store->>Stats: update_with_contract(contract)
```

#### 4.3 存储抽象层设计

```mermaid
classDiagram
    class PerformanceDataStore {
        <<interface>>
        +contract_exists(id, activity_code) bool
        +get_housekeeper_stats(housekeeper, activity_code) HousekeeperStats
        +save_contract(contract, rewards) void
        +get_project_usage(project_id, activity_code) float
        +get_historical_awards(housekeeper, activity_code) List~String~
    }

    class SQLitePerformanceDataStore {
        -String db_path
        -Connection connection
        +contract_exists(id, activity_code) bool
        +get_housekeeper_stats(housekeeper, activity_code) HousekeeperStats
        +save_contract(contract, rewards) void
        +execute_aggregation_query(sql, params) Dict
        +init_database() void
        +create_indexes() void
    }

    class CSVPerformanceDataStore {
        -String csv_path
        -Dict cache
        +contract_exists(id, activity_code) bool
        +get_housekeeper_stats(housekeeper, activity_code) HousekeeperStats
        +save_contract(contract, rewards) void
        +load_csv_data() List~Dict~
        +write_csv_data(data) void
    }

    class DatabaseSchema {
        +performance_data table
        +contracts table
        +rewards table
        +housekeeper_stats view
    }

    PerformanceDataStore <|-- SQLitePerformanceDataStore
    PerformanceDataStore <|-- CSVPerformanceDataStore
    SQLitePerformanceDataStore --> DatabaseSchema
    SQLitePerformanceDataStore --> HousekeeperStats
    CSVPerformanceDataStore --> HousekeeperStats
```

#### 4.4 奖励计算器设计

```mermaid
classDiagram
    class RewardCalculator {
        -String config_key
        -Dict config
        -Dict awards_mapping
        +calculate(contract, stats) List~Reward~
        +calculate_lucky_reward(contract, stats) Reward
        +calculate_tiered_reward(stats) Reward
        +calculate_self_referral_reward(contract, stats) Reward
        +should_enable_badge(config_key) bool
    }

    class LuckyNumberCalculator {
        +calculate_by_contract_tail(contract, lucky_number) Reward
        +calculate_by_personal_sequence(stats, lucky_number) Reward
        +get_reward_level(amount, thresholds) String
    }

    class TieredRewardCalculator {
        +calculate_progressive_reward(count, tiers) Reward
        +get_tier_for_count(count, tiers) Dict
        +apply_badge_multiplier(reward, has_badge) Reward
    }

    class SelfReferralCalculator {
        +calculate_project_reward(contract, stats) Reward
        +is_new_project(project, existing_projects) bool
        +get_referral_config(config_key) Dict
    }

    RewardCalculator --> LuckyNumberCalculator
    RewardCalculator --> TieredRewardCalculator
    RewardCalculator --> SelfReferralCalculator
    RewardCalculator --> Reward
    RewardCalculator --> Contract
    RewardCalculator --> HousekeeperStats
```

#### 4.5 配置驱动设计

```mermaid
classDiagram
    class ConfigManager {
        +get_processing_config(city, month) ProcessingConfig
        +get_reward_config(config_key) Dict
        +get_notification_config(city) Dict
        +validate_config(config) bool
    }

    class RewardConfigs {
        +BJ_2025_06 Dict
        +BJ_2025_09 Dict
        +SH_2025_04 Dict
        +SH_2025_09 Dict
        +get_config(key) Dict
        +get_awards_mapping(key) Dict
        +get_performance_limits(key) Dict
    }

    class NotificationConfigs {
        +WECOM_GROUP_NAMES Dict
        +CAMPAIGN_CONTACTS Dict
        +MESSAGE_TEMPLATES Dict
        +get_group_name(city) String
        +get_contact(city) String
        +get_template(city, type) String
    }

    ConfigManager --> RewardConfigs
    ConfigManager --> NotificationConfigs
    ConfigManager --> ProcessingConfig
    RewardCalculator --> ConfigManager
    DataProcessingPipeline --> ConfigManager
```

## 解决方案：重建+SQLite

### 核心设计原则
1. **领域驱动设计**: 明确的领域对象和业务概念
2. **存储抽象层**: 支持SQLite和CSV两种实现
3. **数据库驱动**: 用SQL查询替代复杂的内存计算
4. **配置驱动**: 所有差异通过REWARD_CONFIGS控制
5. **管道化**: 标准化的数据处理流程
6. **彻底消除"伪复用"**: 停止通过全局篡改来复用不兼容的函数

## 阶段1：建立新骨架+SQLite（3-4天）

### 1.1 实现核心领域对象
**新建**: `modules/core/domain_models.py`

```python
from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict
from enum import Enum
from datetime import datetime

class CityCode(Enum):
    BEIJING = "BJ"
    SHANGHAI = "SH"

class OrderType(Enum):
    PLATFORM = "platform"
    SELF_REFERRAL = "self_referral"

class StorageType(Enum):
    SQLITE = "sqlite"
    CSV = "csv"

@dataclass
class Contract:
    """合同领域对象 - 统一所有城市的合同表示"""
    id: str
    amount: float
    housekeeper: str
    service_provider: str
    activity_code: str
    order_type: OrderType
    signed_date: datetime
    project_address: str
    pc_contract_num: Optional[str] = None  # 历史合同编号

    def is_historical(self) -> bool:
        """北京9月历史合同判断"""
        return self.pc_contract_num is not None

    def get_housekeeper_key(self, format_type: str) -> str:
        """根据城市生成管家键 - 解决北京/上海差异"""
        if format_type == "housekeeper_provider":
            return f"{self.housekeeper}_{self.service_provider}"
        return self.housekeeper

    def calculate_performance_amount(self, limits: Dict) -> float:
        """计算计入业绩金额 - 应用各种上限规则"""
        performance_amount = self.amount

        # 应用单合同上限
        if limits.get("enable_cap", False):
            cap = limits.get("single_contract_cap", float('inf'))
            performance_amount = min(performance_amount, cap)

        return performance_amount

@dataclass
class HousekeeperStats:
    """管家统计领域对象 - 替代复杂的字典结构"""
    housekeeper: str
    activity_code: str
    count: int = 0
    total_amount: float = 0.0
    performance_amount: float = 0.0
    awarded_rewards: List[str] = field(default_factory=list)

    # 双轨统计扩展（上海9月）
    platform_count: int = 0
    platform_amount: float = 0.0
    self_referral_count: int = 0
    self_referral_amount: float = 0.0
    self_referral_projects: Set[str] = field(default_factory=set)

    def update_with_contract(self, contract: Contract) -> None:
        """用新合同更新统计数据"""
        self.count += 1
        self.total_amount += contract.amount
        self.performance_amount += contract.calculate_performance_amount({})

        # 双轨统计更新
        if contract.order_type == OrderType.PLATFORM:
            self.platform_count += 1
            self.platform_amount += contract.amount
        elif contract.order_type == OrderType.SELF_REFERRAL:
            self.self_referral_count += 1
            self.self_referral_amount += contract.amount
            self.self_referral_projects.add(contract.project_address)

    def get_track_stats(self, order_type: OrderType) -> Dict:
        """获取指定轨道的统计数据"""
        if order_type == OrderType.PLATFORM:
            return {"count": self.platform_count, "amount": self.platform_amount}
        elif order_type == OrderType.SELF_REFERRAL:
            return {"count": self.self_referral_count, "amount": self.self_referral_amount}
        return {"count": self.count, "amount": self.total_amount}

@dataclass
class Reward:
    """奖励领域对象"""
    type: str
    name: str
    amount: float
    reason: str
    badge_emoji: str = ""

    def is_badge_reward(self) -> bool:
        """判断是否为徽章奖励"""
        return "徽章" in self.name or "新星" in self.name

    def format_message(self) -> str:
        """格式化奖励消息"""
        message = f"{self.name}: {self.amount}元"
        if self.badge_emoji:
            message = f"{self.badge_emoji} {message}"
        return message

@dataclass
class ProcessingConfig:
    """处理配置对象 - 替代硬编码的配置"""
    config_key: str
    activity_code: str
    city: CityCode
    housekeeper_key_format: str
    storage_type: StorageType = StorageType.SQLITE
    enable_dual_track: bool = False
    enable_historical_contracts: bool = False

    def get_reward_config(self) -> Dict:
        """获取奖励配置"""
        from modules.config import REWARD_CONFIGS
        return REWARD_CONFIGS.get(self.config_key, {})

    def get_limits(self) -> Dict:
        """获取金额限制配置"""
        return self.get_reward_config().get("performance_limits", {})
```

### 1.2 创建存储抽象层
**新建**: `modules/core/storage.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from .domain_models import Contract, HousekeeperStats

class PerformanceDataStore(ABC):
    """存储抽象层 - 支持多种存储实现"""

    @abstractmethod
    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """检查合同是否已存在"""
        pass

    @abstractmethod
    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> HousekeeperStats:
        """获取管家累计统计 - 替代复杂的内存计算"""
        pass

    @abstractmethod
    def save_contract(self, contract: Contract, rewards: List[Reward]) -> None:
        """保存合同和奖励信息"""
        pass

class SQLitePerformanceDataStore(PerformanceDataStore):
    """SQLite实现 - 大幅简化累计计算"""

    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM performance_data WHERE contract_id = ? AND activity_code = ?",
                (contract_id, activity_code)
            )
            return cursor.fetchone() is not None

    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> HousekeeperStats:
        """一条SQL替代50+行累计计算代码"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as count,
                    SUM(contract_amount) as total_amount,
                    SUM(performance_amount) as performance_amount,
                    -- 双轨统计
                    SUM(CASE WHEN order_type = 'platform' THEN 1 ELSE 0 END) as platform_count,
                    SUM(CASE WHEN order_type = 'platform' THEN contract_amount ELSE 0 END) as platform_amount,
                    SUM(CASE WHEN order_type = 'self_referral' THEN 1 ELSE 0 END) as self_referral_count,
                    SUM(CASE WHEN order_type = 'self_referral' THEN contract_amount ELSE 0 END) as self_referral_amount
                FROM performance_data
                WHERE housekeeper = ? AND activity_code = ?
            """, (housekeeper, activity_code))

            result = cursor.fetchone()
            return HousekeeperStats(
                housekeeper=housekeeper,
                activity_code=activity_code,
                count=result[0],
                total_amount=result[1],
                performance_amount=result[2],
                platform_count=result[3],
                platform_amount=result[4],
                self_referral_count=result[5],
                self_referral_amount=result[6]
            )
```

### 1.2 设计数据库Schema
**新建**: `modules/core/database_schema.sql`

```sql
CREATE TABLE performance_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_code TEXT NOT NULL,           -- 'BJ-JUN', 'BJ-SEP', 'SH-APR'
    contract_id TEXT NOT NULL,
    housekeeper TEXT NOT NULL,
    service_provider TEXT,
    contract_amount REAL NOT NULL,
    performance_amount REAL NOT NULL,
    order_type TEXT DEFAULT 'platform',    -- 支持双轨统计
    project_id TEXT,                       -- 工单编号
    reward_types TEXT,
    reward_names TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(activity_code, contract_id)
);

-- 索引优化
CREATE INDEX idx_housekeeper_activity ON performance_data(housekeeper, activity_code);
CREATE INDEX idx_contract_lookup ON performance_data(contract_id, activity_code);
```

### 1.4 创建处理管道
**新建**: `modules/core/processing_pipeline.py`

```python
from typing import List
from .domain_models import Contract, ProcessingConfig, HousekeeperStats
from .storage import PerformanceDataStore
from .reward_calculator import RewardCalculator
from .contract_mapper import ContractMapper

class DataProcessingPipeline:
    """统一数据处理管道 - 替代8个重复的Job函数"""

    def __init__(self, config: ProcessingConfig, store: PerformanceDataStore):
        self.config = config
        self.store = store
        self.reward_calculator = RewardCalculator(config.config_key)
        self.contract_mapper = ContractMapper(config.city)

    def process(self, raw_contract_data: List[dict]) -> List[dict]:
        """统一处理流程 - 消除城市间的重复逻辑"""
        processed_records = []

        for raw_contract in raw_contract_data:
            # 1. 原始数据映射为领域对象
            contract = self.contract_mapper.map_to_domain(raw_contract, self.config.activity_code)

            # 2. 数据库去重查询 - 替代CSV文件扫描
            if self.store.contract_exists(contract.id, contract.activity_code):
                continue

            # 3. 数据库聚合查询 - 替代复杂内存计算
            housekeeper_key = contract.get_housekeeper_key(self.config.housekeeper_key_format)
            hk_stats = self.store.get_housekeeper_stats(housekeeper_key, contract.activity_code)

            # 4. 奖励计算 - 配置驱动
            rewards = self.reward_calculator.calculate(contract, hk_stats)

            # 5. 保存到存储层
            self.store.save_contract(contract, rewards)

            # 6. 构建输出记录
            record = self._build_output_record(contract, hk_stats, rewards)
            processed_records.append(record)

        return processed_records

    def _build_output_record(self, contract: Contract, stats: HousekeeperStats, rewards: List[Reward]) -> dict:
        """构建输出记录 - 统一字段格式"""
        base_record = {
            '活动编号': contract.activity_code,
            '合同ID(_id)': contract.id,
            '管家(serviceHousekeeper)': contract.housekeeper,
            '合同金额(adjustRefundMoney)': contract.amount,
            '管家累计单数': stats.count + 1,  # +1 因为包含当前合同
            '管家累计金额': stats.total_amount + contract.amount,
            '奖励类型': ', '.join([r.type for r in rewards]),
            '奖励名称': ', '.join([r.name for r in rewards]),
            '激活奖励状态': 1 if rewards else 0
        }

        # 城市特定字段扩展
        if self.config.enable_dual_track:
            base_record.update({
                '工单类型': '自引单' if contract.order_type == OrderType.SELF_REFERRAL else '平台单',
                '平台单累计数量': stats.platform_count,
                '平台单累计金额': stats.platform_amount,
                '自引单累计数量': stats.self_referral_count,
                '自引单累计金额': stats.self_referral_amount
            })

        return base_record
```

### 1.5 创建奖励计算器
**新建**: `modules/core/reward_calculator.py`

```python
from typing import List
from .domain_models import Contract, HousekeeperStats, Reward
from modules.config import REWARD_CONFIGS

class RewardCalculator:
    """配置驱动的奖励计算器 - 替代硬编码的奖励逻辑"""

    def __init__(self, config_key: str):
        self.config = REWARD_CONFIGS[config_key]
        self.config_key = config_key

    def calculate(self, contract: Contract, hk_stats: HousekeeperStats) -> List[Reward]:
        """计算所有类型的奖励"""
        rewards = []

        # 幸运数字奖励
        lucky_reward = self._calculate_lucky_reward(contract, hk_stats)
        if lucky_reward:
            rewards.append(lucky_reward)

        # 节节高奖励
        tiered_reward = self._calculate_tiered_reward(hk_stats)
        if tiered_reward:
            rewards.append(tiered_reward)

        # 自引单奖励（上海9月）
        if self.config.get("self_referral_rewards", {}).get("enable", False):
            self_referral_reward = self._calculate_self_referral_reward(contract, hk_stats)
            if self_referral_reward:
                rewards.append(self_referral_reward)

        return rewards

    def _calculate_lucky_reward(self, contract: Contract, hk_stats: HousekeeperStats) -> Optional[Reward]:
        """幸运数字奖励计算 - 支持合同尾号和个人顺序两种模式"""
        lucky_config = self.config.get("lucky_rewards", {})
        if not lucky_config:
            return None

        lucky_number = self.config.get("lucky_number", "")
        if not lucky_number:
            return None

        mode = self.config.get("lucky_number_mode", "contract_tail")

        if mode == "personal_sequence":
            # 北京9月：个人签约顺序模式
            personal_sequence = hk_stats.count + 1
            if personal_sequence % int(lucky_number) == 0:
                return Reward(
                    type="幸运数字",
                    name=lucky_config["base"]["name"],
                    amount=float(self.config["awards_mapping"][lucky_config["base"]["name"]]),
                    reason=f"个人第{personal_sequence}个合同"
                )
        else:
            # 传统模式：合同编号尾号
            if contract.id.endswith(lucky_number):
                reward_key = "high" if contract.amount >= lucky_config["high"]["threshold"] else "base"
                reward_name = lucky_config[reward_key]["name"]
                return Reward(
                    type="幸运数字",
                    name=reward_name,
                    amount=float(self.config["awards_mapping"][reward_name]),
                    reason=f"合同编号尾号{lucky_number}"
                )

        return None
```

### 1.6 架构对比：重构前 vs 重构后

#### 重构前的问题架构
```mermaid
graph TB
    subgraph "当前问题架构"
        Job1[北京6月Job] --> Process1[process_data_jun_beijing]
        Job2[北京8月Job] --> Process1
        Job3[北京9月Job] --> Wrapper[process_data_sep_beijing包装]
        Wrapper --> |全局篡改| Process1
        Wrapper --> |历史合同| Process2[process_data_sep_beijing_with_historical_support]

        Job4[上海4月Job] --> Process3[process_data_shanghai_apr]
        Job5[上海8月Job] --> Process3
        Job6[上海9月Job] --> Process4[process_data_shanghai_sep]

        Process1 --> |硬编码| Config1[全局变量]
        Process3 --> |硬编码| Config1
        Process4 --> |硬编码| Config2[REWARD_CONFIGS]

        Process1 --> |复杂内存计算| Memory[housekeeper_contracts字典]
        Process3 --> |复杂内存计算| Memory
        Process4 --> |复杂内存计算| Memory2[扩展字典+双轨统计]

        Memory --> CSV[CSV文件读写]
        Memory2 --> CSV
    end

    style Wrapper fill:#ffcccc
    style Memory fill:#ffcccc
    style Memory2 fill:#ffcccc
    style Config1 fill:#ffcccc
```

#### 重构后的目标架构
```mermaid
graph TB
    subgraph "目标统一架构"
        JobTemplate[统一Job模板] --> Pipeline[DataProcessingPipeline]
        Pipeline --> Store[PerformanceDataStore抽象层]
        Pipeline --> Calculator[RewardCalculator]
        Pipeline --> Mapper[ContractMapper]

        Store --> SQLite[SQLiteDataStore]
        Store --> CSV[CSVDataStore]
        SQLite --> DB[(SQLite数据库)]
        CSV --> Files[CSV文件]

        Calculator --> Config[REWARD_CONFIGS统一配置]
        Mapper --> DomainModel[Contract领域对象]

        Pipeline --> Stats[HousekeeperStats领域对象]
        Stats --> |SQL聚合查询| DB
    end

    style Pipeline fill:#ccffcc
    style Store fill:#ccffcc
    style Config fill:#ccffcc
    style DomainModel fill:#ccffcc
```

### 1.7 系统对象协作总览

```mermaid
graph TB
    subgraph "领域层 (Domain Layer)"
        Contract[Contract<br/>合同对象]
        Stats[HousekeeperStats<br/>管家统计对象]
        Reward[Reward<br/>奖励对象]
        Config[ProcessingConfig<br/>配置对象]
    end

    subgraph "应用层 (Application Layer)"
        Pipeline[DataProcessingPipeline<br/>处理管道]
        Calculator[RewardCalculator<br/>奖励计算器]
        Mapper[ContractMapper<br/>合同映射器]
        NotificationEngine[NotificationEngine<br/>通知引擎]
    end

    subgraph "基础设施层 (Infrastructure Layer)"
        Store[PerformanceDataStore<br/>存储抽象]
        SQLiteStore[SQLiteDataStore<br/>SQLite实现]
        CSVStore[CSVDataStore<br/>CSV实现]
        Database[(SQLite数据库)]
        Files[CSV文件]
    end

    subgraph "配置层 (Configuration Layer)"
        RewardConfigs[REWARD_CONFIGS<br/>奖励配置]
        NotificationConfigs[通知配置]
    end

    Pipeline --> Contract
    Pipeline --> Stats
    Pipeline --> Calculator
    Pipeline --> Mapper
    Pipeline --> Store

    Calculator --> Reward
    Calculator --> RewardConfigs

    Mapper --> Contract

    Store --> SQLiteStore
    Store --> CSVStore
    SQLiteStore --> Database
    CSVStore --> Files

    Config --> RewardConfigs
    NotificationEngine --> NotificationConfigs

    Contract -.-> Stats : "aggregates to"
    Stats -.-> Reward : "triggers"

    style Contract fill:#e1f5fe
    style Stats fill:#e1f5fe
    style Reward fill:#e1f5fe
    style Config fill:#e1f5fe
    style Pipeline fill:#f3e5f5
    style Calculator fill:#f3e5f5
    style Store fill:#e8f5e8
    style Database fill:#fff3e0
```

### 1.8 对象设计原则验证

#### 单一职责原则 (SRP)
- **Contract**: 只负责合同数据和相关业务逻辑
- **HousekeeperStats**: 只负责管家统计数据的聚合
- **Reward**: 只负责奖励信息的表示和格式化
- **RewardCalculator**: 只负责奖励计算逻辑

#### 开闭原则 (OCP)
- **PerformanceDataStore**: 抽象接口，可扩展新的存储实现
- **RewardCalculator**: 可扩展新的奖励类型而不修改现有代码
- **ProcessingConfig**: 可添加新的配置项而不影响现有功能

#### 依赖倒置原则 (DIP)
- **DataProcessingPipeline**: 依赖抽象的PerformanceDataStore，不依赖具体实现
- **RewardCalculator**: 依赖配置接口，不依赖具体配置实现

#### 接口隔离原则 (ISP)
- **PerformanceDataStore**: 接口方法职责单一，客户端只依赖需要的方法
- **Contract**: 提供特定的业务方法，不强迫客户端依赖不需要的功能

### 验收标准
- [ ] **领域对象模型完成**
  - [ ] Contract、HousekeeperStats、Reward等核心对象
  - [ ] 枚举类型定义（CityCode、OrderType、StorageType）
  - [ ] 对象行为方法实现（业务逻辑封装）
  - [ ] 对象关系图和协作图绘制完成
- [ ] **存储抽象层完成**
  - [ ] PerformanceDataStore抽象接口设计
  - [ ] SQLite和CSV两种具体实现
  - [ ] 配置驱动的存储选择机制
  - [ ] 存储层类图设计完成
- [ ] **处理管道实现**
  - [ ] DataProcessingPipeline统一处理流程
  - [ ] ContractMapper领域对象映射
  - [ ] 配置驱动的差异处理机制
  - [ ] 对象协作序列图验证
- [ ] **架构设计验证**
  - [ ] 组件间依赖关系清晰（依赖图）
  - [ ] SOLID原则遵循验证
  - [ ] 扩展性设计验证（新城市/新功能）
  - [ ] 系统对象协作总览图完成
- [ ] **单元测试覆盖率≥90%**
  - [ ] 每个领域对象的单元测试
  - [ ] 每个应用服务的单元测试
  - [ ] 存储层的集成测试

## 阶段2：北京迁移（2-3天）

### 2.1 北京6月迁移（基准验证）

#### 配置对象化
```python
# 新的配置对象 - 替代硬编码
BJ_JUN_CONFIG = ProcessingConfig(
    config_key="BJ-2025-06",
    activity_code="BJ-JUN",
    city=CityCode.BEIJING,
    housekeeper_key_format="housekeeper",
    storage_type="sqlite",
    enable_dual_track=False,
    enable_historical_contracts=False
)
```

#### 架构迁移对比
```mermaid
graph LR
    subgraph "迁移前"
        OldJob[signing_and_sales_incentive_jun_beijing] --> OldProcess[process_data_jun_beijing]
        OldProcess --> |硬编码| OldConfig[全局变量]
        OldProcess --> |复杂计算| OldMemory[housekeeper_contracts字典]
        OldMemory --> OldCSV[CSV读写]
    end

    subgraph "迁移后"
        NewJob[signing_and_sales_incentive_jun_beijing] --> Pipeline[DataProcessingPipeline]
        Pipeline --> Store[SQLiteDataStore]
        Pipeline --> Calculator[RewardCalculator]
        Calculator --> NewConfig[REWARD_CONFIGS]
        Store --> DB[(SQLite数据库)]
    end

    OldJob -.->|重构| NewJob
    style Pipeline fill:#ccffcc
    style Store fill:#ccffcc
```

#### 新的Job函数实现
```python
def signing_and_sales_incentive_jun_beijing():
    """重构后的北京6月Job - 使用统一架构"""
    # 1. 配置对象化
    config = BJ_JUN_CONFIG
    store = SQLitePerformanceDataStore("performance.db")

    # 2. 统一处理管道
    pipeline = DataProcessingPipeline(config, store)

    # 3. 获取原始数据
    raw_data = fetch_contract_data_from_metabase(config.api_url)

    # 4. 处理数据 - 消除全局副作用和复杂计算
    processed_data = pipeline.process(raw_data)

    # 5. 通知发送
    notification_engine = NotificationEngine(config)
    notification_engine.send_notifications(processed_data)

    return processed_data
```

### 2.2 北京9月迁移（消除全局副作用）
```python
# 配置
BJ_SEP_CONFIG = ProcessingConfig(
    config_key="BJ-2025-09",  # 直接使用正确配置
    activity_code="BJ-SEP",
    city="BJ",
    housekeeper_key_format="管家",
    enable_historical_contracts=True
)

# 删除问题代码
# 删除 modules/data_processing_module.py:1575-1582 的全局篡改逻辑
# 删除 process_data_sep_beijing 包装函数
```

### 验收标准
- [ ] 消除所有全局副作用
- [ ] 北京测试全部通过
- [ ] 数据输出100%等价
- [ ] 性能不降级

## 阶段3：上海迁移（3-4天）

### 3.1 上海双轨统计简化
```python
# 当前复杂的双轨维护
housekeeper_contracts[hk_key] = {
    'platform_count': 0, 'platform_amount': 0,
    'self_referral_count': 0, 'self_referral_amount': 0,
    'self_referral_projects': set()  # 复杂的去重逻辑
}

# SQLite简化后
SELECT 
    order_type,
    COUNT(*) as count,
    SUM(amount) as amount
FROM performance_data 
WHERE housekeeper = ? AND activity_code = ?
GROUP BY order_type
```

### 3.2 上海配置
```python
SH_SEP_CONFIG = ProcessingConfig(
    config_key="SH-2025-09",
    activity_code="SH-SEP",
    city="SH",
    housekeeper_key_format="管家_服务商",
    enable_dual_track=True  # 启用双轨统计
)
```

### 验收标准
- [ ] 双轨统计逻辑正确
- [ ] 8个扩展字段正确
- [ ] 所有上海测试通过

## 阶段4：清理优化（1-2天）

### 4.1 删除旧代码
- 删除 `process_data_jun_beijing`
- 删除 `process_data_shanghai_apr`
- 删除 `process_data_shanghai_sep`
- 删除所有全局副作用代码

### 4.2 统一Job函数
```python
def execute_monthly_incentive(city: str, month: str):
    """统一的月度激励执行函数"""
    config = get_monthly_config(city, month)
    pipeline = DataProcessingPipeline(config, SQLitePerformanceDataStore())
    return pipeline.process(contract_data)

# 替换所有具体Job函数
signing_and_sales_incentive_jun_beijing = lambda: execute_monthly_incentive("BJ", "jun")
signing_and_sales_incentive_sep_shanghai = lambda: execute_monthly_incentive("SH", "sep")
```

## 预期收益

### 代码简化
- **代码行数减少60%+**: SQL查询替代复杂累计逻辑
- **函数数量减少50%+**: 合并重复函数
- **消除全局副作用**: 提升测试稳定性

### 性能提升
- **去重查询**: O(n)→O(1)，索引查询替代文件扫描
- **累计统计**: 数据库聚合查询替代内存循环
- **内存使用**: 不再加载整个CSV到内存

### 系统稳定性
- **数据一致性**: 事务保证，避免CSV竞争条件
- **并发安全**: 数据库锁机制
- **扩展性**: 便于复杂查询和报表生成

## 风险控制

### 1. 存储抽象层
- 同时支持SQLite和CSV
- 配置驱动选择存储方式
- 测试使用内存SQLite

### 2. 渐进迁移
- 每个阶段独立验证
- 完整的等价性测试
- 快速回滚机制

### 3. 影子模式
- SQLite与CSV并行运行1周
- 验证数据一致性和性能
- 监控系统稳定性

## 实施时间表

- **阶段1**: 3-4天（建立新骨架+SQLite）
- **阶段2**: 2-3天（北京迁移验证）
- **阶段3**: 3-4天（上海迁移）
- **阶段4**: 1-2天（清理优化）
- **影子模式**: 1周（并行验证）
- **全量上线**: 1周（监控稳定性）
- **总计**: 4-5周

## 下一步行动

1. **立即开始阶段1**: 建立存储抽象层和SQLite实现
2. **并行准备**: 设计数据库Schema和处理管道
3. **测试准备**: 准备等价性验证脚本
4. **团队同步**: 确保团队理解新架构设计

---

**文档版本**: v1.0  
**创建日期**: 2025-01-08  
**策略**: 重建+迁移+SQLite集成  
**预期收益**: 代码减少60%+，性能大幅提升，系统稳定性显著改善
