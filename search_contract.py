#!/usr/bin/env python3
"""
搜索GD20250900205合同
"""

import sqlite3
import json

def main():
    # 连接数据库
    conn = sqlite3.connect('performance_data.db')
    cursor = conn.cursor()
    
    # 搜索包含GD20250900205的所有记录
    cursor.execute('''
        SELECT * FROM performance_data 
        WHERE contract_id LIKE '%GD20250900205%' 
           OR extensions LIKE '%GD20250900205%'
           OR remarks LIKE '%GD20250900205%'
    ''')
    
    records = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    print(f'搜索GD20250900205，找到记录数量: {len(records)}')
    
    if records:
        for i, record in enumerate(records):
            record_dict = dict(zip(column_names, record))
            print(f'\n记录 {i+1}:')
            for key, value in record_dict.items():
                if value is not None and value != '':
                    print(f'  {key}: {value}')
    
    # 搜索extensions字段中包含GD20250900205的记录
    print("\n" + "="*50)
    print("搜索extensions字段中的GD20250900205:")
    
    cursor.execute('SELECT * FROM performance_data WHERE extensions IS NOT NULL')
    all_records = cursor.fetchall()
    
    found_in_extensions = []
    for record in all_records:
        record_dict = dict(zip(column_names, record))
        extensions = record_dict.get('extensions')
        if extensions:
            try:
                ext_data = json.loads(extensions)
                # 递归搜索所有字段
                if search_in_dict(ext_data, 'GD20250900205'):
                    found_in_extensions.append(record_dict)
            except:
                # 如果不是JSON，直接搜索字符串
                if 'GD20250900205' in str(extensions):
                    found_in_extensions.append(record_dict)
    
    print(f'在extensions中找到包含GD20250900205的记录: {len(found_in_extensions)}')
    
    for i, record_dict in enumerate(found_in_extensions):
        print(f'\n记录 {i+1}:')
        print(f'  管家: {record_dict.get("housekeeper")}')
        print(f'  合同ID: {record_dict.get("contract_id")}')
        print(f'  订单类型: {record_dict.get("order_type")}')
        print(f'  奖励类型: {record_dict.get("reward_types")}')
        print(f'  奖励名称: {record_dict.get("reward_names")}')
        
        # 解析extensions
        extensions = record_dict.get('extensions')
        if extensions:
            try:
                ext_data = json.loads(extensions)
                print(f'  Extensions详情:')
                print_dict_with_target(ext_data, 'GD20250900205', '    ')
            except Exception as e:
                print(f'  Extensions解析失败: {e}')
                if 'GD20250900205' in str(extensions):
                    print(f'  Extensions原始内容: {extensions}')
    
    # 特别检查自引单获得幸运数字奖励的问题
    print("\n" + "="*50)
    print("检查自引单获得幸运数字奖励的问题:")
    
    cursor.execute('''
        SELECT * FROM performance_data 
        WHERE order_type = 'self_referral' 
          AND reward_types LIKE '%幸运数字%'
          AND housekeeper LIKE '%余金凤%'
    ''')
    
    problem_records = cursor.fetchall()
    print(f'余金凤的自引单获得幸运数字奖励的记录: {len(problem_records)}')
    
    for i, record in enumerate(problem_records):
        record_dict = dict(zip(column_names, record))
        print(f'\n问题记录 {i+1}:')
        print(f'  管家: {record_dict.get("housekeeper")}')
        print(f'  合同ID: {record_dict.get("contract_id")}')
        print(f'  订单类型: {record_dict.get("order_type")}')
        print(f'  奖励类型: {record_dict.get("reward_types")}')
        print(f'  奖励名称: {record_dict.get("reward_names")}')
        print(f'  合同序号: {record_dict.get("contract_sequence")}')
        
        # 检查extensions中的详细信息
        extensions = record_dict.get('extensions')
        if extensions:
            try:
                ext_data = json.loads(extensions)
                print(f'  Extensions详情:')
                for key, value in ext_data.items():
                    if 'platform' in key.lower() or 'self' in key.lower() or 'count' in key.lower():
                        print(f'    {key}: {value}')
            except Exception as e:
                print(f'  Extensions解析失败: {e}')
    
    conn.close()

def search_in_dict(data, target):
    """递归搜索字典中的目标值"""
    if isinstance(data, dict):
        for key, value in data.items():
            if target in str(key) or target in str(value):
                return True
            if isinstance(value, (dict, list)):
                if search_in_dict(value, target):
                    return True
    elif isinstance(data, list):
        for item in data:
            if search_in_dict(item, target):
                return True
    else:
        return target in str(data)
    return False

def print_dict_with_target(data, target, indent=''):
    """打印包含目标值的字典内容"""
    if isinstance(data, dict):
        for key, value in data.items():
            if target in str(key) or target in str(value):
                print(f'{indent}{key}: {value}')
            elif isinstance(value, (dict, list)):
                if search_in_dict(value, target):
                    print(f'{indent}{key}:')
                    print_dict_with_target(value, target, indent + '  ')
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if search_in_dict(item, target):
                print(f'{indent}[{i}]:')
                print_dict_with_target(item, target, indent + '  ')

if __name__ == "__main__":
    main()
