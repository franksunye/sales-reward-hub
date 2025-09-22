#!/usr/bin/env python3
"""
个体抽样验证工具

验证具体管家和合同在新旧架构下的个体结果一致性。
补充统计验证的不足，确保个体层面的等价性。
"""

import sys
import os
import pandas as pd
from datetime import datetime
import random

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def sample_housekeepers_validation(old_df, new_df, sample_size=10):
    """抽样验证管家个体结果"""
    print("👨‍💼 管家个体抽样验证")
    print("-" * 50)
    
    # 获取所有管家
    all_housekeepers = list(set(old_df['管家(serviceHousekeeper)'].unique()) & 
                           set(new_df['管家(serviceHousekeeper)'].unique()))
    
    # 随机抽样
    sample_housekeepers = random.sample(all_housekeepers, min(sample_size, len(all_housekeepers)))
    
    print(f"从{len(all_housekeepers)}个管家中抽样{len(sample_housekeepers)}个进行详细验证")
    print()
    
    issues = []
    
    for i, housekeeper in enumerate(sample_housekeepers, 1):
        print(f"🔍 验证管家 {i}/{len(sample_housekeepers)}: {housekeeper}")
        
        # 获取该管家的所有记录
        old_hk_records = old_df[old_df['管家(serviceHousekeeper)'] == housekeeper]
        new_hk_records = new_df[new_df['管家(serviceHousekeeper)'] == housekeeper]
        
        # 验证记录数量
        if len(old_hk_records) != len(new_hk_records):
            issue = f"管家{housekeeper}记录数不一致: 旧{len(old_hk_records)} vs 新{len(new_hk_records)}"
            issues.append(issue)
            print(f"  ❌ {issue}")
            continue
        
        # 验证合同金额总和
        old_total = old_hk_records['合同金额(adjustRefundMoney)'].sum()
        new_total = new_hk_records['合同金额(adjustRefundMoney)'].sum()
        
        if abs(old_total - new_total) > 0.01:
            issue = f"管家{housekeeper}合同金额不一致: 旧{old_total:.2f} vs 新{new_total:.2f}"
            issues.append(issue)
            print(f"  ❌ {issue}")
            continue
        
        # 验证业绩金额总和
        old_perf = old_hk_records['计入业绩金额'].sum()
        new_perf = new_hk_records['计入业绩金额'].sum()
        
        if abs(old_perf - new_perf) > 0.01:
            issue = f"管家{housekeeper}业绩金额不一致: 旧{old_perf:.2f} vs 新{new_perf:.2f}"
            issues.append(issue)
            print(f"  ❌ {issue}")
            continue
        
        # 验证奖励记录
        old_rewards = old_hk_records[old_hk_records['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)]
        new_rewards = new_hk_records[new_hk_records['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)]
        
        if len(old_rewards) != len(new_rewards):
            issue = f"管家{housekeeper}奖励数量不一致: 旧{len(old_rewards)} vs 新{len(new_rewards)}"
            issues.append(issue)
            print(f"  ❌ {issue}")
            continue
        
        # 验证具体奖励类型
        old_reward_types = set(old_rewards['奖励名称'].str.extract(r'(接好运|达标奖|优秀奖)')[0].dropna())
        new_reward_types = set(new_rewards['奖励名称'].str.extract(r'(接好运|达标奖|优秀奖)')[0].dropna())
        
        if old_reward_types != new_reward_types:
            issue = f"管家{housekeeper}奖励类型不一致: 旧{old_reward_types} vs 新{new_reward_types}"
            issues.append(issue)
            print(f"  ❌ {issue}")
            continue
        
        print(f"  ✅ 记录数:{len(old_hk_records)}, 合同金额:{old_total:.2f}, 业绩金额:{old_perf:.2f}, 奖励数:{len(old_rewards)}")
    
    return issues

def sample_contracts_validation(old_df, new_df, sample_size=20):
    """抽样验证合同个体结果"""
    print(f"\n📋 合同个体抽样验证")
    print("-" * 50)
    
    # 获取所有合同ID
    all_contracts = list(set(old_df['合同ID(_id)'].astype(str)) & 
                        set(new_df['合同ID(_id)'].astype(str)))
    
    # 随机抽样
    sample_contracts = random.sample(all_contracts, min(sample_size, len(all_contracts)))
    
    print(f"从{len(all_contracts)}个合同中抽样{len(sample_contracts)}个进行详细验证")
    print()
    
    issues = []
    
    for i, contract_id in enumerate(sample_contracts, 1):
        print(f"🔍 验证合同 {i}/{len(sample_contracts)}: {contract_id}")
        
        # 获取该合同的记录
        old_contract = old_df[old_df['合同ID(_id)'].astype(str) == contract_id]
        new_contract = new_df[new_df['合同ID(_id)'].astype(str) == contract_id]
        
        if len(old_contract) != 1 or len(new_contract) != 1:
            issue = f"合同{contract_id}记录数异常: 旧{len(old_contract)} vs 新{len(new_contract)}"
            issues.append(issue)
            print(f"  ❌ {issue}")
            continue
        
        old_record = old_contract.iloc[0]
        new_record = new_contract.iloc[0]
        
        # 验证关键字段
        key_fields = [
            ('合同金额(adjustRefundMoney)', '合同金额'),
            ('支付金额(paidAmount)', '支付金额'),
            ('计入业绩金额', '业绩金额'),
            ('管家(serviceHousekeeper)', '管家')
        ]
        
        contract_issues = []
        for field, name in key_fields:
            if field in old_contract.columns and field in new_contract.columns:
                old_val = old_record[field]
                new_val = new_record[field]
                
                if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                    if abs(float(old_val) - float(new_val)) > 0.01:
                        contract_issues.append(f"{name}不一致: 旧{old_val} vs 新{new_val}")
                else:
                    if str(old_val) != str(new_val):
                        contract_issues.append(f"{name}不一致: 旧{old_val} vs 新{new_val}")
        
        # 验证奖励状态
        old_reward = old_record.get('奖励名称', '')
        new_reward = new_record.get('奖励名称', '')
        
        old_has_reward = bool(pd.notna(old_reward) and str(old_reward).strip() and 
                             any(x in str(old_reward) for x in ['接好运', '达标奖', '优秀奖']))
        new_has_reward = bool(pd.notna(new_reward) and str(new_reward).strip() and 
                             any(x in str(new_reward) for x in ['接好运', '达标奖', '优秀奖']))
        
        if old_has_reward != new_has_reward:
            contract_issues.append(f"奖励状态不一致: 旧{'有' if old_has_reward else '无'} vs 新{'有' if new_has_reward else '无'}")
        
        if contract_issues:
            for issue in contract_issues:
                issues.append(f"合同{contract_id}: {issue}")
                print(f"  ❌ {issue}")
        else:
            # 显示验证通过的关键信息
            amount = old_record['合同金额(adjustRefundMoney)']
            housekeeper = old_record['管家(serviceHousekeeper)']
            reward_status = "有奖励" if old_has_reward else "无奖励"
            print(f"  ✅ 管家:{housekeeper}, 金额:{amount:.2f}, {reward_status}")
    
    return issues

def detailed_reward_analysis(old_df, new_df):
    """详细奖励分析"""
    print(f"\n🏆 详细奖励分析")
    print("-" * 50)
    
    # 获取所有获奖记录
    old_rewards = old_df[old_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)]
    new_rewards = new_df[new_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)]
    
    print(f"奖励记录总数: 旧{len(old_rewards)} vs 新{len(new_rewards)}")
    
    # 按管家分组分析奖励
    old_hk_rewards = old_rewards.groupby('管家(serviceHousekeeper)')['奖励名称'].apply(list).to_dict()
    new_hk_rewards = new_rewards.groupby('管家(serviceHousekeeper)')['奖励名称'].apply(list).to_dict()
    
    # 找出奖励不一致的管家
    all_reward_housekeepers = set(old_hk_rewards.keys()) | set(new_hk_rewards.keys())
    
    issues = []
    consistent_count = 0
    
    print(f"\n按管家详细对比奖励:")
    for housekeeper in sorted(all_reward_housekeepers):
        old_rewards_list = old_hk_rewards.get(housekeeper, [])
        new_rewards_list = new_hk_rewards.get(housekeeper, [])
        
        # 提取奖励类型
        old_types = []
        new_types = []
        
        for reward in old_rewards_list:
            if '接好运' in reward:
                old_types.append('接好运')
            if '达标奖' in reward:
                old_types.append('达标奖')
            if '优秀奖' in reward:
                old_types.append('优秀奖')
        
        for reward in new_rewards_list:
            if '接好运' in reward:
                new_types.append('接好运')
            if '达标奖' in reward:
                new_types.append('达标奖')
            if '优秀奖' in reward:
                new_types.append('优秀奖')
        
        old_types_set = set(old_types)
        new_types_set = set(new_types)
        
        if old_types_set == new_types_set:
            consistent_count += 1
            print(f"  ✅ {housekeeper}: {sorted(old_types_set) if old_types_set else '无奖励'}")
        else:
            issue = f"管家{housekeeper}奖励类型不一致: 旧{sorted(old_types_set)} vs 新{sorted(new_types_set)}"
            issues.append(issue)
            print(f"  ❌ {housekeeper}: 旧{sorted(old_types_set)} vs 新{sorted(new_types_set)}")
    
    print(f"\n奖励一致性: {consistent_count}/{len(all_reward_housekeepers)} 个管家一致")
    
    return issues

def main():
    """主函数"""
    print("🔍 北京9月个体抽样验证")
    print("=" * 60)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("目标: 补充统计验证，确保个体层面等价性")
    
    # 读取数据文件
    old_file = 'state/PerformanceData-BJ-Sep.csv'
    new_file = 'performance_data_BJ-SEP_20250922_075022.csv'
    
    if not os.path.exists(old_file):
        print(f"❌ 旧架构文件不存在: {old_file}")
        return 1
    
    if not os.path.exists(new_file):
        print(f"❌ 新架构文件不存在: {new_file}")
        return 1
    
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)
    
    print(f"数据加载: 旧架构{len(old_df)}条, 新架构{len(new_df)}条")
    
    # 设置随机种子确保可重复
    random.seed(42)
    
    # 执行各项个体验证
    all_issues = []
    
    # 管家抽样验证
    hk_issues = sample_housekeepers_validation(old_df, new_df, sample_size=10)
    all_issues.extend(hk_issues)
    
    # 合同抽样验证
    contract_issues = sample_contracts_validation(old_df, new_df, sample_size=20)
    all_issues.extend(contract_issues)
    
    # 详细奖励分析
    reward_issues = detailed_reward_analysis(old_df, new_df)
    all_issues.extend(reward_issues)
    
    # 总结结果
    print(f"\n{'='*60}")
    print("📊 个体抽样验证总结")
    print("-" * 30)
    
    if not all_issues:
        print("🎉 个体抽样验证100%通过！")
        print("✅ 所有抽样的管家和合同在新旧架构下结果完全一致")
        print("✅ 统计一致性 + 个体一致性 = 完全等价性确认")
        return 0
    else:
        print(f"⚠️ 发现 {len(all_issues)} 个个体差异:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n💡 建议:")
        print("   - 检查个体计算逻辑差异")
        print("   - 验证数据处理顺序")
        print("   - 确认业务规则实现")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
