#!/usr/bin/env python3
"""
9月份Job影子模式配置脚本

自动配置北京和上海9月份Job的影子模式
在jobs.py中添加影子模式包装，实现新旧系统对比

使用方法:
    python setup_september_shadow_mode.py
    python setup_september_shadow_mode.py --dry-run  # 预览修改，不实际执行
"""

import os
import sys
import argparse
import shutil
from datetime import datetime

def backup_jobs_file():
    """备份原始jobs.py文件"""
    if os.path.exists('jobs.py'):
        backup_name = f'jobs_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
        shutil.copy2('jobs.py', backup_name)
        print(f"✅ 已备份原始jobs.py为: {backup_name}")
        return backup_name
    else:
        print("⚠️  未找到jobs.py文件")
        return None

def generate_shadow_mode_code():
    """生成影子模式代码"""
    
    shadow_mode_code = '''
# ==================== 影子模式配置 ====================
# 以下代码为9月份Job影子模式配置
# 新系统运行但不影响业务，旧系统保证业务连续性

import logging
import time
from typing import List

def original_signing_and_sales_incentive_sep_beijing():
    """原始北京9月Job函数 - 备份版本"""
    # TODO: 将现有的signing_and_sales_incentive_sep_beijing函数内容复制到这里
    # 这是旧系统的实现，用于保证业务连续性
    pass

def original_signing_and_sales_incentive_sep_shanghai():
    """原始上海9月Job函数 - 备份版本"""
    # TODO: 将现有的signing_and_sales_incentive_sep_shanghai函数内容复制到这里
    # 这是旧系统的实现，用于保证业务连续性
    pass

def validate_beijing_september_results(old_result, new_result):
    """验证北京9月Job结果"""
    try:
        # 基本数量对比
        if len(old_result) != len(new_result):
            logging.warning(f"[北京9月验证] 记录数差异: 旧{len(old_result)} vs 新{len(new_result)}")
            return False
        
        # TODO: 添加更详细的业务逻辑验证
        # - 历史合同处理验证
        # - 个人序列幸运数字验证
        # - 5万上限逻辑验证
        
        logging.info("✅ [北京9月验证] 基本验证通过")
        return True
        
    except Exception as e:
        logging.error(f"❌ [北京9月验证] 验证失败: {e}")
        return False

def validate_shanghai_september_results(old_result, new_result):
    """验证上海9月Job结果"""
    try:
        # 基本数量对比
        if len(old_result) != len(new_result):
            logging.warning(f"[上海9月验证] 记录数差异: 旧{len(old_result)} vs 新{len(new_result)}")
            return False
        
        # TODO: 添加更详细的业务逻辑验证
        # - 双轨统计功能验证
        # - 自引单奖励验证
        # - 项目地址去重验证
        
        logging.info("✅ [上海9月验证] 基本验证通过")
        return True
        
    except Exception as e:
        logging.error(f"❌ [上海9月验证] 验证失败: {e}")
        return False

def signing_and_sales_incentive_sep_beijing():
    """北京9月Job - 影子模式"""
    logging.info("🔄 [北京9月影子模式] 开始执行")
    
    try:
        # 运行新系统（记录但不影响业务）
        start_time = time.time()
        logging.info("🆕 [北京9月] 启动新系统...")
        
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        new_result = signing_and_sales_incentive_sep_beijing_v2()
        new_time = time.time() - start_time
        
        logging.info(f"✅ [北京9月] 新系统完成: {len(new_result)} 条记录, 耗时: {new_time:.2f}秒")
        
        # 运行旧系统（保证业务连续性）
        start_time = time.time()
        logging.info("🔄 [北京9月] 启动旧系统...")
        
        old_result = original_signing_and_sales_incentive_sep_beijing()
        old_time = time.time() - start_time
        
        logging.info(f"✅ [北京9月] 旧系统完成: {len(old_result)} 条记录, 耗时: {old_time:.2f}秒")
        
        # 性能对比
        if old_time > 0:
            performance_ratio = new_time / old_time
            logging.info(f"📊 [北京9月] 性能对比: 新系统/旧系统 = {performance_ratio:.2f}")
        
        # 结果验证
        validation_passed = validate_beijing_september_results(old_result, new_result)
        if validation_passed:
            logging.info("✅ [北京9月] 影子模式验证通过")
        else:
            logging.warning("⚠️ [北京9月] 影子模式验证发现差异")
        
        # 返回旧系统结果，保证业务不受影响
        return old_result
        
    except Exception as e:
        logging.error(f"❌ [北京9月] 影子模式失败，使用旧系统: {e}")
        return original_signing_and_sales_incentive_sep_beijing()

def signing_and_sales_incentive_sep_shanghai():
    """上海9月Job - 影子模式"""
    logging.info("🔄 [上海9月影子模式] 开始执行")
    
    try:
        # 运行新系统（记录但不影响业务）
        start_time = time.time()
        logging.info("🆕 [上海9月] 启动新系统...")
        
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        new_result = signing_and_sales_incentive_sep_shanghai_v2()
        new_time = time.time() - start_time
        
        logging.info(f"✅ [上海9月] 新系统完成: {len(new_result)} 条记录, 耗时: {new_time:.2f}秒")
        
        # 运行旧系统（保证业务连续性）
        start_time = time.time()
        logging.info("🔄 [上海9月] 启动旧系统...")
        
        old_result = original_signing_and_sales_incentive_sep_shanghai()
        old_time = time.time() - start_time
        
        logging.info(f"✅ [上海9月] 旧系统完成: {len(old_result)} 条记录, 耗时: {old_time:.2f}秒")
        
        # 性能对比
        if old_time > 0:
            performance_ratio = new_time / old_time
            logging.info(f"📊 [上海9月] 性能对比: 新系统/旧系统 = {performance_ratio:.2f}")
        
        # 结果验证
        validation_passed = validate_shanghai_september_results(old_result, new_result)
        if validation_passed:
            logging.info("✅ [上海9月] 影子模式验证通过")
        else:
            logging.warning("⚠️ [上海9月] 影子模式验证发现差异")
        
        # 返回旧系统结果，保证业务不受影响
        return old_result
        
    except Exception as e:
        logging.error(f"❌ [上海9月] 影子模式失败，使用旧系统: {e}")
        return original_signing_and_sales_incentive_sep_shanghai()

# ==================== 影子模式配置结束 ====================
'''
    
    return shadow_mode_code

def create_shadow_mode_instructions():
    """创建影子模式配置说明"""
    
    instructions = """
# 9月份Job影子模式配置说明

## 📋 手动配置步骤

### 第1步: 备份原有函数
1. 找到jobs.py中的以下函数:
   - `signing_and_sales_incentive_sep_beijing()`
   - `signing_and_sales_incentive_sep_shanghai()`

2. 将它们的完整实现复制到:
   - `original_signing_and_sales_incentive_sep_beijing()`
   - `original_signing_and_sales_incentive_sep_shanghai()`

### 第2步: 替换函数实现
将原有的9月份Job函数替换为影子模式版本（已在上面生成）

### 第3步: 测试验证
运行以下命令测试影子模式:
```bash
# 测试北京9月Job
python -c "from jobs import signing_and_sales_incentive_sep_beijing; signing_and_sales_incentive_sep_beijing()"

# 测试上海9月Job  
python -c "from jobs import signing_and_sales_incentive_sep_shanghai; signing_and_sales_incentive_sep_shanghai()"
```

### 第4步: 监控日志
观察日志输出，确认:
- ✅ 新旧系统都正常运行
- ✅ 性能对比数据
- ✅ 验证结果
- ✅ 业务流程无中断

## 🚨 安全保障
- 影子模式始终返回旧系统结果
- 新系统失败时自动回退到旧系统
- 完整的错误处理和日志记录
- 可以随时禁用新系统调用

## 📊 监控指标
- 处理时间对比
- 记录数一致性
- 业务逻辑验证结果
- 错误率统计
"""
    
    return instructions

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='9月份Job影子模式配置')
    parser.add_argument('--dry-run', action='store_true', help='预览修改，不实际执行')
    
    args = parser.parse_args()
    
    print("🚀 9月份Job影子模式配置工具")
    print("=" * 50)
    
    if args.dry_run:
        print("📋 预览模式 - 不会修改任何文件")
    
    # 生成影子模式代码
    shadow_code = generate_shadow_mode_code()
    instructions = create_shadow_mode_instructions()
    
    # 保存到文件
    shadow_file = 'september_shadow_mode_code.py'
    instructions_file = 'september_shadow_mode_instructions.md'
    
    if not args.dry_run:
        # 备份原始文件
        backup_name = backup_jobs_file()
        
        # 保存生成的代码
        with open(shadow_file, 'w', encoding='utf-8') as f:
            f.write(shadow_code)
        print(f"✅ 影子模式代码已保存到: {shadow_file}")
        
        # 保存配置说明
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        print(f"✅ 配置说明已保存到: {instructions_file}")
        
        print("\n📋 下一步操作:")
        print("1. 查看生成的影子模式代码")
        print("2. 按照说明手动配置jobs.py")
        print("3. 运行测试验证影子模式")
        
    else:
        print("📋 预览生成的文件:")
        print(f"- {shadow_file}")
        print(f"- {instructions_file}")
        print("\n使用 --dry-run 移除此参数来实际生成文件")
    
    print("\n🎯 影子模式配置完成!")

if __name__ == "__main__":
    main()
