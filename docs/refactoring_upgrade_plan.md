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
- [ ] **等价性验证通过**
  - [ ] 使用相同测试数据，新旧版本输出CSV 100%一致
  - [ ] 关键字段逐行比较：合同ID、管家、累计金额、奖励类型等
  - [ ] 通知消息格式和内容完全一致
  - [ ] 业务逻辑计算结果一致（奖励计算、累计统计等）
- [ ] **性能验证通过**
  - [ ] 处理时间不超过原版本110%
  - [ ] 内存使用不超过原版本120%

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
- [ ] **通知等价性验证通过**
  - [ ] 群通知消息格式100%一致
  - [ ] 个人奖励消息内容100%一致
  - [ ] 徽章显示逻辑正确
  - [ ] 特殊字符和emoji处理一致
- [ ] **并行验证通过**
  - [ ] 新旧版本并行运行1周，结果100%一致
  - [ ] 通知发送成功率≥99%

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
- [ ] **全量等价性验证通过**
  - [ ] 所有城市/活动的数据输出100%一致
  - [ ] 双轨统计逻辑验证通过（上海9月）
  - [ ] 自引单奖励计算验证通过
  - [ ] 历史数据兼容性验证通过
- [ ] **系统集成验证通过**
  - [ ] 端到端测试全部通过
  - [ ] 性能基准测试通过
  - [ ] 记录构建逻辑统一，代码复用度提高50%+

## 实施计划

### 时间安排
- **Sprint 1**: 3-4个工作日 (包含1天等价性验证)
- **Sprint 2**: 3-4个工作日 (包含1天并行验证)
- **Sprint 3**: 4-5个工作日 (包含2天全量验证)
- **影子模式运行**: 1周 (新旧版本并行，验证等价性)
- **灰度发布**: 1周 (部分活动试运行)
- **全量上线**: 1周 (全部切换，监控稳定性)
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
