#!/usr/bin/env python3
"""
检查马俊杰的具体数据
"""

import sqlite3
import os

if not os.path.exists('performance_data.db'):
    print("❌ 数据库文件不存在")
    exit(1)

conn = sqlite3.connect('performance_data.db')
cursor = conn.cursor()

print('🔍 马俊杰的数据分析:')

# 查找马俊杰的所有记录
cursor.execute('SELECT * FROM performance_data WHERE housekeeper = "马俊杰" AND activity_code = "BJ-OCT"')
records = cursor.fetchall()

print(f'  马俊杰总记录数: {len(records)}')

if records:
    # 获取列名
    cursor.execute("PRAGMA table_info(performance_data)")
    columns = [col[1] for col in cursor.fetchall()]
    
    for i, record in enumerate(records):
        print(f'\n  记录 {i+1}:')
        record_dict = dict(zip(columns, record))
        print(f'    合同ID: {record_dict["contract_id"]}')
        print(f'    订单类型: {record_dict["order_type"]}')
        print(f'    合同金额: {record_dict["contract_amount"]}')
        print(f'    奖励类型: {record_dict["reward_types"]}')
        print(f'    奖励名称: {record_dict["reward_names"]}')
        print(f'    创建时间: {record_dict["created_at"]}')

# 检查所有只有自引单的管家
print('\n🔍 所有只有自引单的管家:')
cursor.execute('''
    SELECT housekeeper, 
           COUNT(*) as total_count,
           SUM(CASE WHEN order_type = 'platform' THEN 1 ELSE 0 END) as platform_count,
           SUM(CASE WHEN order_type = 'self_referral' THEN 1 ELSE 0 END) as self_referral_count,
           SUM(CASE WHEN reward_types LIKE '%幸运数字%' THEN 1 ELSE 0 END) as lucky_rewards
    FROM performance_data 
    WHERE activity_code = "BJ-OCT" 
    GROUP BY housekeeper
    HAVING platform_count = 0 AND self_referral_count > 0
''')

self_referral_only = cursor.fetchall()
print(f'  只有自引单的管家数量: {len(self_referral_only)}')

for housekeeper, total, platform, self_ref, lucky in self_referral_only:
    print(f'    {housekeeper}: 总{total}单 (平台{platform}单, 自引{self_ref}单) - 幸运数字奖励{lucky}个')

# 检查所有获得幸运数字奖励但平台单为0的情况
print('\n🚨 BUG验证 - 平台单为0但获得幸运数字奖励的情况:')
cursor.execute('''
    SELECT housekeeper, 
           COUNT(*) as total_count,
           SUM(CASE WHEN order_type = 'platform' THEN 1 ELSE 0 END) as platform_count,
           SUM(CASE WHEN order_type = 'self_referral' THEN 1 ELSE 0 END) as self_referral_count,
           SUM(CASE WHEN reward_types LIKE '%幸运数字%' THEN 1 ELSE 0 END) as lucky_rewards
    FROM performance_data 
    WHERE activity_code = "BJ-OCT" 
    GROUP BY housekeeper
    HAVING platform_count = 0 AND lucky_rewards > 0
''')

bug_cases = cursor.fetchall()
print(f'  BUG案例数量: {len(bug_cases)}')

for housekeeper, total, platform, self_ref, lucky in bug_cases:
    print(f'    ❌ {housekeeper}: 平台单{platform}单, 自引单{self_ref}单 - 错误获得{lucky}个幸运数字奖励')

conn.close()
print('\n✅ 分析完成')
