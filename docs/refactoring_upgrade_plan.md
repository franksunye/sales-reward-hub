# 代码重构升级方案

## 概述

本文档详细描述了对当前签约激励系统的重构升级方案。当前系统经过大量迭代后，代码结构复杂，存在全局副作用、通知逻辑重复、配置散乱等问题。本方案采用渐进式重构策略，分三个Sprint完成，确保每步可回滚、可测试。

## 当前问题分析

### 1. 全局副作用问题
**位置**: `modules/data_processing_module.py:892-914`

**问题**: 北京9月数据处理通过动态替换全局函数和修改全局配置实现
```python
# 问题代码示例
globals()['determine_rewards_jun_beijing_generic'] = determine_rewards_sep_beijing_generic
config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000
try:
    result = process_data_jun_beijing(...)
finally:
    # 恢复原有配置
    globals()['determine_rewards_jun_beijing_generic'] = original_determine_rewards
    config.PERFORMANCE_AMOUNT_CAP_BJ_FEB = original_performance_cap
```

**风险**: 
- 全局副作用导致竞争条件
- 代码可读性差，难以理解和维护
- 与测试框架耦合，影响测试稳定性

### 2. 数据结构不统一
**问题**: 不同城市/月份维护不同的管家统计结构
- 北京: `housekeeper_key = "管家"`
- 上海: `housekeeper_key = "管家_服务商"`
- 上海9月: 额外增加双轨字段 `platform_*` 和 `self_referral_*`

**影响**: 虽然奖励计算已通用化，但数据层面难以复用

### 3. 通知逻辑重复
**问题**: 存在三套通知逻辑
- `notify_awards_beijing_generic()` (118-177行)
- `notify_awards_shanghai_generate_message_march()` (197-245行) 
- `notify_awards_shanghai_generic()` (288-352行)

**影响**: 代码重复，维护成本高，容易出现不一致

### 4. 任务编排耦合
**问题**: `jobs.py` 使用通配符导入，数据处理与通知耦合紧密
```python
from modules.* import *  # 可读性差，依赖不明确
```

## 重构目标

1. **消除全局副作用**: 所有配置通过参数传递，不修改全局状态
2. **统一数据结构**: 建立标准的管家统计数据结构
3. **合并通知逻辑**: 一套通用通知器，支持城市差异化配置
4. **解耦任务编排**: 明确模块依赖，简化任务流程
5. **保持向后兼容**: 确保现有测试通过，行为完全一致

## 重构策略

采用**渐进式重构**策略，分三个Sprint执行：
1. **Sprint 1**: 北京链路清晰化，去除全局副作用
2. **Sprint 2**: 通知统一，模板化最小化  
3. **Sprint 3**: 上海链路对齐，统一记录构建器

每个Sprint都保证：
- 测试可通过
- 行为等价
- 可独立回滚

## Sprint 1: 北京链路清晰化

### 目标
将北京6月/9月的数据处理统一为一个函数，完全从`REWARD_CONFIGS`读取配置，消除全局副作用。

### 具体任务

#### 1.1 创建奖励计算模块
**新建**: `modules/rewards.py`

**内容**: 从`data_processing_module.py`迁移以下函数
- `determine_lucky_number_reward_generic()`
- `determine_rewards_generic()`  
- `should_enable_badge()`
- `get_self_referral_config()`
- `determine_self_referral_rewards()`

**目的**: 将奖励算法与数据处理流程解耦

#### 1.2 创建北京数据处理模块
**新建**: `modules/processing/beijing.py`

**核心函数**: 
```python
def process_data_beijing(contract_data, existing_ids, hk_awards, config_key, activity_code):
    """
    北京数据处理统一入口
    
    Args:
        contract_data: 合同数据列表
        existing_ids: 已存在的合同ID集合
        hk_awards: 管家历史奖励列表
        config_key: 配置键 (如 "BJ-2025-06", "BJ-2025-09")
        activity_code: 活动编号 (如 "BJ-JUN", "BJ-SEP")
    
    Returns:
        list: 处理后的业绩数据列表
    """
    # 从REWARD_CONFIGS读取配置，不使用全局变量
    limits = config.REWARD_CONFIGS[config_key]["performance_limits"]
    cap = limits.get("single_contract_cap", 999999)
    
    # 统一housekeeper_key为"管家(serviceHousekeeper)"
    # 直接写入activity_code，不后续修改
    # 调用rewards.determine_rewards_generic()计算奖励
    
    return performance_data
```

#### 1.3 修改Jobs调用
**修改**: `jobs.py`中的北京相关函数

**变更前**:
```python
def signing_and_sales_incentive_sep_beijing():
    # 使用包装函数，存在全局副作用
    processed_data = process_data_sep_beijing(...)
```

**变更后**:
```python
def signing_and_sales_incentive_sep_beijing():
    # 直接调用统一函数，传递配置参数
    processed_data = process_data_beijing(
        contract_data, existing_ids, hk_awards, 
        config_key="BJ-2025-09", 
        activity_code="BJ-SEP"
    )
```

#### 1.4 删除问题代码
**删除**: `modules/data_processing_module.py:892-914`的全局改写逻辑

### 验收标准
- [ ] 删除全局副作用代码
- [ ] 北京相关测试全部通过
  - `tests/test_beijing_sep_features.py`
  - `tests/test_beijing_sep_integration.py`
- [ ] 输出CSV与原实现完全一致

## Sprint 2: 通知统一

### 目标
创建一套通用通知入口，支持城市差异化配置，合并现有的三套通知逻辑。

### 具体任务

#### 2.1 创建通用通知函数
**新建**: `notify_awards_generic()`

**接口设计**:
```python
def notify_awards_generic(perf_csv, status_json, config_key, group_name, campaign_contact, city):
    """
    通用奖励通知函数
    
    Args:
        perf_csv: 业绩数据CSV文件路径
        status_json: 发送状态JSON文件路径  
        config_key: 配置键
        group_name: 企微群名称
        campaign_contact: 活动联系人
        city: 城市标识 ("BJ"/"SH")
    """
    records = get_all_records_from_csv(perf_csv)
    for record in records:
        if record['是否发送通知'] == 'N':
            # 生成群消息
            msg = build_group_message(record, config_key, city)
            create_task('send_wecom_message', group_name, msg)
            
            # 生成个人奖励消息
            if record['激活奖励状态'] == '1':
                award_msg = generate_award_message(record, get_awards_mapping(config_key), city, config_key)
                create_task('send_wechat_message', campaign_contact, award_msg)
            
            # 更新状态
            update_send_status(status_json, record['合同ID(_id)'], '发送成功')
            record['是否发送通知'] = 'Y'
    
    # 保存更新后的CSV
    update_performance_data(perf_csv, records, list(records[0].keys()))
```

#### 2.2 创建消息构建函数
**新建**: `build_group_message(record, config_key, city)`

**功能**: 根据城市和配置生成差异化的群消息模板
- 北京: 显示业绩金额信息
- 上海: 显示转化率信息  
- 上海9月: 额外显示双轨统计信息

#### 2.3 保留薄包装函数
保留现有的包装函数以维持向后兼容:
```python
def notify_awards_sep_beijing(perf_csv, status_json):
    return notify_awards_generic(
        perf_csv, status_json, "BJ-2025-09", 
        WECOM_GROUP_NAME_BJ, CAMPAIGN_CONTACT_BJ, "BJ"
    )

def notify_awards_sep_shanghai(perf_csv, status_json):
    return notify_awards_generic(
        perf_csv, status_json, "SH-2025-09",
        WECOM_GROUP_NAME_SH, CAMPAIGN_CONTACT_SH, "SH"
    )
```

#### 2.4 清理Jobs导入
**修改**: `jobs.py`
- 移除通配符导入 `from modules.* import *`
- 改为显式导入需要的函数

### 验收标准
- [ ] 合并三套通知逻辑为一套
- [ ] 上海通知相关测试通过
  - `tests/test_shanghai_sep_notification.py`
- [ ] 通知消息格式与原实现一致

## Sprint 3: 上海链路对齐

### 目标
将上海4月/9月切换到统一骨架，创建通用的记录构建器。

### 具体任务

#### 3.1 创建上海数据处理模块
**新建**: `modules/processing/shanghai.py`

**核心函数**:
```python
def process_data_shanghai(contract_data, existing_ids, hk_awards, config_key, activity_code, dual_track=False):
    """
    上海数据处理统一入口
    
    Args:
        dual_track: 是否启用双轨处理 (上海9月为True)
    """
    # dual_track=True时，维护platform/self_referral两套统计
    # dual_track=False时，使用标准统计逻辑
    # housekeeper_key使用"管家_服务商"格式
```

#### 3.2 创建记录构建器
**新建**: `modules/record_builder.py`

**功能**: 统一记录构建逻辑，支持扩展字段
```python
def build_performance_record_base(contract, hk_data, activity_code, ...):
    """构建基础业绩记录 (北京/上海通用字段)"""
    
def extend_shanghai_sep_fields(base_record, hk_data, ...):
    """扩展上海9月特有字段"""
```

#### 3.3 统一管家数据结构
定义标准的管家统计数据结构:
```python
# 必须字段 (rewards.determine_rewards_generic所需)
required_fields = ['count', 'total_amount', 'performance_amount', 'awarded']

# 扩展字段 (用于分类统计)
extended_fields = ['platform_count', 'platform_amount', 'self_referral_count', 'self_referral_amount']
```

### 验收标准
- [ ] 上海4月/9月使用统一处理骨架
- [ ] 所有上海相关测试通过
- [ ] 记录构建逻辑统一，代码复用度提高

## 实施计划

### 时间安排
- **Sprint 1**: 2-3个工作日
- **Sprint 2**: 2-3个工作日  
- **Sprint 3**: 3-4个工作日
- **总计**: 1-2周

### 风险控制
1. **每个Sprint独立可回滚**
2. **保持现有测试通过**
3. **行为完全等价验证**
4. **分支开发，主干稳定**

### 测试策略
1. **单元测试**: 新增模块的单元测试
2. **集成测试**: 现有集成测试必须通过
3. **回归测试**: 输出数据与原实现对比
4. **性能测试**: 确保重构后性能不降低

## 预期收益

### 代码质量提升
- **消除全局副作用**: 提高代码可预测性和测试稳定性
- **减少代码重复**: 通知逻辑从3套合并为1套
- **提高可维护性**: 模块职责清晰，依赖关系明确

### 开发效率提升  
- **新增城市/活动**: 复用统一骨架，开发效率提高50%+
- **问题定位**: 模块化设计，问题定位更快速
- **测试覆盖**: 统一接口，测试覆盖更全面

### 系统稳定性提升
- **并发安全**: 消除全局状态修改
- **配置驱动**: 所有差异通过配置控制
- **向后兼容**: 保持现有接口不变

## 后续优化方向

重构完成后，可考虑以下优化:
1. **引入SQLite**: 替代CSV存储，提升查询效率
2. **配置中心化**: 将消息模板迁移到配置文件
3. **监控告警**: 增加处理过程的监控和告警
4. **性能优化**: 批量处理、缓存机制等

---

**文档版本**: v1.0  
**创建日期**: 2025-01-08  
**负责人**: Augment Agent  
**审核状态**: 待审核
