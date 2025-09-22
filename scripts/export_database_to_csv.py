#!/usr/bin/env python3
"""
数据库导出工具

从SQLite数据库导出指定活动的数据到CSV文件。
用于替代自动生成CSV文件的功能，提供按需导出。
"""

import sys
import os
import sqlite3
import csv
import json
from datetime import datetime
import argparse

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def export_activity_to_csv(db_path: str, activity_code: str, output_path: str = None):
    """从数据库导出指定活动的数据到CSV文件"""
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None
    
    # 生成输出文件名
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"performance_data_{activity_code}_{timestamp}.csv"
    
    try:
        with sqlite3.connect(db_path) as conn:
            # 查询指定活动的数据
            cursor = conn.execute("""
                SELECT * FROM performance_data 
                WHERE activity_code = ? 
                ORDER BY created_at
            """, (activity_code,))
            
            rows = cursor.fetchall()
            
            if not rows:
                print(f"⚠️ 活动 {activity_code} 没有找到数据")
                return None
            
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            # 写入CSV文件
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                writer.writerow(column_names)
                
                # 写入数据行
                for row in rows:
                    # 处理extensions字段（JSON格式）
                    processed_row = []
                    for i, value in enumerate(row):
                        if column_names[i] == 'extensions' and value:
                            try:
                                # 解析JSON并展开字段
                                extensions = json.loads(value)
                                processed_row.append(json.dumps(extensions, ensure_ascii=False))
                            except:
                                processed_row.append(value)
                        else:
                            processed_row.append(value)
                    
                    writer.writerow(processed_row)
            
            print(f"✅ 导出完成: {output_path}")
            print(f"   活动代码: {activity_code}")
            print(f"   记录数量: {len(rows)}")
            print(f"   字段数量: {len(column_names)}")
            
            return output_path
            
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return None

def export_activity_to_compatible_csv(db_path: str, activity_code: str, output_path: str = None):
    """导出兼容旧格式的CSV文件"""
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None
    
    # 生成输出文件名
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"performance_data_{activity_code}_{timestamp}.csv"
    
    try:
        with sqlite3.connect(db_path) as conn:
            # 查询数据并重构为兼容格式
            cursor = conn.execute("""
                SELECT 
                    activity_code as '活动编号',
                    contract_id as '合同ID(_id)',
                    housekeeper as '管家(serviceHousekeeper)',
                    service_provider as '服务商(orgName)',
                    contract_amount as '合同金额(adjustRefundMoney)',
                    performance_amount as '计入业绩金额',
                    reward_types as '奖励类型',
                    reward_names as '奖励名称',
                    is_historical as '是否历史合同',
                    extensions,
                    created_at as '创建时间'
                FROM performance_data 
                WHERE activity_code = ? 
                ORDER BY created_at
            """, (activity_code,))
            
            rows = cursor.fetchall()
            
            if not rows:
                print(f"⚠️ 活动 {activity_code} 没有找到数据")
                return None
            
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            # 写入CSV文件
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=[])
                
                # 处理第一行数据以确定所有字段
                all_fieldnames = set()
                processed_rows = []
                
                for row in rows:
                    row_dict = dict(zip(column_names, row))
                    
                    # 处理extensions字段
                    if row_dict.get('extensions'):
                        try:
                            extensions = json.loads(row_dict['extensions'])
                            row_dict.update(extensions)
                        except:
                            pass
                    
                    # 移除extensions字段
                    row_dict.pop('extensions', None)
                    
                    # 处理布尔值
                    if '是否历史合同' in row_dict:
                        row_dict['是否历史合同'] = 'Y' if row_dict['是否历史合同'] else 'N'
                    
                    all_fieldnames.update(row_dict.keys())
                    processed_rows.append(row_dict)
                
                # 重新创建writer with所有字段
                writer = csv.DictWriter(csvfile, fieldnames=sorted(all_fieldnames))
                writer.writeheader()
                writer.writerows(processed_rows)
            
            print(f"✅ 兼容格式导出完成: {output_path}")
            print(f"   活动代码: {activity_code}")
            print(f"   记录数量: {len(rows)}")
            print(f"   字段数量: {len(all_fieldnames)}")
            
            return output_path
            
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return None

def list_activities(db_path: str):
    """列出数据库中的所有活动"""
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT activity_code, COUNT(*) as record_count, 
                       MIN(created_at) as first_record, 
                       MAX(created_at) as last_record
                FROM performance_data 
                GROUP BY activity_code 
                ORDER BY activity_code
            """)
            
            activities = cursor.fetchall()
            
            if not activities:
                print("📊 数据库中没有活动数据")
                return
            
            print("📊 数据库中的活动列表:")
            print("-" * 60)
            print(f"{'活动代码':<15} {'记录数':<8} {'首次记录':<20} {'最新记录':<20}")
            print("-" * 60)
            
            for activity_code, count, first, last in activities:
                print(f"{activity_code:<15} {count:<8} {first:<20} {last:<20}")
            
            print("-" * 60)
            print(f"总计: {len(activities)} 个活动")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库导出工具')
    parser.add_argument('--db', default='performance_data.db', help='数据库文件路径')
    parser.add_argument('--activity', help='活动代码 (如: BJ-SEP)')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--list', action='store_true', help='列出所有活动')
    parser.add_argument('--compatible', action='store_true', help='导出兼容旧格式的CSV')
    
    args = parser.parse_args()
    
    print("🔍 数据库导出工具")
    print("=" * 50)
    
    if args.list:
        list_activities(args.db)
        return
    
    if not args.activity:
        print("❌ 请指定活动代码 (使用 --activity)")
        print("💡 使用 --list 查看所有可用活动")
        return
    
    if args.compatible:
        result = export_activity_to_compatible_csv(args.db, args.activity, args.output)
    else:
        result = export_activity_to_csv(args.db, args.activity, args.output)
    
    if result:
        print(f"\n💡 使用方法:")
        print(f"   查看文件: head -5 {result}")
        print(f"   记录数量: wc -l {result}")
        print(f"   对比验证: 可与旧架构输出进行对比")

if __name__ == "__main__":
    main()
