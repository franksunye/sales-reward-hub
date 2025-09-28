#!/usr/bin/env python3
"""
检查数据库结构和余金凤的数据
"""

import sqlite3
import json

def main():
    # 连接数据库
    conn = sqlite3.connect('performance_data.db')
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("PRAGMA table_info(performance_data)")
    columns = cursor.fetchall()
    print("数据库表结构:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    print()
    
    # 查询余金凤的所有记录
    cursor.execute('''
        SELECT * FROM performance_data 
        WHERE housekeeper LIKE '%余金凤%' 
        ORDER BY contract_id
    ''')
    
    records = cursor.fetchall()
    print(f'找到余金凤的记录数量: {len(records)}')
    print()
    
    # 获取列名
    column_names = [description[0] for description in cursor.description]
    
    for i, record in enumerate(records):
        print(f'记录 {i+1}:')
        record_dict = dict(zip(column_names, record))
        
        # 显示关键字段
        print(f'  管家: {record_dict.get("housekeeper", "N/A")}')
        print(f'  合同ID: {record_dict.get("contract_id", "N/A")}')
        print(f'  订单类型: {record_dict.get("order_type", "N/A")}')
        print(f'  活动代码: {record_dict.get("activity_code", "N/A")}')
        print(f'  合同金额: {record_dict.get("contract_amount", "N/A")}')
        
        # 检查是否有奖励相关字段
        reward_fields = [k for k in record_dict.keys() if 'reward' in k.lower()]
        if reward_fields:
            for field in reward_fields:
                print(f'  {field}: {record_dict.get(field, "N/A")}')
        
        # 解析raw_data中的sourceType
        raw_data = record_dict.get('raw_data')
        if raw_data:
            try:
                raw_dict = json.loads(raw_data)
                source_type = raw_dict.get('工单类型(sourceType)', 'N/A')
                print(f'  sourceType: {source_type}')
                
                # 检查是否有奖励信息
                reward_info = raw_dict.get('奖励信息', 'N/A')
                if reward_info and reward_info != 'N/A':
                    print(f'  奖励信息: {reward_info}')
                    
            except Exception as e:
                print(f'  raw_data解析失败: {e}')
        
        print()
    
    # 特别查找GD20250900205这个合同
    print("=" * 50)
    print("特别查找合同 GD20250900205:")
    cursor.execute('''
        SELECT * FROM performance_data 
        WHERE contract_id = 'GD20250900205'
    ''')
    
    target_records = cursor.fetchall()
    if target_records:
        for record in target_records:
            record_dict = dict(zip(column_names, record))
            print("找到目标合同:")
            for key, value in record_dict.items():
                if value is not None and value != '':
                    print(f"  {key}: {value}")
            
            # 特别解析raw_data
            raw_data = record_dict.get('raw_data')
            if raw_data:
                try:
                    raw_dict = json.loads(raw_data)
                    print("\nraw_data详细信息:")
                    for key, value in raw_dict.items():
                        if '奖励' in key or 'reward' in key.lower() or 'sourceType' in key:
                            print(f"  {key}: {value}")
                except Exception as e:
                    print(f"  raw_data解析失败: {e}")
    else:
        print("未找到合同 GD20250900205")
    
    conn.close()

if __name__ == "__main__":
    main()
