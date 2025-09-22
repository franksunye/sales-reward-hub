#!/usr/bin/env python3
"""
逐管家奖励对比分析脚本
"""

import pandas as pd
import sys

def main():
    print('=== 逐管家奖励对比分析 ===')
    print()

    # 读取旧架构数据
    old_df = pd.read_csv('baseline/BJ-SEP/performance_data_BJ-SEP_baseline.csv')
    old_activated = old_df[old_df['激活奖励状态'] == 1]

    # 读取新架构数据
    new_df = pd.read_csv('temp/performance_data_BJ-SEP_legacy_fixed.csv')
    new_rewards = new_df[new_df['奖励名称'].notna()]
    new_rewards = new_rewards[new_rewards['奖励名称'] != '']

    # 统计旧架构管家奖励
    old_housekeeper_rewards = {}
    for _, row in old_activated.iterrows():
        housekeeper = row['管家(serviceHousekeeper)']
        reward = str(row['奖励名称']).strip()
        if housekeeper not in old_housekeeper_rewards:
            old_housekeeper_rewards[housekeeper] = []
        if reward and reward != 'nan':
            old_housekeeper_rewards[housekeeper].append(reward)

    # 统计新架构管家奖励
    new_housekeeper_rewards = {}
    for _, row in new_rewards.iterrows():
        housekeeper = row['管家(serviceHousekeeper)']
        rewards = str(row['奖励名称']).split(',')
        if housekeeper not in new_housekeeper_rewards:
            new_housekeeper_rewards[housekeeper] = []
        for reward in rewards:
            reward = reward.strip()
            if reward and reward != 'nan':
                new_housekeeper_rewards[housekeeper].append(reward)

    # 获取所有管家
    all_housekeepers = set(old_housekeeper_rewards.keys()) | set(new_housekeeper_rewards.keys())

    print('管家奖励对比:')
    print('管家名称 | 旧架构奖励 | 新架构奖励 | 状态')
    print('-' * 80)

    differences = []
    matches = 0
    
    for housekeeper in sorted(all_housekeepers):
        old_rewards = sorted(old_housekeeper_rewards.get(housekeeper, []))
        new_rewards_list = sorted(new_housekeeper_rewards.get(housekeeper, []))
        
        if old_rewards == new_rewards_list:
            status = '✅ 一致'
            matches += 1
        else:
            status = '❌ 差异'
            differences.append((housekeeper, old_rewards, new_rewards_list))
        
        old_str = ', '.join(old_rewards) if old_rewards else '无'
        new_str = ', '.join(new_rewards_list) if new_rewards_list else '无'
        
        print(f'{housekeeper:<12} | {old_str:<20} | {new_str:<20} | {status}')

    print()
    print(f'总管家数: {len(all_housekeepers)}')
    print(f'一致的管家数: {matches}')
    print(f'有差异的管家数: {len(differences)}')

    if differences:
        print()
        print('=== 差异详情 ===')
        for housekeeper, old_rewards, new_rewards_list in differences:
            print(f'{housekeeper}:')
            print(f'  旧架构: {old_rewards}')
            print(f'  新架构: {new_rewards_list}')
            print()

if __name__ == '__main__':
    main()
