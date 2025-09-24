#!/usr/bin/env python3
"""
快速验证工具

快速验证新旧架构的Task消息生成等价性，专注于关键指标。

使用方法:
    python scripts/quick_validation.py --city BJ
    python scripts/quick_validation.py --city SH
    python scripts/quick_validation.py --all
"""

import sys
import os
import sqlite3
import json
import argparse
from datetime import datetime
import logging

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.WARNING)  # 减少日志输出

def clean_environment():
    """清理测试环境"""
    for db_file in ['performance_data.db', 'tasks.db']:
        if os.path.exists(db_file):
            os.remove(db_file)
    
    # 清理CSV文件
    csv_files = [
        'state/PerformanceData-BJ-Sep.csv',
        'state/PerformanceData-SH-Sep.csv'
    ]
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            os.remove(csv_file)

def setup_database():
    """设置数据库"""
    from scripts.database_setup import create_tasks_table
    create_tasks_table()

def run_old_architecture_bj():
    """运行旧架构北京"""
    print("🏗️ 运行旧架构 - 北京9月...")
    try:
        from jobs import signing_and_sales_incentive_sep_beijing
        signing_and_sales_incentive_sep_beijing()
        return True
    except Exception as e:
        print(f"❌ 旧架构北京执行失败: {e}")
        return False

def run_old_architecture_sh():
    """运行旧架构上海"""
    print("🏗️ 运行旧架构 - 上海9月...")
    try:
        from jobs import signing_and_sales_incentive_sep_shanghai
        signing_and_sales_incentive_sep_shanghai()
        return True
    except Exception as e:
        print(f"❌ 旧架构上海执行失败: {e}")
        return False

def run_new_architecture_bj():
    """运行新架构北京"""
    print("🆕 运行新架构 - 北京9月...")
    try:
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        records = signing_and_sales_incentive_sep_beijing_v2()
        
        # 生成通知
        generate_notifications_bj(records)
        
        return True, len(records)
    except Exception as e:
        print(f"❌ 新架构北京执行失败: {e}")
        return False, 0

def run_new_architecture_sh():
    """运行新架构上海"""
    print("🆕 运行新架构 - 上海9月...")
    try:
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        records = signing_and_sales_incentive_sep_shanghai_v2()
        
        # 生成通知
        generate_notifications_sh(records)
        
        return True, len(records)
    except Exception as e:
        print(f"❌ 新架构上海执行失败: {e}")
        return False, 0

def generate_notifications_bj(records):
    """为北京生成通知"""
    if not records:
        return
    
    # 保存到CSV文件
    csv_file = 'state/PerformanceData-BJ-Sep.csv'
    save_records_to_csv(records, csv_file)
    
    # 生成通知
    from modules.notification_module import notify_awards_sep_beijing
    status_file = 'state/send_status_bj_sep.json'
    notify_awards_sep_beijing(csv_file, status_file)

def generate_notifications_sh(records):
    """为上海生成通知"""
    if not records:
        return
    
    # 保存到CSV文件
    csv_file = 'state/PerformanceData-SH-Sep.csv'
    save_records_to_csv(records, csv_file)
    
    # 生成通知
    from modules.notification_module import notify_awards_sep_shanghai
    status_file = 'state/send_status_shanghai_sep.json'
    notify_awards_sep_shanghai(csv_file, status_file)

def save_records_to_csv(records, csv_file):
    """保存记录到CSV文件"""
    import csv
    
    if not records:
        return
    
    # 确保目录存在
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    # 获取所有字段
    all_fields = set()
    record_dicts = []
    for record in records:
        record_dict = record.to_dict()
        all_fields.update(record_dict.keys())
        record_dicts.append(record_dict)
    
    # 写入CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
        writer.writeheader()
        writer.writerows(record_dicts)

def get_task_statistics():
    """获取任务统计"""
    if not os.path.exists('tasks.db'):
        return {}
    
    with sqlite3.connect('tasks.db') as conn:
        cursor = conn.execute("""
            SELECT task_type, COUNT(*) as count
            FROM tasks 
            GROUP BY task_type
        """)
        
        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = row[1]
        
        # 总数
        cursor = conn.execute("SELECT COUNT(*) FROM tasks")
        stats['total'] = cursor.fetchone()[0]
        
        return stats

def get_performance_statistics(csv_file):
    """获取业绩数据统计"""
    if not os.path.exists(csv_file):
        return {}
    
    import csv
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    if not records:
        return {}
    
    # 统计奖励类型
    reward_types = {}
    housekeepers = set()
    
    for record in records:
        # 奖励类型统计
        reward_type = record.get('奖励类型', record.get('reward_types', ''))
        if reward_type:
            reward_types[reward_type] = reward_types.get(reward_type, 0) + 1
        
        # 管家统计
        housekeeper = record.get('管家(serviceHousekeeper)', record.get('housekeeper', ''))
        if housekeeper:
            housekeepers.add(housekeeper)
    
    return {
        'total_records': len(records),
        'unique_housekeepers': len(housekeepers),
        'reward_types': reward_types
    }

def compare_results(old_tasks, new_tasks, old_perf, new_perf):
    """对比结果"""
    print("\n📊 结果对比:")
    print("-" * 50)
    
    # 任务对比
    print("📨 任务统计:")
    print(f"   旧架构总任务: {old_tasks.get('total', 0)}")
    print(f"   新架构总任务: {new_tasks.get('total', 0)}")
    print(f"   差异: {new_tasks.get('total', 0) - old_tasks.get('total', 0):+d}")
    
    # 任务类型对比
    all_types = set(old_tasks.keys()) | set(new_tasks.keys())
    all_types.discard('total')
    
    for task_type in sorted(all_types):
        old_count = old_tasks.get(task_type, 0)
        new_count = new_tasks.get(task_type, 0)
        if old_count != new_count:
            print(f"   {task_type}: {old_count} -> {new_count} ({new_count - old_count:+d})")
    
    # 业绩数据对比
    print("\n🗃️ 业绩数据:")
    print(f"   旧架构记录数: {old_perf.get('total_records', 0)}")
    print(f"   新架构记录数: {new_perf.get('total_records', 0)}")
    print(f"   旧架构管家数: {old_perf.get('unique_housekeepers', 0)}")
    print(f"   新架构管家数: {new_perf.get('unique_housekeepers', 0)}")
    
    # 奖励类型对比
    old_rewards = old_perf.get('reward_types', {})
    new_rewards = new_perf.get('reward_types', {})
    all_reward_types = set(old_rewards.keys()) | set(new_rewards.keys())
    
    if all_reward_types:
        print("\n🏆 奖励类型分布:")
        for reward_type in sorted(all_reward_types):
            old_count = old_rewards.get(reward_type, 0)
            new_count = new_rewards.get(reward_type, 0)
            if old_count != new_count:
                print(f"   {reward_type}: {old_count} -> {new_count} ({new_count - old_count:+d})")
    
    # 判断是否等价
    tasks_match = old_tasks.get('total', 0) == new_tasks.get('total', 0)
    records_match = old_perf.get('total_records', 0) == new_perf.get('total_records', 0)
    
    print(f"\n🎯 等价性判断:")
    print(f"   任务数量匹配: {'✅' if tasks_match else '❌'}")
    print(f"   记录数量匹配: {'✅' if records_match else '❌'}")
    
    return tasks_match and records_match

def validate_city(city):
    """验证指定城市"""
    print(f"\n🎯 验证 {city} 城市")
    print("=" * 40)
    
    # 清理环境
    clean_environment()
    setup_database()
    
    # 运行旧架构
    if city == 'BJ':
        old_success = run_old_architecture_bj()
        csv_file = 'state/PerformanceData-BJ-Sep.csv'
    else:
        old_success = run_old_architecture_sh()
        csv_file = 'state/PerformanceData-SH-Sep.csv'
    
    if not old_success:
        print("❌ 旧架构执行失败")
        return False
    
    # 获取旧架构结果
    old_tasks = get_task_statistics()
    old_perf = get_performance_statistics(csv_file)
    
    # 清理并重新设置
    clean_environment()
    setup_database()
    
    # 运行新架构
    if city == 'BJ':
        new_success, record_count = run_new_architecture_bj()
    else:
        new_success, record_count = run_new_architecture_sh()
    
    if not new_success:
        print("❌ 新架构执行失败")
        return False
    
    # 获取新架构结果
    new_tasks = get_task_statistics()
    new_perf = get_performance_statistics(csv_file)
    
    # 对比结果
    return compare_results(old_tasks, new_tasks, old_perf, new_perf)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='快速验证工具')
    parser.add_argument('--city', choices=['BJ', 'SH'], help='验证指定城市')
    parser.add_argument('--all', action='store_true', help='验证所有城市')
    
    args = parser.parse_args()
    
    print("⚡ 快速验证工具")
    print("=" * 40)
    print("验证新旧架构Task消息生成等价性")
    print("=" * 40)
    
    if args.all:
        cities = ['BJ', 'SH']
        all_passed = True
        
        for city in cities:
            try:
                passed = validate_city(city)
                all_passed = all_passed and passed
            except Exception as e:
                print(f"❌ {city} 验证异常: {e}")
                all_passed = False
        
        print(f"\n🏁 全部验证完成: {'✅ 全部通过' if all_passed else '❌ 存在问题'}")
        
    elif args.city:
        try:
            validate_city(args.city)
        except Exception as e:
            print(f"❌ 验证异常: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("❌ 请指定验证选项")
        print("💡 验证北京: python scripts/quick_validation.py --city BJ")
        print("💡 验证上海: python scripts/quick_validation.py --city SH")
        print("💡 验证全部: python scripts/quick_validation.py --all")

if __name__ == "__main__":
    main()
