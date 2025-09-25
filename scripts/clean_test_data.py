#!/usr/bin/env python3
"""
测试数据清理脚本

清理测试相关的数据，确保可以进行干净的测试：
1. 清空数据库中的业绩记录（保留表结构）
2. 清空任务记录
3. 清理CSV输出文件
4. 保留数据库结构和配置

使用方法:
    python scripts/clean_test_data.py --all
    python scripts/clean_test_data.py --city SH --activity SH-SEP
    python scripts/clean_test_data.py --databases-only
    python scripts/clean_test_data.py --files-only
"""

import os
import sqlite3
import glob
import argparse
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_performance_database(activity_code=None):
    """清理新架构的业绩数据库 (performance_data.db)"""
    db_path = 'performance_data.db'

    if not os.path.exists(db_path):
        print(f"📊 新架构数据库文件不存在: {db_path}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 获取清理前的记录数
            if activity_code:
                cursor.execute("SELECT COUNT(*) FROM performance_data WHERE activity_code = ?", (activity_code,))
                before_count = cursor.fetchone()[0]

                # 清理指定活动的记录
                cursor.execute("DELETE FROM performance_data WHERE activity_code = ?", (activity_code,))
                deleted_count = cursor.rowcount

                print(f"📊 清理新架构业绩数据库 ({activity_code}): 删除 {deleted_count} 条记录")
            else:
                cursor.execute("SELECT COUNT(*) FROM performance_data")
                before_count = cursor.fetchone()[0]

                # 清理所有记录
                cursor.execute("DELETE FROM performance_data")
                deleted_count = cursor.rowcount

                print(f"📊 清理新架构业绩数据库 (全部): 删除 {deleted_count} 条记录")

            conn.commit()

    except Exception as e:
        print(f"❌ 清理新架构业绩数据库失败: {e}")

def clean_tasks_database():
    """清理旧架构的任务数据库 (tasks.db)"""
    db_path = 'tasks.db'

    if not os.path.exists(db_path):
        print(f"📋 旧架构任务数据库文件不存在: {db_path}")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 获取清理前的记录数
            cursor.execute("SELECT COUNT(*) FROM tasks")
            before_count = cursor.fetchone()[0]

            # 清理所有任务记录
            cursor.execute("DELETE FROM tasks")
            deleted_count = cursor.rowcount

            conn.commit()

            print(f"📋 清理旧架构任务数据库: 删除 {deleted_count} 条记录")

    except Exception as e:
        print(f"❌ 清理旧架构任务数据库失败: {e}")

def clean_state_directory_files(city=None, activity=None):
    """清理旧架构的state目录文件"""
    patterns = []

    if city and activity:
        # 清理特定城市和活动的文件
        patterns = [
            f"state/PerformanceData-{activity}.csv",
            f"state/*{activity}*",
            f"state/*{city}*"
        ]
    else:
        # 清理所有state目录文件
        patterns = [
            "state/PerformanceData-*.csv",
            "state/*-SEP*",
            "state/*.csv"
        ]

    deleted_files = []

    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
                print(f"🗑️ 删除旧架构文件: {file_path}")
            except Exception as e:
                print(f"❌ 删除旧架构文件失败 {file_path}: {e}")

    if not deleted_files:
        print("📁 没有找到需要清理的旧架构state文件")
    else:
        print(f"📁 共删除 {len(deleted_files)} 个旧架构state文件")

def clean_new_architecture_csv_files(city=None, activity=None):
    """清理新架构的CSV输出文件"""
    patterns = []

    if city and activity:
        # 清理特定城市和活动的文件
        patterns = [
            f"performance_data_{activity}_*.csv",
            f"performance_data_{activity}_dual_track_*.csv"
        ]
    else:
        # 清理所有新架构相关文件
        patterns = [
            "performance_data_*-SEP_*.csv",
            "performance_data_*-SEP_dual_track_*.csv"
        ]

    deleted_files = []

    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
                print(f"🗑️ 删除新架构文件: {file_path}")
            except Exception as e:
                print(f"❌ 删除新架构文件失败 {file_path}: {e}")

    if not deleted_files:
        print("📁 没有找到需要清理的新架构CSV文件")
    else:
        print(f"📁 共删除 {len(deleted_files)} 个新架构CSV文件")

def clean_all_test_data(city=None, activity=None):
    """清理所有测试数据（新旧架构）"""
    print("🧹 开始清理测试数据...")
    print("=" * 60)

    # 构建活动代码
    activity_code = None
    if city and activity:
        activity_code = activity
        print(f"🎯 目标: {city} {activity}")
    else:
        print("🎯 目标: 全部数据")

    print()

    # 清理新架构数据
    print("🆕 清理新架构数据:")
    clean_performance_database(activity_code)
    clean_new_architecture_csv_files(city, activity)

    print()

    # 清理旧架构数据
    print("🏗️ 清理旧架构数据:")
    clean_tasks_database()
    clean_state_directory_files(city, activity)

    print()
    print("✅ 数据清理完成")
    print("💡 现在可以进行干净的测试了")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试数据清理工具')
    parser.add_argument('--all', action='store_true', help='清理所有测试数据')
    parser.add_argument('--city', choices=['BJ', 'SH'], help='城市代码')
    parser.add_argument('--activity', help='活动代码 (如: SH-SEP, BJ-SEP)')
    parser.add_argument('--databases-only', action='store_true', help='只清理数据库')
    parser.add_argument('--files-only', action='store_true', help='只清理文件')
    
    args = parser.parse_args()
    
    print("🧹 测试数据清理工具")
    print("=" * 50)
    
    if args.all:
        clean_all_test_data()
    elif args.city and args.activity:
        clean_all_test_data(args.city, args.activity)
    elif args.databases_only:
        print("🗃️ 只清理数据库...")
        print("🆕 清理新架构数据库:")
        clean_performance_database()
        print("🏗️ 清理旧架构数据库:")
        clean_tasks_database()
        print("✅ 数据库清理完成")
    elif args.files_only:
        print("📁 只清理文件...")
        print("🆕 清理新架构文件:")
        clean_new_architecture_csv_files()
        print("🏗️ 清理旧架构文件:")
        clean_state_directory_files()
        print("✅ 文件清理完成")
    else:
        print("❌ 请指定清理选项")
        print("💡 示例:")
        print("  python scripts/clean_test_data.py --all")
        print("  python scripts/clean_test_data.py --city SH --activity SH-SEP")
        print("  python scripts/clean_test_data.py --databases-only")

if __name__ == "__main__":
    main()
