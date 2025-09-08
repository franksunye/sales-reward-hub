# 代码重构升级方案

## 概述

本文档详细描述了对当前签约激励系统的重构升级方案。当前系统经过大量迭代后，代码结构复杂，存在全局副作用、通知逻辑重复、配置散乱等问题。本方案采用渐进式重构策略，分三个Sprint完成，确保每步可回滚、可测试。

## 深度问题分析（基于完整代码研读）

### 1. 北京月份演进的"伪复用"问题

#### 1.1 北京6月→8月→9月的复用陷阱
**核心问题**: 为了复用6月的`process_data_jun_beijing`函数，后续月份采用了"包装+篡改"的方式

**北京8月的实现**:
```python
# jobs.py:39 - 8月直接复用6月函数，但配置不同
processed_data = process_data_jun_beijing(contract_data, existing_contract_ids, housekeeper_award_lists)
# 使用6月的配置 "BJ-2025-06"，但实际是8月活动
```

**北京9月的复杂包装**:
```python
# data_processing_module.py:1575-1582 - 全局篡改方式
globals()['determine_rewards_jun_beijing_generic'] = determine_rewards_sep_beijing_generic
config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000  # 临时改为5万
try:
    result = process_data_jun_beijing(...)  # 复用6月函数
    for record in result:
        record['活动编号'] = 'BJ-SEP'  # 事后修改活动编号
finally:
    # 恢复全局状态
```

**问题根源**:
- 6月函数硬编码了太多假设（50万上限、"BJ-JUN"活动编号等）
- 为了复用而不是重构，导致9月逻辑极其复杂
- 全局副作用使得并发测试不可靠

#### 1.2 北京9月的历史合同处理复杂性
**新增复杂度**: 9月引入了历史合同处理，导致包装函数内部又有分支:
```python
# data_processing_module.py:1565-1572
def process_data_sep_beijing(contract_data, existing_contract_ids, housekeeper_award_lists):
    has_historical_field = any('pcContractdocNum' in contract for contract in contract_data)
    if has_historical_field:
        return process_data_sep_beijing_with_historical_support(...)  # 新逻辑
    else:
        # 全局篡改 + 复用6月逻辑
```

**结果**: 一个函数内部有两套完全不同的处理路径，维护噩梦

### 2. 上海月份演进的"复制粘贴"问题

#### 2.1 上海4月→8月→9月的重复演进
**上海8月复用4月**:
```python
# jobs.py:80 - 8月复用4月函数
processed_data = process_data_shanghai_apr(contract_data, existing_contract_ids, housekeeper_award_lists)
# 注释说"奖励规则与4月保持一致"，但实际是8月活动
```

**上海9月全新实现**:
```python
# 完全独立的 process_data_shanghai_sep 函数
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
- 4月和9月的管家统计结构完全不兼容
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

### 3. 通知模块的"三套马车"问题

#### 3.1 北京通知的演进路径
**已合并**: 北京通知已经通过`notify_awards_beijing_generic`实现了统一
```python
# notification_module.py:291-307 - 薄包装函数
def notify_awards_jun_beijing(performance_data_filename, status_filename):
    return notify_awards_beijing_generic(..., "BJ-2025-06", enable_rising_star_badge=True)

def notify_awards_sep_beijing(performance_data_filename, status_filename):
    return notify_awards_beijing_generic(..., "BJ-2025-09", enable_rising_star_badge=False)
```

#### 3.2 上海通知的分裂状态
**三套不同逻辑**:
1. **上海3月旧版**: `notify_awards_shanghai_generate_message_march` (309-356行)
2. **上海9月新版**: `notify_awards_shanghai_generic` (400-463行)
3. **上海8月**: 复用3月旧版逻辑

**关键差异**:
- 消息模板不同（转化率显示、双轨统计等）
- 字段处理逻辑不同
- 配置获取方式不同

### 4. 配置系统的"新旧并存"问题

#### 4.1 新配置系统 vs 旧全局变量
**新系统**: `REWARD_CONFIGS` 统一配置（config.py:9-162）
**旧系统**: 散落的全局变量仍在使用
```python
# 旧变量仍在使用
PERFORMANCE_AMOUNT_CAP_BJ_FEB = 500000  # line:257
ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB = True  # line:259
SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB = 500000  # line:255
```

**问题**: 北京9月通过临时修改旧变量来影响6月函数的行为

#### 4.2 配置键命名不一致
**北京**: "BJ-2025-06", "BJ-2025-09"
**上海**: "SH-2025-04", "SH-2025-09"
**问题**: 8月份活动复用了其他月份的配置，配置键与实际月份不匹配

### 5. 数据字段的"渐进膨胀"问题

#### 5.1 CSV字段的不断增加
**北京6月**: 29个字段
**北京9月**: 32个字段（新增3个历史合同相关字段）
**上海9月**: 37个字段（新增8个双轨统计字段）

#### 5.2 字段处理逻辑分散
**问题**: 每个月份的字段构建逻辑都硬编码在各自的函数中
- 北京6月: data_processing_module.py:391-421 (30行字典构建)
- 上海4月: data_processing_module.py:506-536 (30行字典构建)
- 上海9月: data_processing_module.py:737-778 (40行字典构建)

**影响**:
- 无法复用字段构建逻辑
- 新增字段需要修改多个地方
- 字段顺序和命名容易不一致

### 6. 任务编排的"通配符导入"问题

#### 6.1 依赖关系不明确
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

#### 6.2 Job函数的"复制粘贴"演进
**模式**: 每个新月份都复制上个月份的Job函数，然后修改部分参数
**结果**:
- 8个几乎相同的Job函数（北京3个+上海3个+其他2个）
- 每个函数50-100行，大部分代码重复
- 修改通用逻辑需要改8个地方

## 重构目标（基于深度分析）

### 核心目标
1. **彻底消除"伪复用"**: 停止通过全局篡改来复用不兼容的函数
2. **建立真正的通用骨架**: 数据处理、奖励计算、通知发送的标准化流程
3. **统一数据模型**: 管家统计结构、字段构建逻辑、配置驱动方式
4. **消除复制粘贴演进**: Job函数、通知逻辑、字段构建的模板化
5. **配置系统现代化**: 完全迁移到REWARD_CONFIGS，废弃旧全局变量

### 具体量化目标
- **代码行数减少40%**: 从当前~2000行核心逻辑减少到~1200行
- **函数数量减少50%**: 合并重复的处理和通知函数
- **配置统一度100%**: 所有差异通过REWARD_CONFIGS控制
- **测试稳定性提升**: 消除全局副作用导致的测试不稳定

## 重构策略（重新设计）

### 策略调整原因
经过深度代码分析发现，原计划的"渐进式重构"存在问题：
1. **北京9月的复杂性**: 不仅有全局副作用，还有历史合同处理的双重逻辑
2. **上海的数据结构差异**: 双轨统计与标准统计无法简单合并
3. **通知逻辑的深度差异**: 不仅是模板差异，还有字段处理逻辑差异

### 新策略：**"重建+迁移"**
采用**重建核心骨架，逐步迁移**的策略：

#### 阶段1：建立新骨架（2-3天）
- 设计统一的数据处理管道
- 建立标准的管家统计模型
- 创建配置驱动的奖励计算器
- 实现通用的通知生成器

#### 阶段2：北京迁移（2-3天）
- 将北京6月/8月/9月迁移到新骨架
- 验证功能等价性
- 删除旧的北京处理函数

#### 阶段3：上海迁移（3-4天）
- 将上海4月/8月/9月迁移到新骨架
- 处理双轨统计的特殊需求
- 验证功能等价性

#### 阶段4：清理优化（1-2天）
- 删除所有旧代码
- 优化Job函数
- 完善文档和测试

### 风险控制策略
1. **并行开发**: 新骨架与现有系统并行，不影响生产
2. **逐个迁移**: 每次只迁移一个城市/月份，降低风险
3. **完整验证**: 每次迁移都进行100%等价性验证
4. **快速回滚**: 保留旧代码直到全部迁移完成

## 阶段1：建立新骨架（重建核心架构 + SQLite集成）

### 目标
设计并实现统一的数据处理管道，**同时引入SQLite数据库**，彻底解决"中间计算持久化"问题。

### 为什么现在是引入SQLite的最佳时机

#### 1. 当前"中间计算"问题的严重性
通过代码分析发现，当前系统的复杂性很大程度上来自"手工维护累计状态"：

**问题1: 复杂的housekeeper_contracts字典维护**
```python
# 每个处理函数都要维护这样的复杂结构
housekeeper_contracts[housekeeper] = {
    'count': 0, 'total_amount': 0, 'performance_amount': 0, 'awarded': [],
    'platform_count': 0, 'platform_amount': 0,      # 上海9月新增
    'self_referral_count': 0, 'self_referral_amount': 0,  # 上海9月新增
    'self_referral_projects': set(),  # 上海9月新增
    'self_referral_rewards': 0        # 上海9月新增
}
```

**问题2: 重复的去重逻辑**
```python
# 每个Job都要读取整个CSV文件
existing_contract_ids = collect_unique_contract_ids_from_file(performance_data_filename)
if contract_id in existing_contract_ids:
    continue
```

**问题3: 复杂的历史数据查询**
```python
# 北京9月的历史合同处理特别复杂
housekeeper_award_lists = get_housekeeper_award_list(performance_data_filename)
existing_housekeeper_stats = load_existing_housekeeper_stats_from_performance_file()
```

#### 2. SQLite的完美契合度
- **重建时机**: 我们正在重建核心架构，改存储层成本最低
- **复杂性消除**: 数据库天然擅长累计计算和去重查询
- **新架构适配**: HousekeeperStats模型可直接映射为数据库表

### 核心设计原则
1. **配置驱动**: 所有差异通过REWARD_CONFIGS控制
2. **管道化**: 数据获取→处理→奖励计算→通知发送的标准流程
3. **存储抽象**: 支持SQLite和CSV两种存储方式，保持灵活性
4. **可扩展**: 新增城市/月份只需添加配置，无需修改代码
5. **无副作用**: 纯函数设计，无全局状态修改

### 具体任务

#### 1.1 设计存储抽象层
**新建**: `modules/core/storage.py`

```python
from abc import ABC, abstractmethod
from typing import Set, List, Dict, Optional
import sqlite3
import csv

class PerformanceDataStore(ABC):
    """性能数据存储抽象接口"""

    @abstractmethod
    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """检查合同是否已存在"""
        pass

    @abstractmethod
    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> Dict:
        """获取管家累计统计数据"""
        pass

    @abstractmethod
    def get_housekeeper_awards(self, housekeeper: str, activity_code: str) -> List[str]:
        """获取管家历史奖励列表"""
        pass

    @abstractmethod
    def save_performance_record(self, record: Dict) -> None:
        """保存业绩记录"""
        pass

    @abstractmethod
    def get_project_usage(self, project_id: str, activity_code: str) -> float:
        """获取项目累计使用金额（北京工单上限用）"""
        pass

class SQLitePerformanceDataStore(PerformanceDataStore):
    """SQLite实现 - 大幅简化累计计算"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    def contract_exists(self, contract_id: str, activity_code: str) -> bool:
        """简化的去重查询"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM performance_data WHERE contract_id = ? AND activity_code = ?",
                (contract_id, activity_code)
            )
            return cursor.fetchone() is not None

    def get_housekeeper_stats(self, housekeeper: str, activity_code: str) -> Dict:
        """数据库聚合查询 - 替代复杂的内存计算"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as count,
                    COALESCE(SUM(contract_amount), 0) as total_amount,
                    COALESCE(SUM(performance_amount), 0) as performance_amount,
                    COALESCE(SUM(CASE WHEN order_type = 'platform' THEN 1 ELSE 0 END), 0) as platform_count,
                    COALESCE(SUM(CASE WHEN order_type = 'platform' THEN contract_amount ELSE 0 END), 0) as platform_amount,
                    COALESCE(SUM(CASE WHEN order_type = 'self_referral' THEN 1 ELSE 0 END), 0) as self_referral_count,
                    COALESCE(SUM(CASE WHEN order_type = 'self_referral' THEN contract_amount ELSE 0 END), 0) as self_referral_amount
                FROM performance_data
                WHERE housekeeper = ? AND activity_code = ?
            """, (housekeeper, activity_code))

            result = cursor.fetchone()
            return {
                'count': result[0],
                'total_amount': result[1],
                'performance_amount': result[2],
                'platform_count': result[3],
                'platform_amount': result[4],
                'self_referral_count': result[5],
                'self_referral_amount': result[6]
            }

class CSVPerformanceDataStore(PerformanceDataStore):
    """CSV实现 - 向后兼容"""
    # 保持现有的CSV逻辑，确保迁移安全
```

#### 1.2 设计数据库Schema
**新建**: `modules/core/database_schema.sql`

```sql
-- 统一的业绩数据表，支持所有城市和月份
CREATE TABLE performance_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_code TEXT NOT NULL,           -- 'BJ-JUN', 'BJ-SEP', 'SH-APR', 'SH-SEP'
    contract_id TEXT NOT NULL,
    housekeeper TEXT NOT NULL,
    service_provider TEXT,
    contract_amount REAL NOT NULL,
    performance_amount REAL NOT NULL,
    order_type TEXT DEFAULT 'platform',    -- 'platform' or 'self_referral'
    project_id TEXT,                       -- 工单编号，用于北京的项目上限
    reward_types TEXT,
    reward_names TEXT,
    is_historical BOOLEAN DEFAULT FALSE,   -- 北京9月历史合同标记
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 扩展字段（JSON格式存储城市特有数据）
    extensions TEXT,                       -- JSON格式存储额外字段

    UNIQUE(activity_code, contract_id)
);

-- 索引优化查询性能
CREATE INDEX idx_housekeeper_activity ON performance_data(housekeeper, activity_code);
CREATE INDEX idx_contract_lookup ON performance_data(contract_id, activity_code);
CREATE INDEX idx_project_activity ON performance_data(project_id, activity_code);
CREATE INDEX idx_order_type ON performance_data(order_type, activity_code);
```

#### 1.3 设计统一数据模型
**新建**: `modules/core/data_models.py`

```python
@dataclass
class HousekeeperStats:
    """标准管家统计数据结构 - 直接从数据库查询获得"""
    count: int = 0
    total_amount: float = 0.0
    performance_amount: float = 0.0
    awarded: List[str] = field(default_factory=list)

    # 双轨统计字段（上海9月）
    platform_count: int = 0
    platform_amount: float = 0.0
    self_referral_count: int = 0
    self_referral_amount: float = 0.0

@dataclass
class ProcessingConfig:
    """处理配置数据结构"""
    config_key: str
    activity_code: str
    city: str
    housekeeper_key_format: str  # "管家" 或 "管家_服务商"
    storage_type: str = "sqlite"  # "sqlite" 或 "csv"
    enable_dual_track: bool = False
    enable_historical_contracts: bool = False
```

#### 1.4 创建数据库驱动的处理管道
**新建**: `modules/core/processing_pipeline.py`

```python
class DataProcessingPipeline:
    """数据库驱动的统一处理管道 - 大幅简化逻辑"""

    def __init__(self, config: ProcessingConfig, store: PerformanceDataStore):
        self.config = config
        self.store = store
        self.reward_calculator = RewardCalculator(config.config_key)
        self.record_builder = RecordBuilder(config)

    def process(self, contract_data):
        """主处理流程 - 消除复杂的内存状态维护"""
        performance_records = []

        for contract in contract_data:
            contract_id = str(contract['合同ID(_id)'])

            # 1. 数据库去重查询 - 替代复杂的CSV读取
            if self.store.contract_exists(contract_id, self.config.activity_code):
                continue

            # 2. 数据库聚合查询 - 替代复杂的内存累计计算
            housekeeper = self._build_housekeeper_key(contract)
            hk_stats = self.store.get_housekeeper_stats(housekeeper, self.config.activity_code)
            hk_awards = self.store.get_housekeeper_awards(housekeeper, self.config.activity_code)

            # 3. 处理工单金额上限（北京特有）
            if self.config.city == "BJ":
                project_usage = self.store.get_project_usage(
                    contract['工单编号(serviceAppointmentNum)'],
                    self.config.activity_code
                )
                # 应用工单级别的金额上限逻辑
                performance_amount = self._apply_project_limit(contract, project_usage)
            else:
                performance_amount = self._calculate_performance_amount(contract)

            # 4. 计算奖励
            rewards = self.reward_calculator.calculate(contract, hk_stats, hk_awards)

            # 5. 构建并保存记录
            record = self.record_builder.build(contract, hk_stats, rewards, performance_amount)
            self.store.save_performance_record(record)
            performance_records.append(record)

        return performance_records

    def _build_housekeeper_key(self, contract):
        """根据城市构建管家键"""
        if self.config.housekeeper_key_format == "管家_服务商":
            return f"{contract['管家(serviceHousekeeper)']}_{contract['服务商(orgName)']}"
        else:
            return contract['管家(serviceHousekeeper)']
```

#### 1.3 创建配置驱动的奖励计算器
**新建**: `modules/core/reward_calculator.py`

```python
class RewardCalculator:
    """配置驱动的奖励计算器"""

    def __init__(self, config_key: str):
        self.config = REWARD_CONFIGS[config_key]

    def calculate(self, contract, housekeeper_stats):
        """计算所有类型的奖励"""
        rewards = []

        # 幸运数字奖励
        lucky_reward = self._calculate_lucky_reward(contract, housekeeper_stats)
        if lucky_reward:
            rewards.append(lucky_reward)

        # 节节高奖励
        tiered_reward = self._calculate_tiered_reward(housekeeper_stats)
        if tiered_reward:
            rewards.append(tiered_reward)

        # 自引单奖励（如果启用）
        if self.config.get("enable_self_referral"):
            self_referral_reward = self._calculate_self_referral_reward(contract, housekeeper_stats)
            if self_referral_reward:
                rewards.append(self_referral_reward)

        return rewards
```

#### 1.4 创建通用通知生成器
**新建**: `modules/core/notification_generator.py`

```python
class NotificationGenerator:
    """通用通知生成器"""

    def __init__(self, config_key: str, city: str):
        self.config_key = config_key
        self.city = city
        self.awards_mapping = get_awards_mapping(config_key)

    def generate_group_message(self, record):
        """生成群通知消息"""
        template = self._get_group_message_template()
        return template.format(**self._prepare_template_data(record))

    def generate_award_message(self, record):
        """生成个人奖励消息"""
        return generate_award_message(record, self.awards_mapping, self.city, self.config_key)

    def _get_group_message_template(self):
        """根据城市获取消息模板"""
        if self.city == "BJ":
            return BEIJING_GROUP_MESSAGE_TEMPLATE
        elif self.city == "SH":
            return SHANGHAI_GROUP_MESSAGE_TEMPLATE
        else:
            raise ValueError(f"Unsupported city: {self.city}")
```

#### 1.5 创建标准Job模板
**新建**: `modules/core/job_template.py`

```python
def execute_incentive_job(job_config: JobConfig):
    """标准激励Job执行模板"""

    # 1. 获取数据
    contract_data = fetch_contract_data(job_config.api_url)
    save_to_csv_with_headers(contract_data, job_config.temp_file, job_config.columns)

    # 2. 加载上下文
    existing_ids = collect_unique_contract_ids_from_file(job_config.performance_file)
    hk_awards = get_housekeeper_award_list(job_config.performance_file)

    # 3. 数据处理
    pipeline = DataProcessingPipeline(job_config.processing_config)
    processed_data = pipeline.process(contract_data, existing_ids, hk_awards)

    # 4. 保存结果
    write_performance_data(job_config.performance_file, processed_data, job_config.headers)

    # 5. 发送通知
    notifier = NotificationGenerator(job_config.config_key, job_config.city)
    send_notifications(processed_data, job_config.status_file, notifier)

    # 6. 归档
    archive_file(job_config.temp_file)
```

#### 1.5 SQLite优势验证
**创建验证脚本**: `scripts/sqlite_benefits_demo.py`

```python
def demonstrate_sqlite_benefits():
    """演示SQLite相比CSV的优势"""

    # 1. 去重查询对比
    print("=== 去重查询对比 ===")

    # CSV方式（当前）
    start_time = time.time()
    existing_ids = collect_unique_contract_ids_from_file("performance_data.csv")  # 读取整个文件
    csv_time = time.time() - start_time
    print(f"CSV去重查询: {csv_time:.3f}秒")

    # SQLite方式
    start_time = time.time()
    exists = sqlite_store.contract_exists("contract_123", "BJ-SEP")  # 索引查询
    sqlite_time = time.time() - start_time
    print(f"SQLite去重查询: {sqlite_time:.3f}秒 (提升 {csv_time/sqlite_time:.1f}倍)")

    # 2. 累计统计对比
    print("\n=== 累计统计对比 ===")

    # CSV方式（当前）- 需要读取整个文件并在内存中计算
    start_time = time.time()
    hk_stats = calculate_housekeeper_stats_from_csv("张三", "BJ-SEP")
    csv_time = time.time() - start_time
    print(f"CSV累计统计: {csv_time:.3f}秒")

    # SQLite方式 - 数据库聚合查询
    start_time = time.time()
    hk_stats = sqlite_store.get_housekeeper_stats("张三", "BJ-SEP")
    sqlite_time = time.time() - start_time
    print(f"SQLite累计统计: {sqlite_time:.3f}秒 (提升 {csv_time/sqlite_time:.1f}倍)")

    # 3. 代码复杂度对比
    print("\n=== 代码复杂度对比 ===")
    print("CSV方式: 需要维护复杂的housekeeper_contracts字典 (50+行代码)")
    print("SQLite方式: 一条SQL查询搞定 (1行代码)")
```

### SQLite集成的具体收益

#### 1. 代码行数大幅减少
- **当前**: 每个处理函数50+行的housekeeper_contracts维护逻辑
- **SQLite后**: 1条SQL查询替代所有累计计算

#### 2. 性能显著提升
- **去重查询**: 从O(n)的CSV扫描变为O(1)的索引查询
- **累计统计**: 从内存循环计算变为数据库聚合查询
- **双轨统计**: 复杂的分类计数变为简单的GROUP BY

#### 3. 数据一致性保障
- **事务支持**: 避免CSV读写的竞争条件
- **原子操作**: 要么全部成功要么全部失败
- **并发安全**: 支持多进程同时访问

#### 4. 扩展性大幅提升
- **复杂查询**: 支持历史数据分析、报表生成
- **索引优化**: 可针对查询模式优化性能
- **数据备份**: 标准的数据库备份恢复机制

### 验收标准
- [ ] **存储抽象层完成**
  - [ ] SQLite和CSV两种实现
  - [ ] 统一的接口设计
  - [ ] 配置驱动的存储选择
- [ ] **数据库Schema设计**
  - [ ] 支持所有城市/月份的统一表结构
  - [ ] 索引优化查询性能
  - [ ] 扩展字段支持特殊需求
- [ ] **处理管道重构**
  - [ ] 消除复杂的内存状态维护
  - [ ] 数据库驱动的累计计算
  - [ ] 配置驱动的差异处理
- [ ] **性能验证**
  - [ ] SQLite查询性能优于CSV
  - [ ] 内存使用大幅降低
  - [ ] 代码复杂度显著简化
- [ ] **向后兼容**
  - [ ] 保留CSV支持用于测试
  - [ ] 渐进迁移策略
  - [ ] 快速回滚机制

## 阶段2：北京迁移（验证新骨架）

### 目标
将北京6月/8月/9月的所有逻辑迁移到新骨架，验证新架构的可行性和等价性。

### 迁移策略
采用**逐个月份迁移**的方式，每次迁移一个月份并完成验证后再进行下一个。

### 具体任务

#### 2.1 北京6月迁移（最简单，作为验证基准）
**配置准备**:
```python
# 在新骨架中定义北京6月配置
BJ_JUN_CONFIG = ProcessingConfig(
    config_key="BJ-2025-06",
    activity_code="BJ-JUN",
    city="BJ",
    housekeeper_key_format="管家",
    enable_dual_track=False,
    enable_historical_contracts=False
)
```

**迁移步骤**:
1. 使用新的`DataProcessingPipeline`处理北京6月数据
2. 对比新旧版本的输出结果
3. 验证通知消息格式一致性
4. 性能基准测试

#### 2.2 北京8月迁移（验证配置复用）
**关键验证点**: 8月复用6月配置的逻辑是否正确
```python
BJ_AUG_CONFIG = ProcessingConfig(
    config_key="BJ-2025-06",  # 复用6月配置
    activity_code="BJ-AUG",   # 但活动编号不同
    city="BJ",
    housekeeper_key_format="管家"
)
```

**验证重点**:
- 配置复用是否导致数据错误
- 活动编号是否正确写入
- 奖励计算是否与原实现一致

#### 2.3 北京9月迁移（最复杂，验证特殊处理）
**复杂性处理**:
1. **历史合同支持**: 在新骨架中实现历史合同处理逻辑
2. **配置差异**: 5万上限、个人顺序幸运数字、禁用徽章
3. **双重逻辑**: 支持有/无历史合同字段的两种数据格式

```python
BJ_SEP_CONFIG = ProcessingConfig(
    config_key="BJ-2025-09",
    activity_code="BJ-SEP",
    city="BJ",
    housekeeper_key_format="管家",
    enable_historical_contracts=True  # 特殊标记
)
```

**关键改进**: 消除全局副作用
- 不再修改`globals()`
- 不再临时改写`config.PERFORMANCE_AMOUNT_CAP_BJ_FEB`
- 所有配置从`REWARD_CONFIGS["BJ-2025-09"]`读取

#### 2.4 北京Job函数统一
**目标**: 将3个北京Job函数合并为1个通用函数
```python
def signing_and_sales_incentive_beijing(month: str):
    """统一的北京激励Job函数"""
    config_map = {
        "jun": BJ_JUN_CONFIG,
        "aug": BJ_AUG_CONFIG,
        "sep": BJ_SEP_CONFIG
    }

    job_config = JobConfig(
        processing_config=config_map[month],
        api_url=get_api_url("BJ", month),
        performance_file=get_performance_file("BJ", month),
        # ... 其他配置
    )

    return execute_incentive_job(job_config)
```

### 验收标准
- [ ] **北京6月迁移完成**
  - [ ] 数据输出100%等价
  - [ ] 通知消息100%等价
  - [ ] 性能不降级
- [ ] **北京8月迁移完成**
  - [ ] 配置复用逻辑正确
  - [ ] 活动编号正确
  - [ ] 等价性验证通过
- [ ] **北京9月迁移完成**
  - [ ] 历史合同处理正确
  - [ ] 消除全局副作用
  - [ ] 双重逻辑支持
  - [ ] 等价性验证通过
- [ ] **Job函数统一**
  - [ ] 3个Job函数合并为1个
  - [ ] 代码行数减少60%+
  - [ ] 所有北京测试通过
- [ ] **旧代码清理**
  - [ ] 删除`process_data_jun_beijing`
  - [ ] 删除`process_data_sep_beijing`
  - [ ] 删除全局副作用代码

## 阶段3：上海迁移（处理复杂差异）

### 目标
将上海4月/8月/9月迁移到新骨架，重点处理双轨统计和housekeeper_key差异。

### 迁移挑战
1. **housekeeper_key差异**: 上海使用"管家_服务商"，北京使用"管家"
2. **双轨统计**: 上海9月的平台单/自引单分类统计
3. **字段差异**: 上海有8个额外的统计字段
4. **通知模板差异**: 转化率显示、双轨信息展示

### 具体任务

#### 3.1 上海4月迁移（基准验证）
**配置设计**:
```python
SH_APR_CONFIG = ProcessingConfig(
    config_key="SH-2025-04",
    activity_code="SH-APR",
    city="SH",
    housekeeper_key_format="管家_服务商",  # 关键差异
    enable_dual_track=False
)
```

**关键验证**:
- housekeeper_key格式是否正确处理
- 转化率字段是否正确计算
- 通知消息模板是否匹配

#### 3.2 上海8月迁移（复用验证）
**配置复用**:
```python
SH_AUG_CONFIG = ProcessingConfig(
    config_key="SH-2025-04",  # 复用4月配置
    activity_code="SH-AUG",   # 但活动编号不同
    city="SH",
    housekeeper_key_format="管家_服务商"
)
```

#### 3.3 上海9月迁移（双轨统计）
**最复杂的迁移**: 需要处理双轨统计逻辑

**扩展数据模型**:
```python
@dataclass
class ShanghaiHousekeeperStats(HousekeeperStats):
    """上海9月扩展的管家统计"""
    platform_count: int = 0
    platform_amount: float = 0.0
    self_referral_count: int = 0
    self_referral_amount: float = 0.0
    self_referral_projects: set = field(default_factory=set)
    self_referral_rewards: int = 0
```

**双轨处理逻辑**:
```python
class ShanghaiDualTrackProcessor:
    """上海双轨统计处理器"""

    def process_contract(self, contract, housekeeper_stats):
        source_type = contract.get('款项来源类型(tradeIn)', 0)

        if source_type == 1:  # 自引单
            self._process_self_referral(contract, housekeeper_stats)
        else:  # 平台单
            self._process_platform_order(contract, housekeeper_stats)
```

**字段扩展**:
```python
class ShanghaiRecordBuilder(RecordBuilder):
    """上海记录构建器，支持双轨字段"""

    def build(self, contract, housekeeper_stats, rewards):
        base_record = super().build(contract, housekeeper_stats, rewards)

        if self.config.enable_dual_track:
            # 添加8个双轨统计字段
            base_record.update({
                '工单类型': '自引单' if contract.get('款项来源类型(tradeIn)') == 1 else '平台单',
                '平台单累计数量': housekeeper_stats.platform_count,
                '平台单累计金额': housekeeper_stats.platform_amount,
                # ... 其他6个字段
            })

        return base_record
```

#### 3.4 上海通知统一
**合并三套通知逻辑**:
1. `notify_awards_shanghai_generate_message_march` (旧版)
2. `notify_awards_shanghai_generic` (新版)
3. 8月复用的逻辑

**统一为**:
```python
class ShanghaiNotificationGenerator(NotificationGenerator):
    """上海通知生成器"""

    def generate_group_message(self, record):
        template = self._get_shanghai_template()
        data = self._prepare_shanghai_data(record)

        # 处理双轨统计显示
        if self._has_dual_track_fields(record):
            data.update(self._prepare_dual_track_data(record))

        return template.format(**data)
```

### 验收标准
- [ ] **上海4月迁移完成**
  - [ ] housekeeper_key格式正确
  - [ ] 转化率计算正确
  - [ ] 通知消息等价
- [ ] **上海8月迁移完成**
  - [ ] 配置复用正确
  - [ ] 等价性验证通过
- [ ] **上海9月迁移完成**
  - [ ] 双轨统计逻辑正确
  - [ ] 8个扩展字段正确
  - [ ] 自引单奖励计算正确
  - [ ] 通知消息包含双轨信息
- [ ] **通知逻辑统一**
  - [ ] 三套通知逻辑合并为一套
  - [ ] 消息格式100%等价
- [ ] **全量验证通过**
  - [ ] 所有上海测试通过
  - [ ] 端到端集成测试通过

## 阶段4：清理优化（完善收尾）

### 目标
删除所有旧代码，优化Job函数，完善文档和测试。

### 具体任务

#### 4.1 旧代码清理
**删除文件/函数**:
- `process_data_jun_beijing`
- `process_data_shanghai_apr`
- `process_data_shanghai_sep`
- `process_data_sep_beijing_with_historical_support`
- 所有全局副作用相关代码

#### 4.2 Job函数优化
**统一所有Job函数**:
```python
def execute_monthly_incentive(city: str, month: str):
    """统一的月度激励执行函数"""
    config = get_monthly_config(city, month)
    return execute_incentive_job(config)

# 替换所有具体的Job函数
signing_and_sales_incentive_jun_beijing = lambda: execute_monthly_incentive("BJ", "jun")
signing_and_sales_incentive_sep_shanghai = lambda: execute_monthly_incentive("SH", "sep")
```

#### 4.3 配置系统清理
**删除旧配置变量**:
- `PERFORMANCE_AMOUNT_CAP_BJ_FEB`
- `ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB`
- `SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB`

**统一到REWARD_CONFIGS**

#### 4.4 测试完善
- 新增新骨架的单元测试
- 更新集成测试
- 添加性能回归测试

### 验收标准
- [ ] **代码行数减少40%+**
- [ ] **函数数量减少50%+**
- [ ] **所有测试通过**
- [ ] **性能不降级**
- [ ] **文档更新完成**

## 实施计划

### 时间安排（基于SQLite集成策略）
- **阶段1 - 建立新骨架+SQLite**: 3-4个工作日 (包含数据库设计和存储抽象层)
- **阶段2 - 北京迁移**: 2-3个工作日 (验证SQLite优势，逐个月份迁移)
- **阶段3 - 上海迁移**: 3-4个工作日 (SQLite简化双轨统计复杂性)
- **阶段4 - 清理优化**: 1-2个工作日 (删除旧代码，性能优化)
- **影子模式运行**: 1周 (SQLite与CSV并行，验证等价性和性能)
- **灰度发布**: 1周 (部分活动使用SQLite)
- **全量上线**: 1周 (全部切换到SQLite，监控稳定性)
- **总计**: 4-5周

### 风险控制
1. **每个Sprint独立可回滚**
2. **保持现有测试通过**
3. **强制等价性验证**: 每个Sprint必须通过100%等价性验证
4. **分支开发，主干稳定**
5. **影子模式**: 新版本先并行运行，不影响生产
6. **快速回滚机制**: 发现问题30秒内回滚

### 测试策略
1. **单元测试**: 新增模块的单元测试，覆盖率≥90%
2. **集成测试**: 现有集成测试必须通过
3. **等价性测试**: 数据输出、通知消息、业务逻辑三维度验证
4. **性能测试**: 确保重构后性能不降低
5. **边界测试**: 异常数据、边界条件全覆盖
6. **压力测试**: 验证系统在高负载下的稳定性

## 预期收益（包含SQLite优势）

### 代码质量大幅提升
- **消除全局副作用**: 提高代码可预测性和测试稳定性
- **代码行数减少60%+**: SQLite消除复杂的累计计算逻辑
  - 当前: 每个处理函数50+行的housekeeper_contracts维护
  - SQLite后: 1条SQL查询替代所有累计计算
- **减少代码重复**: 通知逻辑从3套合并为1套
- **提高可维护性**: 模块职责清晰，依赖关系明确

### 性能显著提升
- **查询性能**:
  - 去重查询: 从O(n)的CSV扫描变为O(1)的索引查询
  - 累计统计: 从内存循环计算变为数据库聚合查询
  - 双轨统计: 复杂的分类计数变为简单的GROUP BY
- **内存使用**: 不再需要将整个CSV加载到内存
- **并发性能**: 数据库锁机制优于文件锁

### 开发效率大幅提升
- **新增城市/活动**: 复用统一骨架，开发效率提高70%+
- **复杂查询**: 数据库天然支持复杂的历史数据分析
- **问题定位**: 模块化设计+数据库日志，问题定位更快速
- **测试效率**: 内存SQLite支持快速测试

### 系统稳定性和扩展性提升
- **数据一致性**: 事务保证，避免CSV读写竞争条件
- **并发安全**: 数据库锁机制，支持多进程访问
- **配置驱动**: 所有差异通过配置控制
- **扩展性**: 便于实现复杂查询、报表生成、数据分析
- **备份恢复**: 标准的数据库备份恢复机制

## 功能等价性验证与安全上线保障

### 等价性验证策略

#### 1. 数据输出等价性验证
**验证目标**: 确保重构后的输出数据与原实现完全一致

**验证方法**:
```python
# 创建等价性验证工具
def verify_data_equivalence(old_csv, new_csv, tolerance=0.01):
    """
    验证两个CSV文件的数据等价性

    Args:
        old_csv: 原实现输出的CSV文件
        new_csv: 重构后输出的CSV文件
        tolerance: 浮点数比较容差

    Returns:
        dict: 验证结果报告
    """
    report = {
        'is_equivalent': True,
        'differences': [],
        'summary': {}
    }

    # 1. 记录数量验证
    old_data = pd.read_csv(old_csv)
    new_data = pd.read_csv(new_csv)

    if len(old_data) != len(new_data):
        report['is_equivalent'] = False
        report['differences'].append(f"记录数量不一致: {len(old_data)} vs {len(new_data)}")

    # 2. 关键字段逐行比较
    key_fields = [
        '合同ID(_id)', '管家(serviceHousekeeper)', '合同金额(adjustRefundMoney)',
        '管家累计单数', '管家累计金额', '计入业绩金额',
        '激活奖励状态', '奖励类型', '奖励名称', '备注'
    ]

    for idx, (old_row, new_row) in enumerate(zip(old_data.iterrows(), new_data.iterrows())):
        for field in key_fields:
            if field in old_row[1] and field in new_row[1]:
                old_val = old_row[1][field]
                new_val = new_row[1][field]

                # 数值字段使用容差比较
                if field in ['管家累计金额', '计入业绩金额', '合同金额(adjustRefundMoney)']:
                    if abs(float(old_val) - float(new_val)) > tolerance:
                        report['is_equivalent'] = False
                        report['differences'].append(
                            f"行{idx+1} {field}: {old_val} vs {new_val}"
                        )
                # 字符串字段精确比较
                else:
                    if str(old_val).strip() != str(new_val).strip():
                        report['is_equivalent'] = False
                        report['differences'].append(
                            f"行{idx+1} {field}: '{old_val}' vs '{new_val}'"
                        )

    return report
```

**验证数据集**:
- **历史真实数据**: 使用最近3个月的生产数据作为验证基准
- **边界用例数据**: 构造包含各种边界情况的测试数据
- **异常数据**: 包含重复合同、异常金额等异常情况的数据

#### 2. 通知消息等价性验证
**验证目标**: 确保通知消息格式和内容完全一致

**验证方法**:
```python
def verify_notification_equivalence(old_messages, new_messages):
    """验证通知消息等价性"""
    # 1. 消息数量验证
    # 2. 消息内容逐条比较
    # 3. 特殊字符和格式验证
    # 4. 徽章和奖励翻倍逻辑验证
```

**验证覆盖**:
- 群通知消息格式
- 个人奖励消息格式
- 徽章显示逻辑
- 奖励翻倍计算
- 特殊字符处理

#### 3. 业务逻辑等价性验证
**验证目标**: 确保核心业务逻辑计算结果一致

**关键验证点**:
- **奖励计算逻辑**: 幸运数字、节节高、自引单奖励
- **累计统计逻辑**: 管家累计单数、累计金额、业绩金额
- **去重逻辑**: 已存在合同ID的处理
- **工单金额上限**: 北京特有的工单金额累计上限逻辑
- **双轨统计**: 上海9月的平台单/自引单分类统计

### 自动化验证框架

#### 1. 创建验证测试套件
**新建**: `tests/equivalence/`目录

**测试文件结构**:
```
tests/equivalence/
├── test_data_equivalence.py      # 数据输出等价性测试
├── test_notification_equivalence.py  # 通知消息等价性测试
├── test_business_logic_equivalence.py # 业务逻辑等价性测试
├── fixtures/                     # 测试数据
│   ├── beijing_test_data.csv
│   ├── shanghai_test_data.csv
│   └── edge_cases_data.csv
└── reports/                      # 验证报告输出目录
```

#### 2. 并行运行验证
**实施策略**: 在重构过程中，新旧版本并行运行

```python
def parallel_verification_test(test_data):
    """并行运行新旧版本，比较输出结果"""

    # 运行原版本
    old_result = run_old_version(test_data)

    # 运行新版本
    new_result = run_new_version(test_data)

    # 比较结果
    equivalence_report = verify_data_equivalence(
        old_result['csv_file'],
        new_result['csv_file']
    )

    # 生成验证报告
    generate_verification_report(equivalence_report)

    return equivalence_report['is_equivalent']
```

#### 3. 持续集成验证
**集成到CI/CD流程**:
```yaml
# .github/workflows/equivalence-verification.yml
name: Equivalence Verification

on:
  pull_request:
    paths:
      - 'modules/processing/**'
      - 'modules/rewards.py'
      - 'modules/notification_module.py'

jobs:
  verify-equivalence:
    runs-on: ubuntu-latest
    steps:
      - name: Run Equivalence Tests
        run: |
          python -m pytest tests/equivalence/ -v --tb=short

      - name: Generate Verification Report
        run: |
          python scripts/generate_equivalence_report.py

      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: equivalence-report
          path: tests/equivalence/reports/
```

### 安全上线标准

#### 1. 技术验收标准
**必须满足的条件**:

- [ ] **所有现有测试通过**: 100%的现有测试用例通过
- [ ] **等价性验证通过**: 数据输出、通知消息、业务逻辑三个维度100%等价
- [ ] **性能不降级**: 处理时间不超过原版本的110%
- [ ] **内存使用稳定**: 内存使用不超过原版本的120%
- [ ] **无新增异常**: 重构后不引入新的异常或错误

#### 2. 业务验收标准
**业务关键指标**:

- [ ] **奖励计算准确性**: 随机抽取100个合同，人工验证奖励计算结果
- [ ] **通知发送完整性**: 验证所有应发送的通知都正确发送
- [ ] **数据完整性**: 验证所有合同数据都正确处理，无遗漏
- [ ] **历史数据兼容性**: 能正确处理历史奖励数据，不影响累计统计

#### 3. 分阶段上线策略
**阶段1: 影子模式运行** (1周)
- 新版本与旧版本并行运行
- 新版本仅输出结果，不实际发送通知
- 每日对比验证结果，确保100%等价

**阶段2: 灰度发布** (1周)
- 选择1-2个低风险活动使用新版本
- 密切监控处理结果和通知发送
- 出现问题立即回滚到旧版本

**阶段3: 全量上线** (1周)
- 所有活动切换到新版本
- 保留旧版本代码作为应急备份
- 持续监控系统稳定性

#### 4. 回滚机制
**快速回滚条件**:
- 数据处理异常率 > 1%
- 通知发送失败率 > 5%
- 系统响应时间 > 原版本150%
- 发现任何数据不一致问题

**回滚操作**:
```bash
# 一键回滚脚本
#!/bin/bash
echo "开始回滚到旧版本..."

# 1. 切换代码分支
git checkout stable-maintenance-backup

# 2. 重启服务
python main.py restart

# 3. 验证服务状态
python scripts/health_check.py

echo "回滚完成，请验证系统状态"
```

#### 5. 监控告警机制
**关键监控指标**:
- 数据处理成功率
- 通知发送成功率
- 系统响应时间
- 内存使用情况
- 异常错误数量

**告警规则**:
```python
# 监控告警配置
MONITORING_RULES = {
    'data_processing_success_rate': {
        'threshold': 0.99,
        'alert_level': 'critical'
    },
    'notification_success_rate': {
        'threshold': 0.95,
        'alert_level': 'warning'
    },
    'response_time_ms': {
        'threshold': 5000,
        'alert_level': 'warning'
    }
}
```

### 验证工具和脚本

#### 1. 等价性验证脚本
**新建**: `scripts/verify_equivalence.py`
```python
#!/usr/bin/env python3
"""
重构等价性验证脚本
用法: python scripts/verify_equivalence.py --test-data data/test_contracts.csv
"""

def main():
    # 1. 加载测试数据
    # 2. 运行新旧版本
    # 3. 比较输出结果
    # 4. 生成验证报告
    pass

if __name__ == "__main__":
    main()
```

#### 2. 性能基准测试
**新建**: `scripts/performance_benchmark.py`
```python
#!/usr/bin/env python3
"""
性能基准测试脚本
比较重构前后的性能指标
"""

def benchmark_performance():
    # 1. 测试数据处理性能
    # 2. 测试内存使用情况
    # 3. 测试并发处理能力
    # 4. 生成性能报告
    pass
```

#### 3. 健康检查脚本
**新建**: `scripts/health_check.py`
```python
#!/usr/bin/env python3
"""
系统健康检查脚本
验证重构后系统各项功能正常
"""

def health_check():
    # 1. 检查配置文件完整性
    # 2. 检查数据库连接
    # 3. 检查API接口可用性
    # 4. 检查文件读写权限
    pass
```

### 质量保证流程

#### 1. 代码审查检查清单
- [ ] 是否消除了所有全局副作用
- [ ] 是否正确使用了配置驱动的设计
- [ ] 是否保持了向后兼容性
- [ ] 是否有充分的错误处理
- [ ] 是否有完整的日志记录

#### 2. 测试覆盖要求
- **单元测试覆盖率**: ≥ 90%
- **集成测试覆盖率**: ≥ 80%
- **等价性测试覆盖率**: 100%
- **边界用例覆盖**: 包含所有已知边界情况

#### 3. 文档更新要求
- [ ] 更新API文档
- [ ] 更新配置说明
- [ ] 更新部署文档
- [ ] 更新故障排查指南

## 后续优化方向

重构完成后，可考虑以下优化:
1. **引入SQLite**: 替代CSV存储，提升查询效率
2. **配置中心化**: 将消息模板迁移到配置文件
3. **监控告警**: 增加处理过程的监控和告警
4. **性能优化**: 批量处理、缓存机制等

---

**文档版本**: v1.1
**创建日期**: 2025-01-08
**更新日期**: 2025-01-08
**负责人**: Augment Agent
**审核状态**: 待审核
