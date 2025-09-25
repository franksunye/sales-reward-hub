#!/usr/bin/env python3
"""
简化验证工具

专注于调用新旧架构函数并比较结果，不重新实现业务逻辑。
适合快速测试，特别是上海数据（192条记录）。

使用方法:
    python scripts/simple_validation.py --city SH
    python scripts/simple_validation.py --city BJ
    python scripts/simple_validation.py --city SH --no-clean
"""

import sys
import os
import sqlite3
import argparse
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def get_task_count():
    """获取任务总数"""
    if not os.path.exists('tasks.db'):
        return 0
    
    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM tasks")
        return cursor.fetchone()[0]

def get_performance_count():
    """获取业绩记录总数"""
    if not os.path.exists('performance_data.db'):
        return 0
    
    with sqlite3.connect('performance_data.db') as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM performance_data")
        return cursor.fetchone()[0]

def clean_test_data(city, activity):
    """使用专用清理工具彻底清理测试数据"""
    print("🧹 使用专用清理工具清理测试数据...")

    # 调用专用的清理工具
    import subprocess
    import sys

    cmd = [sys.executable, 'scripts/clean_test_data.py']
    if city and activity:
        cmd.extend(['--city', city, '--activity', activity])
    else:
        cmd.append('--all')

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("   ✅ 专用清理工具执行成功")
            # 打印清理工具的关键输出
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.strip() and ('清理' in line or '删除' in line or '✅' in line):
                    print(f"   {line.strip()}")
        else:
            print(f"   ❌ 专用清理工具执行失败: {result.stderr}")
            raise Exception(f"清理工具失败: {result.stderr}")
    except Exception as e:
        print(f"   ❌ 调用专用清理工具失败: {e}")
        raise

    # 确保tasks.db存在（清理工具可能删除了它）
    from scripts.database_setup import create_tasks_table
    if not os.path.exists('tasks.db'):
        create_tasks_table()
        print("   重新创建: tasks.db")

    print()

def run_old_architecture(city):
    """运行旧架构"""
    print("🏗️ 运行旧架构...")

    if city == 'SH':
        from jobs import signing_and_sales_incentive_sep_shanghai
        result = signing_and_sales_incentive_sep_shanghai()
    else:  # BJ
        from jobs import signing_and_sales_incentive_sep_beijing
        result = signing_and_sales_incentive_sep_beijing()

    tasks = get_task_count()
    perf = get_performance_count()

    print(f"   任务数: {tasks}")
    print(f"   业绩记录数: {perf}")

    # 备份旧架构的tasks.db
    if os.path.exists('tasks.db') and tasks > 0:
        import shutil
        shutil.copy2('tasks.db', 'tasks_old.db')
        print(f"   备份旧架构数据: tasks.db → tasks_old.db")

    print()

    return {'tasks': tasks, 'performance': perf, 'result': result}

def run_new_architecture(city):
    """运行新架构"""
    print("🆕 运行新架构...")

    # 清理tasks.db，为新架构准备干净环境
    if os.path.exists('tasks.db'):
        os.remove('tasks.db')
        print("   清理旧的tasks.db")

    # 重新创建空的tasks.db
    from scripts.database_setup import create_tasks_table
    create_tasks_table()
    print("   创建新的tasks.db")

    if city == 'SH':
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        result = signing_and_sales_incentive_sep_shanghai_v2()
    else:  # BJ
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        result = signing_and_sales_incentive_sep_beijing_v2()

    # 获取新架构生成的任务数
    new_tasks = get_task_count()
    perf = get_performance_count()

    print(f"   返回记录数: {len(result) if result else 0}")
    print(f"   新架构任务数: {new_tasks}")
    print(f"   业绩记录数: {perf}")
    print()

    return {'tasks': new_tasks, 'performance': perf, 'result': result}

def get_task_count_from_file(db_file):
    """从指定数据库文件获取任务数"""
    if not os.path.exists(db_file):
        return 0

    with sqlite3.connect(db_file) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM tasks")
        return cursor.fetchone()[0]

def compare_results(old_result, new_result):
    """比较结果"""
    print("📊 结果对比")
    print("=" * 50)

    # 任务数对比
    old_tasks = old_result['tasks']
    new_tasks = new_result['tasks']
    tasks_match = old_tasks == new_tasks

    print(f"📋 任务数对比:")
    print(f"   旧架构 (tasks_old.db): {old_tasks}")
    print(f"   新架构 (tasks.db): {new_tasks}")
    print(f"   匹配: {'✅' if tasks_match else '❌'}")

    # 验证备份文件
    old_backup_tasks = get_task_count_from_file('tasks_old.db')
    if old_backup_tasks != old_tasks:
        print(f"   ⚠️ 备份验证: tasks_old.db中有{old_backup_tasks}条记录")

    # 业绩记录数对比
    old_perf = old_result['performance']
    new_perf = new_result['performance']
    perf_match = old_perf == new_perf

    print(f"\n🗃️ 业绩记录数对比:")
    print(f"   旧架构: {old_perf}")
    print(f"   新架构: {new_perf}")
    print(f"   匹配: {'✅' if perf_match else '❌'}")

    # 总体结论
    overall_match = tasks_match and perf_match

    print(f"\n🎯 总体结论:")
    print(f"   {'✅ 新旧架构完全等价！' if overall_match else '❌ 新旧架构存在差异'}")

    if not overall_match:
        print(f"\n📋 详细差异:")
        if not tasks_match:
            print(f"   任务数差异: {new_tasks - old_tasks}")
        if not perf_match:
            print(f"   业绩记录差异: {new_perf - old_perf}")

    return overall_match

def validate_architecture(city, clean_data=True):
    """验证架构等价性"""
    activity = f"{city}-SEP"
    
    print("🔍 简化验证工具")
    print("=" * 50)
    print(f"🎯 验证目标: {city} {activity}")
    print(f"🧹 清理数据: {'是' if clean_data else '否'}")
    print("=" * 50)
    print()
    
    # 清理数据（如果需要）
    if clean_data:
        clean_test_data(city, activity)
    
    # 运行旧架构
    old_result = run_old_architecture(city)
    
    # 运行新架构
    new_result = run_new_architecture(city)
    
    # 比较结果
    return compare_results(old_result, new_result)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化验证工具')
    parser.add_argument('--city', choices=['BJ', 'SH'], required=True, help='城市代码')
    parser.add_argument('--no-clean', action='store_true', help='不清理数据，使用现有数据测试')
    
    args = parser.parse_args()
    
    clean_data = not args.no_clean
    
    try:
        success = validate_architecture(args.city, clean_data)
        if success:
            print("\n🎉 验证成功！新旧架构完全等价。")
        else:
            print("\n⚠️ 验证发现差异，需要进一步检查。")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
