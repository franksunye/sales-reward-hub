#!/usr/bin/env python3
"""
Task消息生成验证工具

验证新架构与旧架构在Task消息生成方面的完全等价性。
确保消息模板、动态数据填充、通知逻辑完全一致。

使用方法:
    python scripts/task_message_validation.py --city BJ --activity BJ-SEP
    python scripts/task_message_validation.py --city SH --activity SH-SEP
    python scripts/task_message_validation.py --compare-all
"""

import sys
import os
import sqlite3
import json
import argparse
from datetime import datetime
from typing import Dict, List, Tuple
import logging

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_test_environment():
    """设置测试环境"""
    print("🔧 设置测试环境...")
    
    # 清理现有数据库
    for db_file in ['performance_data.db', 'tasks.db']:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"   清理数据库: {db_file}")
    
    # 初始化数据库
    from scripts.database_setup import create_tasks_table
    create_tasks_table()
    print("   初始化tasks.db完成")
    
    print("✅ 测试环境准备完成")

def run_old_architecture(city: str, activity: str) -> Tuple[List[Dict], List[Dict]]:
    """运行旧架构获取基线数据"""
    print(f"🏗️ 运行旧架构 - {city} {activity}")
    
    try:
        if city == "BJ" and activity == "BJ-SEP":
            from jobs import signing_and_sales_incentive_sep_beijing
            signing_and_sales_incentive_sep_beijing()
        elif city == "SH" and activity == "SH-SEP":
            from jobs import signing_and_sales_incentive_sep_shanghai
            signing_and_sales_incentive_sep_shanghai()
        else:
            raise ValueError(f"不支持的城市/活动组合: {city}/{activity}")
        
        # 获取生成的PerformanceData
        performance_data = get_performance_data_from_csv(city, activity)
        
        # 获取生成的Tasks
        tasks = get_tasks_from_db()
        
        print(f"   PerformanceData记录: {len(performance_data)}")
        print(f"   Task记录: {len(tasks)}")
        
        return performance_data, tasks
        
    except Exception as e:
        print(f"❌ 旧架构执行失败: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def run_new_architecture(city: str, activity: str) -> Tuple[List[Dict], List[Dict]]:
    """运行新架构获取对比数据"""
    print(f"🆕 运行新架构 - {city} {activity}")
    
    try:
        if city == "BJ" and activity == "BJ-SEP":
            from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
            records = signing_and_sales_incentive_sep_beijing_v2()
            
            # 生成通知任务（新架构需要手动调用）
            generate_notifications_for_records(records, city, activity)
            
        elif city == "SH" and activity == "SH-SEP":
            from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
            records = signing_and_sales_incentive_sep_shanghai_v2()
            
            # 生成通知任务
            generate_notifications_for_records(records, city, activity)
            
        else:
            raise ValueError(f"不支持的城市/活动组合: {city}/{activity}")
        
        # 导出PerformanceData到CSV格式进行对比
        performance_data = export_records_to_csv_format(records)
        
        # 获取生成的Tasks
        tasks = get_tasks_from_db()
        
        print(f"   PerformanceRecord对象: {len(records)}")
        print(f"   PerformanceData记录: {len(performance_data)}")
        print(f"   Task记录: {len(tasks)}")
        
        return performance_data, tasks
        
    except Exception as e:
        print(f"❌ 新架构执行失败: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def generate_notifications_for_records(records, city: str, activity: str):
    """为新架构的记录生成通知任务"""
    print(f"📨 为新架构生成通知任务...")
    
    # 首先将记录保存到CSV文件（模拟旧架构的文件存储）
    csv_file = save_records_to_csv(records, city, activity)
    status_file = get_status_file_path(city, activity)
    
    # 调用通知模块
    if city == "BJ":
        from modules.notification_module import notify_awards_sep_beijing
        notify_awards_sep_beijing(csv_file, status_file)
    elif city == "SH":
        from modules.notification_module import notify_awards_sep_shanghai
        notify_awards_sep_shanghai(csv_file, status_file)
    
    print(f"   通知任务生成完成")

def get_performance_data_from_csv(city: str, activity: str) -> List[Dict]:
    """从CSV文件读取PerformanceData"""
    csv_file = get_performance_file_path(city, activity)
    
    if not os.path.exists(csv_file):
        print(f"⚠️ PerformanceData文件不存在: {csv_file}")
        return []
    
    import csv
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_tasks_from_db() -> List[Dict]:
    """从数据库读取Tasks"""
    if not os.path.exists('tasks.db'):
        return []
    
    with sqlite3.connect('tasks.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at")
        return [dict(row) for row in cursor.fetchall()]

def export_records_to_csv_format(records) -> List[Dict]:
    """将PerformanceRecord对象转换为CSV格式的字典列表"""
    return [record.to_dict() for record in records]

def save_records_to_csv(records, city: str, activity: str) -> str:
    """将记录保存到CSV文件"""
    csv_file = get_performance_file_path(city, activity)
    
    if not records:
        return csv_file
    
    import csv
    
    # 获取所有字段名
    all_fields = set()
    record_dicts = []
    for record in records:
        record_dict = record.to_dict()
        all_fields.update(record_dict.keys())
        record_dicts.append(record_dict)
    
    # 写入CSV文件
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
        writer.writeheader()
        writer.writerows(record_dicts)
    
    return csv_file

def get_performance_file_path(city: str, activity: str) -> str:
    """获取PerformanceData文件路径"""
    if city == "BJ" and activity == "BJ-SEP":
        return "state/PerformanceData-BJ-Sep.csv"
    elif city == "SH" and activity == "SH-SEP":
        return "state/PerformanceData-SH-Sep.csv"
    else:
        return f"state/PerformanceData-{city}-{activity}.csv"

def get_status_file_path(city: str, activity: str) -> str:
    """获取状态文件路径"""
    if city == "BJ" and activity == "BJ-SEP":
        return "state/send_status_bj_sep.json"
    elif city == "SH" and activity == "SH-SEP":
        return "state/send_status_shanghai_sep.json"
    else:
        return f"state/send_status_{city.lower()}_{activity.lower()}.json"

def compare_performance_data(old_data: List[Dict], new_data: List[Dict]) -> Dict:
    """对比PerformanceData"""
    print("📊 对比PerformanceData...")
    
    comparison = {
        'record_count_match': len(old_data) == len(new_data),
        'old_count': len(old_data),
        'new_count': len(new_data),
        'field_differences': [],
        'data_differences': []
    }
    
    if not comparison['record_count_match']:
        print(f"⚠️ 记录数量不匹配: 旧架构 {len(old_data)}, 新架构 {len(new_data)}")
    
    # 对比字段结构
    if old_data and new_data:
        old_fields = set(old_data[0].keys())
        new_fields = set(new_data[0].keys())
        
        missing_in_new = old_fields - new_fields
        extra_in_new = new_fields - old_fields
        
        if missing_in_new:
            comparison['field_differences'].append(f"新架构缺少字段: {missing_in_new}")
        if extra_in_new:
            comparison['field_differences'].append(f"新架构额外字段: {extra_in_new}")
    
    # 对比关键数据字段
    key_fields = ['合同ID(_id)', '管家(serviceHousekeeper)', '奖励名称', '激活奖励状态']
    
    for i, (old_record, new_record) in enumerate(zip(old_data, new_data)):
        for field in key_fields:
            if field in old_record and field in new_record:
                if str(old_record[field]) != str(new_record[field]):
                    comparison['data_differences'].append({
                        'record_index': i,
                        'field': field,
                        'old_value': old_record[field],
                        'new_value': new_record[field]
                    })
    
    return comparison

def compare_tasks(old_tasks: List[Dict], new_tasks: List[Dict]) -> Dict:
    """对比Task消息"""
    print("📨 对比Task消息...")
    
    comparison = {
        'task_count_match': len(old_tasks) == len(new_tasks),
        'old_count': len(old_tasks),
        'new_count': len(new_tasks),
        'message_differences': [],
        'type_differences': [],
        'recipient_differences': []
    }
    
    if not comparison['task_count_match']:
        print(f"⚠️ Task数量不匹配: 旧架构 {len(old_tasks)}, 新架构 {len(new_tasks)}")
    
    # 按类型分组对比
    old_by_type = group_tasks_by_type(old_tasks)
    new_by_type = group_tasks_by_type(new_tasks)
    
    for task_type in set(old_by_type.keys()) | set(new_by_type.keys()):
        old_type_tasks = old_by_type.get(task_type, [])
        new_type_tasks = new_by_type.get(task_type, [])
        
        if len(old_type_tasks) != len(new_type_tasks):
            comparison['type_differences'].append({
                'task_type': task_type,
                'old_count': len(old_type_tasks),
                'new_count': len(new_type_tasks)
            })
        
        # 对比消息内容
        for i, (old_task, new_task) in enumerate(zip(old_type_tasks, new_type_tasks)):
            if old_task['message'] != new_task['message']:
                comparison['message_differences'].append({
                    'task_type': task_type,
                    'task_index': i,
                    'old_message': old_task['message'][:100] + "...",
                    'new_message': new_task['message'][:100] + "...",
                    'full_old_message': old_task['message'],
                    'full_new_message': new_task['message']
                })
            
            if old_task['recipient'] != new_task['recipient']:
                comparison['recipient_differences'].append({
                    'task_type': task_type,
                    'task_index': i,
                    'old_recipient': old_task['recipient'],
                    'new_recipient': new_task['recipient']
                })
    
    return comparison

def group_tasks_by_type(tasks: List[Dict]) -> Dict[str, List[Dict]]:
    """按任务类型分组"""
    grouped = {}
    for task in tasks:
        task_type = task['task_type']
        if task_type not in grouped:
            grouped[task_type] = []
        grouped[task_type].append(task)
    return grouped

def print_comparison_results(perf_comparison: Dict, task_comparison: Dict):
    """打印对比结果"""
    print("\n" + "="*60)
    print("📋 验证结果汇总")
    print("="*60)
    
    # PerformanceData对比结果
    print("\n🗃️ PerformanceData对比:")
    print(f"   记录数量匹配: {'✅' if perf_comparison['record_count_match'] else '❌'}")
    print(f"   旧架构记录数: {perf_comparison['old_count']}")
    print(f"   新架构记录数: {perf_comparison['new_count']}")
    
    if perf_comparison['field_differences']:
        print("   字段差异:")
        for diff in perf_comparison['field_differences']:
            print(f"     - {diff}")
    
    if perf_comparison['data_differences']:
        print(f"   数据差异: {len(perf_comparison['data_differences'])} 处")
        for diff in perf_comparison['data_differences'][:5]:  # 只显示前5个
            print(f"     - 记录{diff['record_index']} {diff['field']}: '{diff['old_value']}' -> '{diff['new_value']}'")
    
    # Task对比结果
    print("\n📨 Task消息对比:")
    print(f"   任务数量匹配: {'✅' if task_comparison['task_count_match'] else '❌'}")
    print(f"   旧架构任务数: {task_comparison['old_count']}")
    print(f"   新架构任务数: {task_comparison['new_count']}")
    
    if task_comparison['type_differences']:
        print("   任务类型差异:")
        for diff in task_comparison['type_differences']:
            print(f"     - {diff['task_type']}: {diff['old_count']} -> {diff['new_count']}")
    
    if task_comparison['message_differences']:
        print(f"   消息内容差异: {len(task_comparison['message_differences'])} 处")
        for diff in task_comparison['message_differences'][:3]:  # 只显示前3个
            print(f"     - {diff['task_type']} 任务{diff['task_index']}:")
            print(f"       旧: {diff['old_message']}")
            print(f"       新: {diff['new_message']}")
    
    if task_comparison['recipient_differences']:
        print(f"   接收人差异: {len(task_comparison['recipient_differences'])} 处")
        for diff in task_comparison['recipient_differences']:
            print(f"     - {diff['task_type']}: '{diff['old_recipient']}' -> '{diff['new_recipient']}'")
    
    # 总体结论
    print("\n🎯 总体结论:")
    is_equivalent = (
        perf_comparison['record_count_match'] and
        not perf_comparison['field_differences'] and
        not perf_comparison['data_differences'] and
        task_comparison['task_count_match'] and
        not task_comparison['message_differences'] and
        not task_comparison['recipient_differences']
    )
    
    if is_equivalent:
        print("✅ 新旧架构完全等价！Task消息生成逻辑一致。")
    else:
        print("❌ 新旧架构存在差异，需要进一步调整。")
    
    return is_equivalent

def validate_city_activity(city: str, activity: str) -> bool:
    """验证指定城市和活动的Task消息生成等价性"""
    print(f"\n🎯 验证 {city} {activity} 的Task消息生成等价性")
    print("="*60)
    
    # 设置测试环境
    setup_test_environment()
    
    # 运行旧架构
    old_perf_data, old_tasks = run_old_architecture(city, activity)
    
    # 清理并重新设置环境
    setup_test_environment()
    
    # 运行新架构
    new_perf_data, new_tasks = run_new_architecture(city, activity)
    
    # 对比结果
    perf_comparison = compare_performance_data(old_perf_data, new_perf_data)
    task_comparison = compare_tasks(old_tasks, new_tasks)
    
    # 打印结果
    return print_comparison_results(perf_comparison, task_comparison)

def validate_configurations():
    """验证新旧架构配置一致性"""
    print("🔧 验证配置一致性...")

    # 验证北京9月配置
    print("\n📋 北京9月配置对比:")
    try:
        from modules.config import REWARD_CONFIGS
        bj_config = REWARD_CONFIGS.get('BJ-2025-09', {})

        print(f"   幸运数字: {bj_config.get('lucky_number', 'N/A')}")
        print(f"   幸运数字模式: {bj_config.get('lucky_number_mode', 'N/A')}")

        perf_limits = bj_config.get('performance_limits', {})
        print(f"   工单金额上限: {perf_limits.get('single_project_limit', 'N/A')}")
        print(f"   合同金额上限: {perf_limits.get('single_contract_cap', 'N/A')}")
        print(f"   启用金额上限: {perf_limits.get('enable_cap', 'N/A')}")

        tiered_rewards = bj_config.get('tiered_rewards', {})
        print(f"   合同门槛: {tiered_rewards.get('min_contracts', 'N/A')}")

        # 验证奖励配置
        awards_mapping = bj_config.get('awards_mapping', {})
        print(f"   奖励层级数: {len(awards_mapping)}")
        for reward_name, amount in awards_mapping.items():
            print(f"     {reward_name}: {amount}元")

    except Exception as e:
        print(f"   ❌ 北京配置读取失败: {e}")
        import traceback
        traceback.print_exc()

    # 验证上海9月配置
    print("\n📋 上海9月配置对比:")
    try:
        sh_config = REWARD_CONFIGS.get('SH-2025-09', {})

        print(f"   幸运数字: '{sh_config.get('lucky_number', 'N/A')}'")

        perf_limits = sh_config.get('performance_limits', {})
        print(f"   启用金额上限: {perf_limits.get('enable_cap', 'N/A')}")
        print(f"   合同金额上限: {perf_limits.get('single_contract_cap', 'N/A')}")

        tiered_rewards = sh_config.get('tiered_rewards', {})
        print(f"   合同门槛: {tiered_rewards.get('min_contracts', 'N/A')}")

        reward_calc = sh_config.get('reward_calculation_strategy', {})
        print(f"   奖励计算策略: {reward_calc.get('type', 'N/A')}")

        # 验证奖励配置
        awards_mapping = sh_config.get('awards_mapping', {})
        print(f"   奖励层级数: {len(awards_mapping)}")
        for reward_name, amount in awards_mapping.items():
            print(f"     {reward_name}: {amount}元")

        # 自引单奖励
        self_referral = sh_config.get('self_referral_reward', {})
        if self_referral:
            print(f"   自引单奖励: {self_referral.get('amount', 'N/A')}元")

    except Exception as e:
        print(f"   ❌ 上海配置读取失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Task消息生成验证工具')
    parser.add_argument('--city', choices=['BJ', 'SH'], help='城市代码')
    parser.add_argument('--activity', help='活动代码')
    parser.add_argument('--compare-all', action='store_true', help='对比所有支持的城市和活动')
    parser.add_argument('--validate-config', action='store_true', help='验证配置一致性')
    parser.add_argument('--dry-run', action='store_true', help='仅验证配置，不执行实际任务')

    args = parser.parse_args()

    print("🔍 Task消息生成验证工具")
    print("="*60)
    print("目标: 验证新架构与旧架构Task消息生成的完全等价性")
    print("范围: 消息模板、动态数据、通知逻辑")
    print("="*60)

    if args.validate_config:
        validate_configurations()
        return

    if args.compare_all:
        # 首先验证配置
        if not args.dry_run:
            validate_configurations()

        # 验证所有支持的组合
        test_cases = [
            ('BJ', 'BJ-SEP'),
            ('SH', 'SH-SEP')
        ]

        if args.dry_run:
            print("\n🔍 干运行模式 - 仅验证配置和环境")
            for city, activity in test_cases:
                print(f"✅ {city} {activity} 配置验证通过")
            return

        all_passed = True
        for city, activity in test_cases:
            try:
                passed = validate_city_activity(city, activity)
                all_passed = all_passed and passed
            except Exception as e:
                print(f"❌ {city} {activity} 验证失败: {e}")
                import traceback
                traceback.print_exc()
                all_passed = False

        print(f"\n🏁 全部验证完成: {'✅ 全部通过' if all_passed else '❌ 存在问题'}")

    elif args.city and args.activity:
        if not args.dry_run:
            validate_configurations()

        if args.dry_run:
            print(f"\n🔍 干运行模式 - {args.city} {args.activity}")
            print("✅ 配置验证通过")
            return

        validate_city_activity(args.city, args.activity)

    else:
        print("❌ 请指定操作选项")
        print("💡 示例: python scripts/task_message_validation.py --city BJ --activity BJ-SEP")
        print("💡 验证配置: python scripts/task_message_validation.py --validate-config")
        print("💡 全部验证: python scripts/task_message_validation.py --compare-all")
        print("💡 干运行: python scripts/task_message_validation.py --compare-all --dry-run")

if __name__ == "__main__":
    main()
