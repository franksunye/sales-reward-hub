# 验证工具脚本说明

本目录包含用于验证新旧架构功能一致性的工具脚本。

## 📋 工具脚本概览

### 1. `clean_test_data.py` - 数据清理工具
**功能**: 清理测试环境中的所有数据，确保干净的测试环境

**支持的清理内容**:
- ✅ 新架构数据库 (`performance_data.db`)
- ✅ 旧架构任务数据库 (`tasks.db`)
- ✅ 旧架构状态文件 (`state/` 目录下的 CSV, JSON 文件)
- ✅ 新架构CSV输出文件
- ✅ 发送状态文件

**使用方法**:
```bash
# 清理指定城市和活动的数据
python scripts/clean_test_data.py --city SH --activity SH-SEP

# 清理所有数据
python scripts/clean_test_data.py --all

# 只清理新架构数据
python scripts/clean_test_data.py --new-only

# 只清理旧架构数据  
python scripts/clean_test_data.py --old-only
```

### 2. `simple_validation.py` - 基础验证工具
**功能**: 快速验证新旧架构生成的任务和记录数量是否一致

**验证内容**:
- ✅ 任务总数对比
- ✅ PerformanceData记录数对比
- ✅ 自动备份旧架构数据
- ✅ 集成数据清理功能

**使用方法**:
```bash
# 验证指定城市和活动
python scripts/simple_validation.py --city SH --activity SH-SEP

# 跳过数据清理，快速验证
python scripts/simple_validation.py --city SH --activity SH-SEP --skip-clean
```

**输出示例**:
```
🎯 验证目标: SH SH-SEP
📊 对比结果
========================================
🗃️ PerformanceData对比:
   旧架构记录数: 196
   新架构记录数: 196
   数量匹配: ✅
📨 Task消息对比:
   旧架构任务数: 261
   新架构任务数: 261
   数量匹配: ✅
🎯 总体结论: ✅ 新旧架构完全匹配
```

### 3. `simple_message_validation.py` - 详细消息验证工具
**功能**: 深入验证新旧架构生成的消息内容是否一致

**验证内容**:
- ✅ 任务数量和类型分布对比
- ✅ PerformanceData记录数对比
- ✅ **详细的消息内容比较**
- ✅ 抽样消息内容验证
- ✅ 消息标准化比较（去除动态内容）

**使用方法**:
```bash
# 详细验证指定城市和活动
python scripts/simple_message_validation.py --city SH --activity SH-SEP

# 跳过数据清理，快速验证
python scripts/simple_message_validation.py --city SH --activity SH-SEP --skip-clean
```

**输出示例**:
```
📨 Task消息对比:
   旧架构任务数: 261
   新架构任务数: 261
   数量匹配: ✅
   🔍 详细消息内容比较:
     send_wechat_message: 65 vs 65 ✅
     send_wecom_message: 196 vs 196 ✅
     ✅ 抽样消息内容匹配
```

## 🔧 增强功能

### `simple_message_validation.py` 的增强功能

1. **智能文件查找**: 自动查找多种可能的CSV文件名格式
2. **完整环境清理**: 清理发送状态文件，避免旧架构跳过已处理的合同
3. **详细消息比较**: 
   - 按任务类型分组比较
   - 抽样消息内容验证
   - 消息标准化处理（去除时间戳、合同ID、金额等动态内容）
4. **差异定位**: 精确定位消息内容的差异位置

### 消息标准化功能

为了准确比较消息内容，工具会自动标准化以下动态内容：
- 时间戳 → `[TIMESTAMP]`
- 合同ID → `[CONTRACT_ID]`  
- 具体金额 → `[AMOUNT]`
- 多余空白字符

## 🎯 使用建议

### 开发阶段
1. 使用 `clean_test_data.py` 清理环境
2. 使用 `simple_validation.py` 快速验证基本功能
3. 使用 `simple_message_validation.py` 详细验证消息内容

### 测试阶段
1. 使用 `simple_message_validation.py` 进行全面验证
2. 关注消息内容的差异，确保业务逻辑正确

### 生产部署前
1. 使用所有三个工具进行完整验证
2. 确保新旧架构输出完全一致

## 📝 注意事项

1. **环境依赖**: 确保项目根目录在Python路径中
2. **数据库权限**: 确保有读写数据库文件的权限
3. **文件路径**: 工具脚本假设在项目根目录下运行
4. **备份机制**: `simple_validation.py` 会自动备份旧架构数据为 `tasks_old.db`

## 🐛 故障排除

### 常见问题

1. **找不到CSV文件**: 检查 `state/` 目录下是否有相应的CSV文件
2. **数据库锁定**: 确保没有其他进程在使用数据库文件
3. **权限错误**: 确保有删除和创建文件的权限
4. **模块导入错误**: 确保在项目根目录下运行脚本

### 调试建议

1. 使用 `--skip-clean` 参数跳过数据清理，快速重复验证
2. 检查日志输出，定位具体的差异位置
3. 手动检查生成的数据库文件内容
4. 比较CSV文件的字段和内容

## 🔄 更新历史

- **v1.0**: 基础的数量验证功能
- **v1.1**: 增加详细的消息内容比较功能
- **v1.2**: 修复CSV文件路径查找问题
- **v1.3**: 增强环境清理功能，支持状态文件清理
- **v1.4**: 添加消息标准化和差异定位功能
