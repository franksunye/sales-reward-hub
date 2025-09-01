# 上海9月双轨激励测试文档

## 📁 测试文件结构

### 🎯 核心功能测试
- **`test_shanghai_sep_data_processing.py`** - 数据处理核心逻辑（完整字段验证）
  - **完整字段计算验证**：覆盖所有业绩数据计算字段
  - **首次计算场景**：从零开始的完整数据处理
  - **增量计算场景**：包含已存在合同的增量处理
  - **真实数据验证**：使用丁长勇真实合同数据测试
  - **累计计算逻辑**：管家累计单数/金额的正确计算
  - **分类统计验证**：平台单/自引单分类统计
  - **奖励计算验证**：基于累计数据的奖励计算
  - **字段映射验证**：新增字段的正确映射

### 🔧 专项功能测试
- **`test_shanghai_sep_self_referral.py`** - 自引单功能
  - 项目地址去重
  - 自引单奖励计算
  - 自引单统计

- **`test_shanghai_sep_notification.py`** - 通知功能
  - 消息生成
  - 通知状态更新
  - 群通知和个人通知

### 🔗 集成测试
- **`test_shanghai_sep_job_integration.py`** - 完整流程测试
  - API数据获取到通知发送的完整流程
  - 文件保存和归档
  - 错误处理

### 📋 测试套件
- **`test_shanghai_sep_suite.py`** - 测试套件管理
  - 统一运行所有测试
  - 核心测试快速验证（专注数据处理）
  - 测试结果汇总

## 🚀 运行测试

### 运行所有测试
```bash
python tests/test_shanghai_sep_suite.py
```

### 只运行核心测试（快速验证）
```bash
python tests/test_shanghai_sep_suite.py --core
```

### 运行单个测试文件
```bash
python -m pytest tests/test_cumulative_calculation.py -v
python -m pytest tests/test_shanghai_sep_data_processing.py -v
```

### 运行特定测试用例
```bash
python -m pytest tests/test_shanghai_sep_data_processing.py::TestShanghaiSepDataProcessing::test_complete_field_calculation_first_time -v
python -m pytest tests/test_shanghai_sep_data_processing.py::TestShanghaiSepDataProcessing::test_real_data_complete_field_validation -v
```

## 📊 测试覆盖范围

### ✅ 已覆盖功能
- [x] **完整字段计算验证** - 覆盖所有业绩数据计算字段
- [x] **首次计算和增量计算** - 两种关键业务场景
- [x] **累计计算逻辑** - 管家累计单数/金额正确性
- [x] **分类统计验证** - 平台单/自引单分类统计
- [x] **奖励计算验证** - 基于累计数据的奖励计算
- [x] **真实数据验证** - 使用丁长勇真实合同数据
- [x] **自引单功能** - 项目地址去重和奖励
- [x] **通知功能** - 消息生成和状态更新
- [x] **集成流程** - 完整的端到端测试

### 🎯 测试重点
1. **业绩数据字段完整性** - 确保所有计算字段正确
2. **累计计算准确性** - 首次计算和增量计算的正确性
3. **真实业务场景** - 使用实际业务数据验证
4. **边界情况处理** - 各种异常输入的处理

## 🔧 测试数据

### 真实业务数据
- 丁长勇：2个合同，累计14900元
- 刘嘉豪：2个合同，累计38000元
- 包含平台单和自引单场景

### 边界测试数据
- 空合同数据
- 所有合同已存在
- 没有已存在合同
- 混合管家数据

## 📝 测试最佳实践

### 1. TDD原则
- 先写测试，再写实现
- 测试驱动修复和重构

### 2. 测试命名
- 使用描述性的测试方法名
- 清楚表达测试意图

### 3. 测试独立性
- 每个测试用例独立运行
- 不依赖其他测试的状态

### 4. 断言明确
- 使用具体的断言消息
- 便于快速定位问题

## 🎯 持续改进

### 定期维护
- 清理过时的测试
- 更新测试数据
- 优化测试性能

### 扩展测试
- 添加新功能的测试
- 增加性能测试
- 添加压力测试
