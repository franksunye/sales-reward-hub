# 升级指南: v1.0.1-stable → v2.0.0

## 升级概述

本指南帮助你从稳定的v1.0.1版本升级到v2.0.0版本，确保平滑过渡和功能等价性。

## 版本对比

### v1.0.1-stable 特点
✅ **生产稳定** - 已验证的稳定版本  
✅ **文件存储** - CSV文件存储业绩数据  
✅ **硬编码配置** - 配置直接写在代码中  
✅ **城市特定** - 每个城市独立处理函数  

### v2.0.0 新特性
🆕 **双存储模式** - 支持文件和数据库存储  
🆕 **环境变量** - 敏感信息环境变量化  
🆕 **通用化架构** - 配置驱动的通用处理  
🆕 **功能等价** - 与v1.0.1完全等价的功能  

## 升级准备

### 1. 环境准备
```bash
# 1. 备份当前生产环境
git tag v1.0.1-production-backup
git stash push -m "production config backup"

# 2. 创建升级分支
git checkout v1.0.1-stable
git checkout -b upgrade-to-v2.0

# 3. 准备测试环境
mkdir upgrade_test
cp -r state/ upgrade_test/
cp -r logs/ upgrade_test/
```

### 2. 环境变量准备
创建 `config/.env` 文件：
```bash
# 数据源配置
METABASE_USERNAME=wangshuang@xlink.bj.cn
METABASE_PASSWORD=xlink123456

# 企业微信配置
WECOM_WEBHOOK_DEFAULT=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=689cebff-3328-4150-9741-fed8b8ce4713
WECOM_WEBHOOK_CONTACT_TIMEOUT=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=80ab1f45-2526-4b41-a639-c580ccde3e2f

# 联系信息
CONTACT_PHONE_NUMBER=15327103039
```

### 3. 数据迁移准备
```bash
# 备份现有数据
mkdir data_backup
cp state/PerformanceData-*.csv data_backup/
cp state/send_status_*.json data_backup/
```

## 升级步骤

### 第一阶段：测试环境验证

#### 1. 切换到v2.0.0
```bash
git checkout v2.0.0
```

#### 2. 配置环境变量
```bash
# Windows
copy config\.env.example config\.env
# 编辑 config\.env 填入实际值
```

#### 3. 配置存储模式
在 `modules/config.py` 中：
```python
# 第一次测试使用文件模式（与v1.0.1兼容）
USE_DATABASE_FOR_PERFORMANCE_DATA = False
USE_GENERIC_PROCESS_FUNCTION = False
```

#### 4. 运行等价性验证
```bash
# 验证北京5月功能等价性
python scripts/verify_beijing_may_equivalence.py

# 验证上海5月功能等价性
python scripts/verify_shanghai_may_equivalence.py

# 验证通知功能等价性
python scripts/verify_notification_equivalence.py
```

### 第二阶段：功能验证

#### 1. 文件模式测试
```python
# 配置文件模式
USE_DATABASE_FOR_PERFORMANCE_DATA = False
USE_GENERIC_PROCESS_FUNCTION = True  # 使用通用函数

# 运行测试
python main.py --env dev --task beijing-may --run-once
```

#### 2. 数据库模式测试
```python
# 配置数据库模式
USE_DATABASE_FOR_PERFORMANCE_DATA = True
USE_GENERIC_PROCESS_FUNCTION = True

# 运行测试
python main.py --env dev --task beijing-may --run-once
```

#### 3. 对比验证
```bash
# 对比文件模式和数据库模式结果
python scripts/compare_storage_modes.py
```

### 第三阶段：生产环境升级

#### 1. 生产环境准备
```bash
# 1. 停止当前生产服务
# 2. 备份生产数据
cp -r state/ production_backup_$(date +%Y%m%d)/
cp -r logs/ production_backup_$(date +%Y%m%d)/

# 3. 设置生产环境变量
# 在生产服务器上配置环境变量
```

#### 2. 渐进式升级
```python
# 第一步：使用v2.0但保持文件模式
USE_DATABASE_FOR_PERFORMANCE_DATA = False
USE_GENERIC_PROCESS_FUNCTION = False  # 使用传统函数

# 第二步：启用通用函数
USE_GENERIC_PROCESS_FUNCTION = True

# 第三步：启用数据库模式（可选）
USE_DATABASE_FOR_PERFORMANCE_DATA = True
```

#### 3. 监控和验证
```bash
# 监控日志
tail -f logs/app.log

# 验证数据一致性
python scripts/verify_production_upgrade.py

# 检查通知发送
grep "notify_awards" logs/app.log
```

## 回滚计划

### 快速回滚
```bash
# 1. 停止v2.0服务
# 2. 切换回v1.0.1-stable
git checkout v1.0.1-stable

# 3. 恢复配置
git stash pop

# 4. 恢复数据
cp production_backup_*/state/* state/
cp production_backup_*/logs/* logs/

# 5. 重启服务
python main.py
```

### 数据回滚
```bash
# 如果使用了数据库模式，需要导出数据回CSV
python scripts/export_db_to_csv.py

# 恢复文件状态
cp data_backup/* state/
```

## 验证清单

### 功能验证
- [ ] 奖励计算结果一致
- [ ] 通知消息格式正确
- [ ] 文件存储功能正常
- [ ] 数据库存储功能正常
- [ ] 环境变量加载正确
- [ ] 日志输出正常

### 性能验证
- [ ] 处理速度无明显下降
- [ ] 内存使用正常
- [ ] 文件大小合理
- [ ] 数据库性能良好

### 安全验证
- [ ] 敏感信息不在日志中
- [ ] 环境变量正确加载
- [ ] 配置文件无敏感信息
- [ ] 权限设置正确

## 故障排除

### 常见问题

#### 1. 环境变量未加载
```bash
# 检查环境变量
python -c "import os; print(os.getenv('METABASE_USERNAME'))"

# Windows设置环境变量
setx METABASE_USERNAME "your_username"
```

#### 2. 数据库连接问题
```python
# 检查数据库文件
import sqlite3
conn = sqlite3.connect('tasks.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())
```

#### 3. 功能不等价
```bash
# 运行详细对比
python scripts/detailed_equivalence_check.py --verbose

# 检查配置差异
python scripts/compare_configs.py v1.0.1 v2.0.0
```

### 支持联系

如果遇到升级问题：
1. 查看详细日志：`logs/app.log`
2. 运行诊断脚本：`python scripts/diagnose_upgrade.py`
3. 检查验证报告：`tests/test_data/*_verification_report.txt`

## 升级后优化

### 配置优化
```python
# 根据实际需求选择最佳配置
USE_DATABASE_FOR_PERFORMANCE_DATA = True   # 推荐：数据库模式
USE_GENERIC_PROCESS_FUNCTION = True        # 推荐：通用函数
```

### 性能优化
- 定期清理日志文件
- 优化数据库索引
- 监控系统资源使用

### 安全优化
- 定期更换API密钥
- 检查环境变量安全性
- 审查日志脱敏效果

---

**升级指南版本**: v1.0→v2.0 | **更新日期**: 2025-05-17 | **状态**: 测试就绪
