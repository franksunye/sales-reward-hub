#!/usr/bin/env python3
"""
消息内容分析工具

深度分析新旧架构生成的Task消息内容，确保：
1. 消息模板完全一致
2. 动态数据填充准确
3. 奖励计算逻辑正确
4. 通知触发条件一致

使用方法:
    python scripts/message_content_analyzer.py --analyze-messages
    python scripts/message_content_analyzer.py --extract-templates
    python scripts/message_content_analyzer.py --compare-rewards
"""

import sys
import os
import sqlite3
import json
import re
import argparse
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import difflib

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def extract_message_template(message: str) -> str:
    """提取消息模板，将动态数据替换为占位符"""
    # 替换常见的动态数据模式
    patterns = [
        (r'恭喜 .+ 签约合同', '恭喜 {管家} 签约合同'),
        (r'签约合同 [A-Z0-9\-]+', '签约合同 {合同编号}'),
        (r'第 \d+ 单', '第 {序号} 单'),
        (r'累计签约第 \d+ 单', '累计签约第 {累计序号} 单'),
        (r'累计签约 [\d,.]+ 元', '累计签约 {累计金额} 元'),
        (r'累计计入业绩 [\d,.]+ 元', '累计计入业绩 {累计业绩} 元'),
        (r'平台单累计 \d+ 单', '平台单累计 {平台单数} 单'),
        (r'自引单累计 \d+ 单', '自引单累计 {自引单数} 单'),
        (r'平台单累计 [\d,.]+ 元', '平台单累计 {平台单金额} 元'),
        (r'自引单累计 [\d,.]+ 元', '自引单累计 {自引单金额} 元'),
        (r'个人转化率 \d+%', '个人转化率 {转化率}'),
        (r'距离 .+ 还需 [\d,.]+ 元', '距离 {下一奖励} 还需 {差额} 元'),
        (r'获得签约奖励\d+元', '获得签约奖励{奖励金额}元'),
        (r'奖励金额 \d+ 元', '奖励金额 {奖励金额} 元'),
        (r'直升至 \d+ 元', '直升至 {翻倍金额} 元'),
    ]
    
    template = message
    for pattern, replacement in patterns:
        template = re.sub(pattern, replacement, template)
    
    return template

def extract_dynamic_data(message: str) -> Dict[str, str]:
    """从消息中提取动态数据"""
    data = {}
    
    # 提取各种动态数据
    patterns = {
        '管家': r'恭喜 (.+?) 签约合同',
        '合同编号': r'签约合同 ([A-Z0-9\-]+)',
        '全局序号': r'平台累计签约第 (\d+) 单',
        '个人序号': r'个人累计签约第 (\d+) 单',
        '累计金额': r'累计签约 ([\d,\.]+) 元',
        '累计业绩': r'累计计入业绩 ([\d,\.]+) 元',
        '平台单数': r'平台单累计 (\d+) 单',
        '自引单数': r'自引单累计 (\d+) 单',
        '平台单金额': r'平台单累计 ([\d,\.]+) 元',
        '自引单金额': r'自引单累计 ([\d,\.]+) 元',
        '转化率': r'个人转化率 (\d+%)',
        '奖励金额': r'获得签约奖励(\d+)元',
        '下一奖励': r'距离 (.+?) 还需',
        '差额': r'还需 ([\d,\.]+) 元',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, message)
        if match:
            data[key] = match.group(1)
    
    return data

def analyze_message_structure(tasks: List[Dict]) -> Dict:
    """分析消息结构"""
    analysis = {
        'total_tasks': len(tasks),
        'task_types': defaultdict(int),
        'message_templates': defaultdict(int),
        'recipients': defaultdict(int),
        'dynamic_data_fields': set(),
        'reward_messages': [],
        'group_messages': [],
    }
    
    for task in tasks:
        task_type = task['task_type']
        recipient = task['recipient']
        message = task['message']
        
        analysis['task_types'][task_type] += 1
        analysis['recipients'][recipient] += 1
        
        # 提取消息模板
        template = extract_message_template(message)
        analysis['message_templates'][template] += 1
        
        # 提取动态数据字段
        dynamic_data = extract_dynamic_data(message)
        analysis['dynamic_data_fields'].update(dynamic_data.keys())
        
        # 分类消息
        if task_type == 'send_wechat_message':
            analysis['reward_messages'].append({
                'recipient': recipient,
                'message': message,
                'template': template,
                'dynamic_data': dynamic_data
            })
        elif task_type == 'send_wecom_message':
            analysis['group_messages'].append({
                'recipient': recipient,
                'message': message,
                'template': template,
                'dynamic_data': dynamic_data
            })
    
    return analysis

def compare_message_structures(old_analysis: Dict, new_analysis: Dict) -> Dict:
    """对比消息结构"""
    comparison = {
        'task_count_diff': new_analysis['total_tasks'] - old_analysis['total_tasks'],
        'task_type_diffs': {},
        'template_diffs': {},
        'recipient_diffs': {},
        'dynamic_field_diffs': {},
        'detailed_message_diffs': []
    }
    
    # 对比任务类型分布
    all_task_types = set(old_analysis['task_types'].keys()) | set(new_analysis['task_types'].keys())
    for task_type in all_task_types:
        old_count = old_analysis['task_types'].get(task_type, 0)
        new_count = new_analysis['task_types'].get(task_type, 0)
        if old_count != new_count:
            comparison['task_type_diffs'][task_type] = {
                'old': old_count,
                'new': new_count,
                'diff': new_count - old_count
            }
    
    # 对比消息模板
    all_templates = set(old_analysis['message_templates'].keys()) | set(new_analysis['message_templates'].keys())
    for template in all_templates:
        old_count = old_analysis['message_templates'].get(template, 0)
        new_count = new_analysis['message_templates'].get(template, 0)
        if old_count != new_count:
            comparison['template_diffs'][template[:100] + "..."] = {
                'old': old_count,
                'new': new_count,
                'diff': new_count - old_count
            }
    
    # 对比接收人
    all_recipients = set(old_analysis['recipients'].keys()) | set(new_analysis['recipients'].keys())
    for recipient in all_recipients:
        old_count = old_analysis['recipients'].get(recipient, 0)
        new_count = new_analysis['recipients'].get(recipient, 0)
        if old_count != new_count:
            comparison['recipient_diffs'][recipient] = {
                'old': old_count,
                'new': new_count,
                'diff': new_count - old_count
            }
    
    # 对比动态数据字段
    old_fields = old_analysis['dynamic_data_fields']
    new_fields = new_analysis['dynamic_data_fields']
    comparison['dynamic_field_diffs'] = {
        'missing_in_new': old_fields - new_fields,
        'extra_in_new': new_fields - old_fields,
        'common_fields': old_fields & new_fields
    }
    
    return comparison

def compare_reward_messages(old_rewards: List[Dict], new_rewards: List[Dict]) -> List[Dict]:
    """详细对比奖励消息"""
    differences = []
    
    # 按接收人分组
    old_by_recipient = defaultdict(list)
    new_by_recipient = defaultdict(list)
    
    for reward in old_rewards:
        old_by_recipient[reward['recipient']].append(reward)
    
    for reward in new_rewards:
        new_by_recipient[reward['recipient']].append(reward)
    
    # 对比每个接收人的消息
    all_recipients = set(old_by_recipient.keys()) | set(new_by_recipient.keys())
    
    for recipient in all_recipients:
        old_msgs = old_by_recipient.get(recipient, [])
        new_msgs = new_by_recipient.get(recipient, [])
        
        if len(old_msgs) != len(new_msgs):
            differences.append({
                'type': 'count_mismatch',
                'recipient': recipient,
                'old_count': len(old_msgs),
                'new_count': len(new_msgs)
            })
        
        # 对比消息内容
        for i, (old_msg, new_msg) in enumerate(zip(old_msgs, new_msgs)):
            if old_msg['message'] != new_msg['message']:
                differences.append({
                    'type': 'content_mismatch',
                    'recipient': recipient,
                    'message_index': i,
                    'old_message': old_msg['message'],
                    'new_message': new_msg['message'],
                    'old_template': old_msg['template'],
                    'new_template': new_msg['template'],
                    'old_dynamic_data': old_msg['dynamic_data'],
                    'new_dynamic_data': new_msg['dynamic_data']
                })
    
    return differences

def compare_group_messages(old_groups: List[Dict], new_groups: List[Dict]) -> List[Dict]:
    """详细对比群组消息"""
    differences = []
    
    # 按接收人分组
    old_by_recipient = defaultdict(list)
    new_by_recipient = defaultdict(list)
    
    for group in old_groups:
        old_by_recipient[group['recipient']].append(group)
    
    for group in new_groups:
        new_by_recipient[group['recipient']].append(group)
    
    # 对比每个群组的消息
    all_recipients = set(old_by_recipient.keys()) | set(new_by_recipient.keys())
    
    for recipient in all_recipients:
        old_msgs = old_by_recipient.get(recipient, [])
        new_msgs = new_by_recipient.get(recipient, [])
        
        if len(old_msgs) != len(new_msgs):
            differences.append({
                'type': 'count_mismatch',
                'recipient': recipient,
                'old_count': len(old_msgs),
                'new_count': len(new_msgs)
            })
        
        # 对比消息内容
        for i, (old_msg, new_msg) in enumerate(zip(old_msgs, new_msgs)):
            if old_msg['message'] != new_msg['message']:
                differences.append({
                    'type': 'content_mismatch',
                    'recipient': recipient,
                    'message_index': i,
                    'old_message': old_msg['message'],
                    'new_message': new_msg['message'],
                    'old_template': old_msg['template'],
                    'new_template': new_msg['template'],
                    'old_dynamic_data': old_msg['dynamic_data'],
                    'new_dynamic_data': new_msg['dynamic_data']
                })
    
    return differences

def print_detailed_analysis(old_analysis: Dict, new_analysis: Dict, comparison: Dict):
    """打印详细分析结果"""
    print("\n" + "="*80)
    print("📊 消息内容深度分析")
    print("="*80)
    
    # 基础统计
    print(f"\n📈 基础统计:")
    print(f"   旧架构任务总数: {old_analysis['total_tasks']}")
    print(f"   新架构任务总数: {new_analysis['total_tasks']}")
    print(f"   差异: {comparison['task_count_diff']:+d}")
    
    # 任务类型分布
    print(f"\n📋 任务类型分布:")
    for task_type, counts in comparison['task_type_diffs'].items():
        print(f"   {task_type}: {counts['old']} -> {counts['new']} ({counts['diff']:+d})")
    
    # 接收人分布
    if comparison['recipient_diffs']:
        print(f"\n👥 接收人分布差异:")
        for recipient, counts in comparison['recipient_diffs'].items():
            print(f"   {recipient}: {counts['old']} -> {counts['new']} ({counts['diff']:+d})")
    
    # 动态数据字段
    print(f"\n🔧 动态数据字段:")
    field_diffs = comparison['dynamic_field_diffs']
    print(f"   共同字段: {len(field_diffs['common_fields'])}")
    if field_diffs['missing_in_new']:
        print(f"   新架构缺少: {field_diffs['missing_in_new']}")
    if field_diffs['extra_in_new']:
        print(f"   新架构额外: {field_diffs['extra_in_new']}")
    
    # 消息模板差异
    if comparison['template_diffs']:
        print(f"\n📝 消息模板差异:")
        for template, counts in list(comparison['template_diffs'].items())[:5]:
            print(f"   模板: {template}")
            print(f"     旧: {counts['old']}, 新: {counts['new']}, 差异: {counts['diff']:+d}")

def analyze_tasks_from_db(db_path: str = 'tasks.db') -> Dict:
    """从数据库分析任务"""
    if not os.path.exists(db_path):
        print(f"⚠️ 数据库文件不存在: {db_path}")
        return {}
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at")
        tasks = [dict(row) for row in cursor.fetchall()]
    
    return analyze_message_structure(tasks)

def save_analysis_report(analysis: Dict, filename: str):
    """保存分析报告"""
    # 转换set为list以便JSON序列化
    serializable_analysis = {}
    for key, value in analysis.items():
        if isinstance(value, set):
            serializable_analysis[key] = list(value)
        elif isinstance(value, defaultdict):
            serializable_analysis[key] = dict(value)
        else:
            serializable_analysis[key] = value
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"📄 分析报告已保存: {filename}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='消息内容分析工具')
    parser.add_argument('--analyze-messages', action='store_true', help='分析当前数据库中的消息')
    parser.add_argument('--extract-templates', action='store_true', help='提取消息模板')
    parser.add_argument('--compare-rewards', action='store_true', help='对比奖励消息')
    parser.add_argument('--db', default='tasks.db', help='数据库文件路径')
    parser.add_argument('--output', help='输出报告文件路径')
    
    args = parser.parse_args()
    
    print("🔍 消息内容分析工具")
    print("="*60)
    
    if args.analyze_messages:
        print("📊 分析消息结构...")
        analysis = analyze_tasks_from_db(args.db)
        
        if analysis:
            print(f"\n📈 分析结果:")
            print(f"   总任务数: {analysis['total_tasks']}")
            print(f"   任务类型: {dict(analysis['task_types'])}")
            print(f"   接收人: {dict(analysis['recipients'])}")
            print(f"   消息模板数: {len(analysis['message_templates'])}")
            print(f"   动态数据字段: {len(analysis['dynamic_data_fields'])}")
            print(f"   奖励消息数: {len(analysis['reward_messages'])}")
            print(f"   群组消息数: {len(analysis['group_messages'])}")
            
            if args.output:
                save_analysis_report(analysis, args.output)
        else:
            print("❌ 没有找到任务数据")
    
    elif args.extract_templates:
        print("📝 提取消息模板...")
        analysis = analyze_tasks_from_db(args.db)
        
        if analysis:
            print(f"\n📋 发现的消息模板:")
            for i, (template, count) in enumerate(analysis['message_templates'].items(), 1):
                print(f"\n模板 {i} (使用 {count} 次):")
                print("-" * 40)
                print(template)
        else:
            print("❌ 没有找到任务数据")
    
    else:
        print("❌ 请指定操作选项")
        print("💡 使用 --analyze-messages 分析消息结构")
        print("💡 使用 --extract-templates 提取消息模板")

if __name__ == "__main__":
    main()
