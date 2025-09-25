# 验证工具集

本目录包含用于验证新旧架构等价性的专业工具集。这些工具确保架构迁移的正确性和可靠性。

## 工具概览

### 1. `clean_test_data.py` - 测试数据清理工具
专业级的测试环境清理工具，确保每次测试都从干净的初始状态开始。

**功能特性：**
- 清理新架构数据（performance_data.db）
- 清理旧架构数据（state目录文件、tasks.db）
- 支持按城市/活动精确清理
- 保留数据库结构，只清理数据
- 灵活的清理选项（全部/数据库/文件）

**使用方法：**
```bash
# 清理所有测试数据
python scripts/clean_test_data.py --all

# 清理特定城市和活动的数据
python scripts/clean_test_data.py --city SH --activity SH-SEP

# 只清理数据库
python scripts/clean_test_data.py --databases-only

# 只清理文件
python scripts/clean_test_data.py --files-only
```

### 2. `simple_validation.py` - 核心架构验证工具
专注于验证新旧架构的核心功能等价性，通过直接调用架构函数进行对比。

**功能特性：**
- 自动清理测试环境
- 分离新旧架构数据（备份恢复机制）
- 对比任务生成数量
- 对比业绩记录数量
- 详细的差异分析报告

**使用方法：**
```bash
# 验证上海架构
python scripts/simple_validation.py --city SH

# 验证北京架构
python scripts/simple_validation.py --city BJ

# 使用现有数据验证（不清理）
python scripts/simple_validation.py --city SH --no-clean
```

### 3. `simple_message_validation.py` - 消息验证工具
专门验证新旧架构生成的Task消息内容是否完全等价。

**功能特性：**
- 验证消息模板一致性
- 验证动态数据填充正确性
- 对比消息内容差异
- 验证通知逻辑等价性

**使用方法：**
```bash
# 验证上海9月活动的消息生成
python scripts/simple_message_validation.py --city SH --activity SH-SEP

# 验证北京9月活动的消息生成
python scripts/simple_message_validation.py --city BJ --activity BJ-SEP

# 使用现有数据验证
python scripts/simple_message_validation.py --city SH --activity SH-SEP --no-clean
```

## 验证流程

推荐的完整验证流程：

1. **清理环境**：使用 `clean_test_data.py` 确保干净的测试环境
2. **核心验证**：使用 `simple_validation.py` 验证架构核心功能
3. **消息验证**：使用 `simple_message_validation.py` 验证消息生成

```bash
# 完整验证流程示例
python scripts/clean_test_data.py --city SH --activity SH-SEP
python scripts/simple_validation.py --city SH
python scripts/simple_message_validation.py --city SH --activity SH-SEP
```

## 设计原则

1. **非侵入性**：不修改现有架构代码，只调用现有函数
2. **数据分离**：通过备份恢复机制完美分离新旧架构数据
3. **专业化**：每个工具专注于特定的验证任务
4. **自动化**：支持CI/CD集成，可自动化执行
5. **用户友好**：清晰的命令行接口和详细的执行反馈

## 依赖要求

- Python 3.7+
- SQLite3
- 项目的现有模块和配置

## 版本信息

- 版本：v1.0
- 创建日期：2025-09-25
- 作者：Sales Reward Hub Team

## 注意事项

- 这些工具会操作数据库和文件，请在测试环境中使用
- 建议在执行前备份重要数据
- 工具设计为幂等操作，可以安全地重复执行
