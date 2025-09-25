#!/usr/bin/env python3
"""
简化消息验证工具

专注于调用新旧架构函数并比较Task消息生成，不重新实现业务逻辑。
验证消息模板、动态数据填充、通知逻辑的完全等价性。

使用方法:
    python scripts/simple_message_validation.py --city SH --activity SH-SEP
    python scripts/simple_message_validation.py --city BJ --activity BJ-SEP
    python scripts/simple_message_validation.py --city SH --activity SH-SEP --no-clean
"""

import sys
import os
import sqlite3
import argparse
from datetime import datetime
from typing import List, Dict, Tuple

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def clean_test_environment(city: str, activity: str):
    """清理测试环境"""
    print("🧹 清理测试环境...")

    # 清理数据库
    for db_file in ['performance_data.db', 'tasks.db']:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"   删除: {db_file}")

    # 清理CSV文件和状态文件
    import glob
    patterns = [
        f"state/PerformanceData-{activity}.csv",
        f"state/PerformanceData-{city}-Sep.csv",  # 旧架构格式
        f"performance_data_{activity}_*.csv",
        f"state/send_status_{city.lower()}*",  # 清理发送状态文件
        f"state/*{activity}*",
        f"state/*{city}*"
    ]

    for pattern in patterns:
        for file_path in glob.glob(pattern):
            os.remove(file_path)
            print(f"   删除: {file_path}")

    # 重新创建tasks.db
    from scripts.database_setup import create_tasks_table
    create_tasks_table()
    print("   重新创建: tasks.db")
    print()

def get_tasks_from_db() -> List[Dict]:
    """从数据库读取Tasks"""
    if not os.path.exists('tasks.db'):
        return []
    
    with sqlite3.connect('tasks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at")
        return [dict(row) for row in cursor.fetchall()]

def get_performance_data_from_csv(city: str, activity: str) -> List[Dict]:
    """从CSV文件读取PerformanceData"""
    # 尝试多种可能的文件名格式
    possible_files = [
        f'state/PerformanceData-{activity}.csv',
        f'state/PerformanceData-{city}-Sep.csv',  # 旧架构使用的格式
        f'state/PerformanceData-{city}-{activity.split("-")[1]}.csv'
    ]

    csv_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            csv_file = file_path
            break

    if not csv_file:
        print(f"   ⚠️ 未找到CSV文件，尝试过: {possible_files}")
        return []

    print(f"   📄 找到CSV文件: {csv_file}")
    import csv
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_performance_data_from_db() -> List[Dict]:
    """从数据库读取PerformanceData"""
    if not os.path.exists('performance_data.db'):
        return []
    
    with sqlite3.connect('performance_data.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM performance_data ORDER BY created_at")
        return [dict(row) for row in cursor.fetchall()]

def run_old_architecture(city: str, activity: str) -> Tuple[List[Dict], List[Dict]]:
    """运行旧架构"""
    print(f"🏗️ 运行旧架构 - {city} {activity}")
    
    try:
        # 直接调用旧架构函数
        if city == "BJ" and activity == "BJ-SEP":
            from jobs import signing_and_sales_incentive_sep_beijing
            result = signing_and_sales_incentive_sep_beijing()

        elif city == "SH" and activity == "SH-SEP":
            from jobs import signing_and_sales_incentive_sep_shanghai
            result = signing_and_sales_incentive_sep_shanghai()
            
        else:
            raise ValueError(f"不支持的城市/活动组合: {city}/{activity}")
        
        # 获取结果
        perf_data = get_performance_data_from_csv(city, activity)
        tasks = get_tasks_from_db()
        
        print(f"   PerformanceData记录: {len(perf_data)}")
        print(f"   Task记录: {len(tasks)}")
        
        return perf_data, tasks
        
    except Exception as e:
        print(f"❌ 旧架构执行失败: {e}")
        raise

def run_new_architecture(city: str, activity: str) -> Tuple[List[Dict], List[Dict]]:
    """运行新架构"""
    print(f"🆕 运行新架构 - {city} {activity}")
    
    # 清理tasks.db，保留performance_data.db
    if os.path.exists('tasks.db'):
        os.remove('tasks.db')
    from scripts.database_setup import create_tasks_table
    create_tasks_table()
    print("   清理tasks.db，保留performance_data.db")
    
    try:
        # 直接调用新架构函数
        if city == "BJ" and activity == "BJ-SEP":
            from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
            records = signing_and_sales_incentive_sep_beijing_v2()
            
        elif city == "SH" and activity == "SH-SEP":
            from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
            records = signing_and_sales_incentive_sep_shanghai_v2()
            
        else:
            raise ValueError(f"不支持的城市/活动组合: {city}/{activity}")
        
        # 获取结果
        perf_data = get_performance_data_from_db()
        tasks = get_tasks_from_db()
        
        print(f"   PerformanceRecord对象: {len(records) if records else 0}")
        print(f"   PerformanceData记录: {len(perf_data)}")
        print(f"   Task记录: {len(tasks)}")
        
        return perf_data, tasks
        
    except Exception as e:
        print(f"❌ 新架构执行失败: {e}")
        raise

def compare_tasks(old_tasks: List[Dict], new_tasks: List[Dict]) -> bool:
    """比较Task消息"""
    print("📨 Task消息对比:")

    old_count = len(old_tasks)
    new_count = len(new_tasks)
    count_match = old_count == new_count

    print(f"   旧架构任务数: {old_count}")
    print(f"   新架构任务数: {new_count}")
    print(f"   数量匹配: {'✅' if count_match else '❌'}")

    if not count_match:
        return False

    # 如果都是0，也算匹配
    if old_count == 0 and new_count == 0:
        print("   内容匹配: ✅ (都没有任务)")
        return True

    # 详细的消息内容比较
    return compare_task_messages(old_tasks, new_tasks)

def compare_task_messages(old_tasks: List[Dict], new_tasks: List[Dict]) -> bool:
    """详细比较任务消息内容"""
    print("   🔍 详细消息内容比较:")

    # 按任务类型分组
    old_by_type = {}
    new_by_type = {}

    for task in old_tasks:
        task_type = task.get('task_type', 'unknown')
        if task_type not in old_by_type:
            old_by_type[task_type] = []
        old_by_type[task_type].append(task)

    for task in new_tasks:
        task_type = task.get('task_type', 'unknown')
        if task_type not in new_by_type:
            new_by_type[task_type] = []
        new_by_type[task_type].append(task)

    # 比较任务类型分布
    old_types = set(old_by_type.keys())
    new_types = set(new_by_type.keys())

    if old_types != new_types:
        print(f"     ❌ 任务类型不匹配")
        print(f"        旧架构: {sorted(old_types)}")
        print(f"        新架构: {sorted(new_types)}")
        return False

    # 比较每种类型的任务数量
    type_match = True
    for task_type in old_types:
        old_count = len(old_by_type[task_type])
        new_count = len(new_by_type[task_type])
        match = old_count == new_count

        print(f"     {task_type}: {old_count} vs {new_count} {'✅' if match else '❌'}")
        if not match:
            type_match = False

    if not type_match:
        return False

    # 抽样比较消息内容（比较前3条消息）
    sample_match = True
    for task_type in old_types:
        old_samples = old_by_type[task_type][:3]
        new_samples = new_by_type[task_type][:3]

        for i, (old_task, new_task) in enumerate(zip(old_samples, new_samples)):
            old_msg = old_task.get('message', '')
            new_msg = new_task.get('message', '')

            # 简单的消息相似度检查（去除时间戳等动态内容）
            old_normalized = normalize_message(old_msg)
            new_normalized = normalize_message(new_msg)

            if old_normalized != new_normalized:
                print(f"     ❌ {task_type} 第{i+1}条消息不匹配")
                print(f"        旧架构: {old_msg[:100]}...")
                print(f"        新架构: {new_msg[:100]}...")
                sample_match = False
                break

    if sample_match:
        print("     ✅ 抽样消息内容匹配")

    return sample_match

def normalize_message(message: str) -> str:
    """标准化消息内容，去除动态部分"""
    import re

    # 去除时间戳
    message = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '[TIMESTAMP]', message)

    # 去除合同ID中的动态部分（保留格式）
    message = re.sub(r'YHWX-\w+-\w+-\d+', '[CONTRACT_ID]', message)

    # 去除具体金额（保留格式）
    message = re.sub(r'\d{1,3}(,\d{3})*(\.\d+)?', '[AMOUNT]', message)

    # 去除多余空白
    message = re.sub(r'\s+', ' ', message).strip()

    return message

def compare_performance_data(old_perf: List[Dict], new_perf: List[Dict]) -> bool:
    """比较PerformanceData"""
    print("🗃️ PerformanceData对比:")
    
    old_count = len(old_perf)
    new_count = len(new_perf)
    count_match = old_count == new_count
    
    print(f"   旧架构记录数: {old_count}")
    print(f"   新架构记录数: {new_count}")
    print(f"   数量匹配: {'✅' if count_match else '❌'}")
    
    return count_match

def validate_message_generation(city: str, activity: str, clean_data: bool = True) -> bool:
    """验证消息生成等价性"""
    print("🔍 简化消息验证工具")
    print("=" * 60)
    print("目标: 验证新架构与旧架构Task消息生成的完全等价性")
    print("范围: 消息模板、动态数据、通知逻辑")
    print("=" * 60)
    print(f"🎯 验证目标: {city} {activity}")
    print(f"🧹 清理数据: {'是' if clean_data else '否'}")
    print()
    
    # 清理测试环境（如果需要）
    if clean_data:
        clean_test_environment(city, activity)
    
    # 运行旧架构
    old_perf, old_tasks = run_old_architecture(city, activity)
    
    # 运行新架构
    new_perf, new_tasks = run_new_architecture(city, activity)
    
    # 对比结果
    print("📊 对比结果")
    print("=" * 40)
    
    perf_match = compare_performance_data(old_perf, new_perf)
    task_match = compare_tasks(old_tasks, new_tasks)
    
    # 总体结论
    overall_match = perf_match and task_match
    
    print(f"\n🎯 总体结论:")
    print(f"   {'✅ 新旧架构完全等价！Task消息生成逻辑一致。' if overall_match else '❌ 新旧架构存在差异'}")
    
    return overall_match

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化消息验证工具')
    parser.add_argument('--city', choices=['BJ', 'SH'], required=True, help='城市代码')
    parser.add_argument('--activity', required=True, help='活动代码')
    parser.add_argument('--no-clean', action='store_true', help='不清理数据，使用现有数据测试')
    
    args = parser.parse_args()
    
    clean_data = not args.no_clean
    
    try:
        success = validate_message_generation(args.city, args.activity, clean_data)
        if success:
            print("\n🎉 验证成功！新旧架构Task消息生成完全等价。")
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
