#!/usr/bin/env python3
"""
快速手工测试脚本
用于本地快速验证新旧架构等价性

使用方法:
    python quick_manual_test.py --beijing    # 只测试北京
    python quick_manual_test.py --shanghai   # 只测试上海  
    python quick_manual_test.py --all        # 测试所有城市
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path

def run_command(cmd, description, ignore_notification_errors=False):
    """运行命令并显示结果"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)

        # 检查是否是通知相关的非关键错误
        if result.returncode != 0 and ignore_notification_errors:
            stderr_lower = result.stderr.lower()
            if ("no such table: tasks" in stderr_lower or
                "notification" in stderr_lower or
                "task_manager" in stderr_lower):
                print(f"⚠️ {description}完成（忽略通知错误）")
                return True

        if result.returncode == 0:
            print(f"✅ {description}完成")
            return True
        else:
            print(f"❌ {description}失败")
            print(f"错误: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description}超时")
        return False
    except Exception as e:
        print(f"❌ {description}异常: {e}")
        return False

def test_beijing():
    """测试北京9月"""
    print("\n" + "="*60)
    print("🏢 北京9月快速验证")
    print("="*60)
    
    # 清理环境
    print("🧹 清理环境...")
    os.system("rm -f performance_data.db state/PerformanceData-BJ-Sep.csv performance_data_BJ-SEP_*.csv")

    # 初始化数据库
    print("🔧 初始化数据库...")
    if not run_command("python scripts/init_database.py", "初始化数据库"):
        print("⚠️ 数据库初始化失败，继续执行...")
    
    # 执行旧架构
    old_cmd = '''python -c "
import sys
sys.path.insert(0, '.')
from jobs import signing_and_sales_incentive_sep_beijing
signing_and_sales_incentive_sep_beijing()
print('旧架构执行完成')
"'''
    
    if not run_command(old_cmd, "执行北京旧架构", ignore_notification_errors=True):
        return False
    
    # 检查旧架构输出
    if not os.path.exists('state/PerformanceData-BJ-Sep.csv'):
        print("❌ 旧架构未生成输出文件")
        return False
    
    # 执行新架构
    new_cmd = '''python -c "
import sys
sys.path.insert(0, '.')
from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
result = signing_and_sales_incentive_sep_beijing_v2()
print(f'新架构执行完成，处理了{len(result)}条记录')
"'''
    
    if not run_command(new_cmd, "执行北京新架构"):
        return False
    
    # 导出新架构数据
    export_cmd = "python scripts/export_database_to_csv.py --activity BJ-SEP --compatible"
    if not run_command(export_cmd, "导出北京新架构数据"):
        return False
    
    # 对比验证
    compare_cmd = "python scripts/manual_validation_helper.py"
    if not run_command(compare_cmd, "北京数据对比验证"):
        return False
    
    print("✅ 北京9月验证通过")
    return True

def test_shanghai():
    """测试上海9月"""
    print("\n" + "="*60)
    print("🏙️ 上海9月快速验证")
    print("="*60)
    
    # 清理环境
    print("🧹 清理环境...")
    os.system("rm -f performance_data.db state/PerformanceData-SH-Sep.csv performance_data_SH-SEP_*.csv")

    # 初始化数据库
    print("🔧 初始化数据库...")
    if not run_command("python scripts/init_database.py", "初始化数据库"):
        print("⚠️ 数据库初始化失败，继续执行...")
    
    # 执行旧架构
    old_cmd = '''python -c "
import sys
sys.path.insert(0, '.')
from jobs import signing_and_sales_incentive_sep_shanghai
signing_and_sales_incentive_sep_shanghai()
print('旧架构执行完成')
"'''
    
    if not run_command(old_cmd, "执行上海旧架构", ignore_notification_errors=True):
        return False
    
    # 检查旧架构输出
    if not os.path.exists('state/PerformanceData-SH-Sep.csv'):
        print("❌ 旧架构未生成输出文件")
        return False
    
    # 执行新架构
    new_cmd = '''python -c "
import sys
sys.path.insert(0, '.')
from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
result = signing_and_sales_incentive_sep_shanghai_v2()
print(f'新架构执行完成，处理了{len(result)}条记录')
"'''
    
    if not run_command(new_cmd, "执行上海新架构"):
        return False
    
    # 导出新架构数据
    export_cmd = "python scripts/export_database_to_csv.py --activity SH-SEP"
    if not run_command(export_cmd, "导出上海新架构数据"):
        return False
    
    # 对比验证
    compare_cmd = "python scripts/manual_validation_helper.py"
    if not run_command(compare_cmd, "上海数据对比验证"):
        return False
    
    print("✅ 上海9月验证通过")
    return True

def main():
    parser = argparse.ArgumentParser(description='快速手工测试脚本')
    parser.add_argument('--beijing', action='store_true', help='只测试北京')
    parser.add_argument('--shanghai', action='store_true', help='只测试上海')
    parser.add_argument('--all', action='store_true', help='测试所有城市')
    
    args = parser.parse_args()
    
    # 检查环境
    if not os.path.exists('modules'):
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    print("🔍 快速手工测试工具")
    print("=" * 60)
    print("目标: 验证新旧架构等价性")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    # 根据参数决定测试范围
    if args.beijing or args.all:
        total_count += 1
        if test_beijing():
            success_count += 1
    
    if args.shanghai or args.all:
        total_count += 1
        if test_shanghai():
            success_count += 1
    
    if not (args.beijing or args.shanghai or args.all):
        print("请指定测试范围: --beijing, --shanghai, 或 --all")
        parser.print_help()
        sys.exit(1)
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有测试通过！新旧架构完全等价")
        print("✅ 可以安全部署新架构")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查问题")
        print("💡 建议查看详细日志: tail -f logs/app.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
