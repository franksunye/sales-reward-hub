#!/usr/bin/env python3
"""
余金凤详细分析脚本
"""

import pandas as pd

def main():
    print('=== 余金凤详细分析 ===')

    # 读取新架构数据
    new_df = pd.read_csv('temp/performance_data_BJ-SEP_final_fixed.csv')
    yujinfeng_records = new_df[new_df['管家(serviceHousekeeper)'] == '余金凤']

    print(f'余金凤总记录数: {len(yujinfeng_records)}')

    # 分析有奖励的记录
    reward_records = yujinfeng_records[yujinfeng_records['奖励名称'].notna()]
    reward_records = reward_records[reward_records['奖励名称'] != '']
    print(f'有奖励的记录数: {len(reward_records)}')

    print()
    print('奖励记录详情:')
    print('合同ID | 奖励名称 | 奖励类型 | 是否历史合同')
    print('-' * 60)

    for _, row in reward_records.iterrows():
        contract_id = str(row['合同ID(_id)'])[-8:]  # 显示后8位
        rewards = row['奖励名称']
        reward_types = row['奖励类型']
        is_historical = row['is_historical']
        
        print(f'{contract_id} | {rewards:<20} | {reward_types:<10} | {is_historical}')

    # 统计业绩情况
    total_performance = yujinfeng_records['计入业绩金额'].sum()
    new_contracts = yujinfeng_records[yujinfeng_records['is_historical'] == False]
    new_performance = new_contracts['计入业绩金额'].sum()

    print()
    print(f'余金凤业绩统计:')
    print(f'  总业绩金额: {total_performance:,.0f}元')
    print(f'  新增合同业绩: {new_performance:,.0f}元')
    print(f'  新增合同数: {len(new_contracts)}')
    
    # 分析旧架构数据
    print()
    print('=== 旧架构对比 ===')
    old_df = pd.read_csv('baseline/BJ-SEP/performance_data_BJ-SEP_baseline.csv')
    old_yujinfeng = old_df[old_df['管家(serviceHousekeeper)'] == '余金凤']
    old_activated = old_yujinfeng[old_yujinfeng['激活奖励状态'] == 1]
    
    print(f'旧架构余金凤激活奖励记录数: {len(old_activated)}')
    print('旧架构奖励详情:')
    for _, row in old_activated.iterrows():
        contract_id = str(row['合同ID(_id)'])[-8:]
        reward = row['奖励名称']
        print(f'  {contract_id}: {reward}')

if __name__ == '__main__':
    main()
