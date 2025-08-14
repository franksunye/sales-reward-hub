# 敏感信息保护计划

## 文档信息
**文档类型**: 项目计划
**文档编号**: sensitive_information-PLAN-001
**版本**: 1.0.0
**创建日期**: 2025-04-29
**最后更新**: 2025-04-29
**状态**: 草稿
**负责人**: Frank
**团队成员**: Frank, 小智
**优先级**: 高
**预计工期**: 1个Sprint (2周)

**相关文档**:
- [敏感信息保护任务清单](./sensitive_information_03_TASK_protection.md) (sensitive_information-TASK-001) [计划中]

## 1. 项目概述

### 1.1 背景

当前项目是一个公开的GitHub仓库，但代码中包含多处敏感信息，如账号密码、API密钥、Webhook URLs等。这些信息直接硬编码在源代码中，存在安全风险。

### 1.2 目标

- 识别并移除代码中所有硬编码的敏感信息
- 实施安全的配置管理机制
- 确保代码功能在修改后保持不变
- 建立敏感信息管理的最佳实践

### 1.3 范围

- 审查并修改所有包含敏感信息的代码文件
- 实现环境变量配置系统
- 修改日志记录系统，避免记录敏感信息
- 改进会话管理机制，加密存储敏感信息
- 更新相关文档和配置指南

### 1.4 非范围

- 不包括对系统功能的扩展或改进
- 不包括对系统架构的重大变更
- 不包括对第三方服务的替换或升级

## 2. 已发现的敏感信息

### 2.1 账号凭据
- **Metabase账号密码** (`modules/config.py`):
  ```python
  METABASE_USERNAME = 'wangshuang@xlink.bj.cn'
  METABASE_PASSWORD = 'xlink123456'
  ```

### 2.2 API密钥和Webhook URLs
- **企业微信Webhook URLs** (`modules/config.py`):
  ```python
  WEBHOOK_URL_DEFAULT = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=689cebff-3328-4150-9741-fed8b8ce4713'
  WEBHOOK_URL_CONTACT_TIMEOUT = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=80ab1f45-2526-4b41-a639-c580ccde3e2f"
  ```

### 2.3 API端点
- **Metabase API端点** (`modules/config.py`):
  ```python
  METABASE_URL = 'http://metabase.fsgo365.cn:3000'
  API_URL_TS = "http://metabase.fsgo365.cn:3000/api/card/719/query"
  ```

### 2.4 个人信息
- **电话号码** (`modules/config.py`):
  ```python
  PHONE_NUMBER = '15327103039'
  ```

### 2.5 敏感日志
- **在日志中记录敏感信息** (`modules/request_module.py`):
  ```python
  logging.debug(f"Sending POST request to {METABASE_SESSION} with username: {METABASE_USERNAME} and password: {METABASE_PASSWORD}")
  ```

## 3. 实施计划

### 3.1 第一阶段: 准备工作 (第1-2天)
- [ ] **任务1.1**: 创建详细的敏感信息清单
  - 优先级: 高
  - 估计工时: 2小时
  - 描述: 全面审查代码，创建包含所有敏感信息的详细清单，包括位置和类型。

- [ ] **任务1.2**: 设计环境变量结构
  - 优先级: 高
  - 估计工时: 3小时
  - 描述: 设计合理的环境变量命名和组织结构，确保易于维护和使用。

- [ ] **任务1.3**: 创建`.env.example`文件模板
  - 优先级: 高
  - 估计工时: 1小时
  - 描述: 创建包含所有必要环境变量但不包含实际值的示例文件。

### 3.2 第二阶段: 配置系统修改 (第3-5天)
- [ ] **任务2.1**: 修改`modules/config.py`使用环境变量
  - 优先级: 高
  - 估计工时: 4小时
  - 描述: 将硬编码的敏感信息替换为环境变量引用。
  - 步骤:
    1. 导入必要的库: `import os` 和 `from dotenv import load_dotenv`
    2. 添加环境变量加载代码: `load_dotenv()`
    3. 替换所有硬编码的敏感信息

- [ ] **任务2.2**: 添加环境变量加载和验证机制
  - 优先级: 高
  - 估计工时: 3小时
  - 描述: 实现环境变量加载和验证，确保所有必需的环境变量都已设置。

- [ ] **任务2.3**: 更新`.gitignore`文件
  - 优先级: 高
  - 估计工时: 0.5小时
  - 描述: 更新`.gitignore`文件，确保敏感文件不会被提交到版本控制系统。

### 3.3 第三阶段: 日志系统修改 (第6-7天)
- [ ] **任务3.1**: 修改`modules/request_module.py`中的日志记录
  - 优先级: 高
  - 估计工时: 2小时
  - 描述: 修改日志记录代码，避免记录敏感信息。
  - 步骤:
    1. 识别所有记录敏感信息的日志语句
    2. 修改这些语句，移除或掩盖敏感信息
    3. 实现通用的日志脱敏函数(可选)

- [ ] **任务3.2**: 审查其他文件中可能的敏感信息日志
  - 优先级: 中
  - 估计工时: 3小时
  - 描述: 全面审查所有日志记录，确保没有敏感信息被记录。

### 3.4 第四阶段: 会话管理改进 (第8-9天)
- [ ] **任务4.1**: 实现会话信息加密存储
  - 优先级: 中
  - 估计工时: 4小时
  - 描述: 实现会话信息的加密存储功能。
  - 步骤:
    1. 创建加密工具函数
    2. 修改会话保存和加载代码，使用加密函数
    3. 将加密密钥存储在环境变量中

- [ ] **任务4.2**: 改进会话管理机制
  - 优先级: 中
  - 估计工时: 3小时
  - 描述: 改进会话管理，包括会话刷新和安全存储。

### 3.5 第五阶段: 测试与验证 (第10-12天)
- [ ] **任务5.1**: 编写单元测试
  - 优先级: 高
  - 估计工时: 6小时
  - 描述: 为修改的组件编写单元测试，确保功能正确。
  - 测试项目:
    - 环境变量加载测试
    - 配置访问测试
    - 日志记录测试
    - 会话管理测试

- [ ] **任务5.2**: 执行功能测试
  - 优先级: 高
  - 估计工时: 4小时
  - 描述: 执行功能测试，验证系统主要功能正常工作。
  - 测试项目:
    - Metabase连接测试
    - 数据获取测试
    - 通知发送测试

- [ ] **任务5.3**: 执行集成测试
  - 优先级: 高
  - 估计工时: 4小时
  - 描述: 执行集成测试，验证整个系统正常运行。
  - 测试项目:
    - 端到端流程测试
    - 错误处理测试

- [ ] **任务5.4**: 修复发现的问题
  - 优先级: 高
  - 估计工时: 6小时
  - 描述: 修复测试过程中发现的问题。

### 3.6 第六阶段: 文档与部署 (第13-14天)
- [ ] **任务6.1**: 更新配置指南文档
  - 优先级: 中
  - 估计工时: 2小时
  - 描述: 更新配置指南，包括环境变量设置说明。

- [ ] **任务6.2**: 创建环境设置指南
  - 优先级: 中
  - 估计工时: 2小时
  - 描述: 创建详细的环境设置指南，帮助开发人员正确设置环境。

- [ ] **任务6.3**: Sprint回顾与总结
  - 优先级: 中
  - 估计工时: 1小时
  - 描述: 进行Sprint回顾，总结经验和教训。

## 4. 测试与验证计划

### 4.1 测试目标

确保敏感信息保护实施后，系统的所有功能仍能正常工作，同时验证敏感信息已被正确保护。

### 4.2 测试范围

1. 环境变量配置和加载
2. 配置系统功能
3. API连接和数据获取
4. 日志记录和敏感信息保护
5. 会话管理和安全存储
6. 系统主要功能的端到端测试

### 4.3 关键测试用例

#### 环境变量测试
```python
def test_env_loading():
    from dotenv import load_dotenv
    import os

    # 加载环境变量
    load_dotenv()

    # 检查关键环境变量
    assert os.getenv('METABASE_USERNAME') is not None
    assert os.getenv('METABASE_PASSWORD') is not None
    assert os.getenv('WEBHOOK_URL_DEFAULT') is not None
```

#### 日志记录测试
```python
def test_log_no_sensitive_info():
    import logging
    import re
    from modules import request_module

    # 设置测试日志文件
    logging.basicConfig(filename='test.log', level=logging.DEBUG)

    # 执行包含日志的代码
    request_module.get_metabase_session()

    # 分析日志文件
    with open('test.log', 'r') as f:
        log_content = f.read()

    # 检查是否包含密码
    assert not re.search(r'password=\S+', log_content)
    assert not re.search(r'METABASE_PASSWORD', log_content)
```

#### Metabase连接测试
```python
def test_metabase_login():
    from modules.request_module import get_metabase_session

    # 获取会话ID
    session_id = get_metabase_session()

    # 验证会话ID
    assert session_id is not None
    assert isinstance(session_id, str)
    assert len(session_id) > 0
```

#### 端到端流程测试
```python
def test_beijing_apr_complete_flow():
    from jobs import signing_and_sales_incentive_apr_beijing
    import os
    import csv

    # 执行完整流程
    signing_and_sales_incentive_apr_beijing()

    # 验证数据文件
    performance_file = os.getenv('PERFORMANCE_DATA_FILENAME_BJ_APR')
    assert os.path.exists(performance_file)

    # 验证数据内容
    with open(performance_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = list(reader)
        assert len(data) > 0
```

## 5. 风险与缓解措施

### 5.1 已识别风险

1. **功能中断风险**:
   - **风险**: 修改配置系统可能导致现有功能中断
   - **缓解**: 全面的测试计划和回滚机制
2. **环境变量缺失风险**:
   - **风险**: 部署时可能忘记设置某些环境变量
   - **缓解**: 添加环境变量验证和默认值
3. **迁移复杂性风险**:
   - **风险**: 迁移过程可能比预期更复杂
   - **缓解**: 分阶段实施，先处理最关键的敏感信息

### 5.2 应急计划

1. 保留原始代码的备份
2. 准备回滚脚本
3. 设置监控和警报机制

## 6. 依赖关系

### 6.1 内部依赖

1. 需要对现有代码库有全面的了解
2. 需要了解所有使用敏感信息的模块和功能
3. 依赖于现有的日志系统和配置系统

### 6.2 外部依赖

1. Python-dotenv库用于环境变量管理
2. Cryptography库用于会话信息加密
3. 依赖于Metabase API和企业微信API的稳定性

## 7. 资源需求

1. **人力资源**:
   - 1名开发人员负责代码修改和测试
   - 1名审核人员负责代码审查和验证

2. **技术资源**:
   - 开发环境
   - 测试环境
   - 版本控制系统

3. **时间资源**:
   - 总计2周时间
   - 每个阶段1-3天

## 8. 交付物

1. 更新的源代码，移除所有硬编码敏感信息
2. `.env.example`文件模板
3. 更新的文档，包括配置指南和环境设置指南
4. 测试报告和验证结果

## 9. 验收标准

1. 所有硬编码的敏感信息都已从代码中移除
2. 系统功能在修改后保持不变
3. 所有测试都通过
4. 文档已更新，包括新的配置方法

## 10. 项目时间线

| 阶段 | 开始日期 | 结束日期 | 工作内容 |
|------|----------|----------|----------|
| 准备工作 | [待定] | [待定] | 创建敏感信息清单，设计环境变量结构 |
| 配置系统修改 | [待定] | [待定] | 修改config.py，添加环境变量加载机制 |
| 日志系统修改 | [待定] | [待定] | 修改日志记录，避免记录敏感信息 |
| 会话管理改进 | [待定] | [待定] | 实现会话信息加密存储 |
| 测试与验证 | [待定] | [待定] | 编写和执行测试，修复问题 |
| 文档与部署 | [待定] | [待定] | 更新文档，准备部署 |

## 更新记录

| 版本 | 日期 | 更新者 | 更新内容 |
|------|------|--------|----------|
| 1.0.0 | 2025-04-29 | 小智 | 初始版本 |
