#!/usr/bin/env python3
"""
简化的消息内容对比脚本
直接对比新旧架构生成的消息内容
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple
import difflib

def extract_contract_info_from_message(message: str) -> Dict:
    """从消息中提取合同信息用于匹配"""
    info = {'housekeeper': '', 'contract_num': '', 'message_type': ''}
    
    try:
        if '🧨🧨🧨 签约喜报 🧨🧨🧨' in message:
            # 群通知消息
            info['message_type'] = 'group'
            lines = message.split('\n')
            for line in lines:
                if '恭喜' in line and '签约合同' in line:
                    # 提取管家姓名和合同编号
                    parts = line.split('签约合同')
                    if len(parts) >= 2:
                        housekeeper_part = parts[0].replace('恭喜', '').strip()
                        contract_part = parts[1].split('并完成')[0].strip()
                        info['housekeeper'] = housekeeper_part
                        info['contract_num'] = contract_part
                    break
        else:
            # 奖励通知消息
            info['message_type'] = 'reward'
            # 从消息中提取管家姓名和合同编号
            if '签约合同' in message:
                parts = message.split('签约合同')
                if len(parts) >= 2:
                    housekeeper_part = parts[0].strip()
                    contract_part = parts[1].split('）')[0] + '）'
                    info['housekeeper'] = housekeeper_part
                    info['contract_num'] = contract_part
    
    except Exception as e:
        print(f"提取合同信息失败: {e}")
    
    return info

def extract_tasks():
    """提取新旧架构的Task记录"""
    print("📊 提取Task记录...")
    
    with sqlite3.connect('tasks.db') as conn:
        conn.row_factory = sqlite3.Row
        
        # 提取旧架构Task记录（20-30分钟前）
        cursor = conn.execute("""
            SELECT * FROM tasks 
            WHERE created_at >= datetime('now', '-30 minutes')
            AND created_at < datetime('now', '-15 minutes')
            ORDER BY created_at
        """)
        old_tasks = [dict(row) for row in cursor.fetchall()]
        
        # 提取新架构Task记录（最近10分钟）
        cursor = conn.execute("""
            SELECT * FROM tasks 
            WHERE created_at >= datetime('now', '-10 minutes')
            AND status != 'new_architecture_backup'
            ORDER BY created_at
        """)
        new_tasks = [dict(row) for row in cursor.fetchall()]
    
    print(f"   旧架构Task记录: {len(old_tasks)} 条")
    print(f"   新架构Task记录: {len(new_tasks)} 条")
    
    return old_tasks, new_tasks

def match_tasks(old_tasks: List[Dict], new_tasks: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """匹配新旧架构的Task记录"""
    print("🔗 匹配Task记录...")
    
    matched_pairs = []
    old_task_map = {}
    
    # 为旧架构Task建立索引
    for task in old_tasks:
        info = extract_contract_info_from_message(task['message'])
        key = f"{info['housekeeper']}_{info['contract_num']}_{info['message_type']}"
        if key not in old_task_map:
            old_task_map[key] = task
    
    # 匹配新架构Task
    matched_keys = set()
    for new_task in new_tasks:
        info = extract_contract_info_from_message(new_task['message'])
        key = f"{info['housekeeper']}_{info['contract_num']}_{info['message_type']}"
        
        if key in old_task_map and key not in matched_keys:
            matched_pairs.append((old_task_map[key], new_task))
            matched_keys.add(key)
    
    print(f"   成功匹配: {len(matched_pairs)} 对")
    print(f"   未匹配的旧架构记录: {len(old_task_map) - len(matched_pairs)} 条")
    print(f"   未匹配的新架构记录: {len(new_tasks) - len(matched_pairs)} 条")
    
    return matched_pairs

def compare_messages(matched_pairs: List[Tuple[Dict, Dict]]):
    """详细对比消息内容"""
    print("🔍 详细对比消息内容...")
    
    identical_count = 0
    different_count = 0
    differences = []
    
    for i, (old_task, new_task) in enumerate(matched_pairs):
        old_msg = old_task['message'].strip()
        new_msg = new_task['message'].strip()
        
        if old_msg == new_msg:
            identical_count += 1
        else:
            different_count += 1
            
            # 记录差异
            diff = {
                'pair_index': i + 1,
                'task_type': old_task['task_type'],
                'recipient': old_task['recipient'],
                'old_message': old_msg,
                'new_message': new_msg,
                'contract_info': extract_contract_info_from_message(old_msg)
            }
            differences.append(diff)
            
            # 显示前几个差异
            if len(differences) <= 5:
                print(f"\n❌ 差异 #{len(differences)}:")
                print(f"   任务类型: {diff['task_type']}")
                print(f"   接收者: {diff['recipient']}")
                print(f"   合同信息: {diff['contract_info']}")
                print(f"   旧架构消息: {old_msg[:100]}...")
                print(f"   新架构消息: {new_msg[:100]}...")
    
    print(f"\n📊 对比结果:")
    print(f"   完全相同: {identical_count} 条")
    print(f"   存在差异: {different_count} 条")
    
    if matched_pairs:
        accuracy_rate = identical_count / len(matched_pairs) * 100
        print(f"   准确率: {accuracy_rate:.2f}%")
    
    return identical_count, different_count, differences

def generate_sample_report(differences: List[Dict]):
    """生成样本对比报告"""
    if not differences:
        print("✅ 所有消息内容完全相同！")
        return
    
    print(f"\n📋 差异样本报告（前5个）:")
    print("=" * 80)
    
    for i, diff in enumerate(differences[:5]):
        print(f"\n差异 #{i+1}:")
        print(f"任务类型: {diff['task_type']}")
        print(f"接收者: {diff['recipient']}")
        print(f"合同信息: {diff['contract_info']}")
        print(f"\n旧架构消息:")
        print(diff['old_message'])
        print(f"\n新架构消息:")
        print(diff['new_message'])
        print("-" * 80)

def main():
    """主函数"""
    print("🎯 简化消息内容对比测试")
    print("=" * 50)
    
    try:
        # 提取Task记录
        old_tasks, new_tasks = extract_tasks()
        
        if not old_tasks:
            print("❌ 没有找到旧架构Task记录")
            return False
        
        if not new_tasks:
            print("❌ 没有找到新架构Task记录")
            return False
        
        # 匹配Task记录
        matched_pairs = match_tasks(old_tasks, new_tasks)
        
        if not matched_pairs:
            print("❌ 没有找到匹配的Task记录对")
            return False
        
        # 对比消息内容
        identical_count, different_count, differences = compare_messages(matched_pairs)
        
        # 生成报告
        generate_sample_report(differences)
        
        # 显示结果摘要
        print(f"\n🎉 对比测试完成!")
        if different_count == 0:
            print("🎊 恭喜！新旧架构消息内容完全相同！")
        else:
            print(f"⚠️  发现 {different_count} 处差异")
        
        return True
        
    except Exception as e:
        print(f"❌ 对比测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
