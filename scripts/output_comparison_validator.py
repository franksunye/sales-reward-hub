#!/usr/bin/env python3
"""
输出结果对比验证工具

对比新旧架构的输出结果，验证数据一致性。
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def compare_basic_statistics(old_df, new_df):
    """对比基础统计信息"""
    print("📊 基础统计对比")
    print("-" * 40)
    
    print(f"记录总数:")
    print(f"  旧架构: {len(old_df)} 条")
    print(f"  新架构: {len(new_df)} 条")
    
    if len(old_df) != len(new_df):
        print("⚠️ 记录总数不一致")
        return False
    
    # 对比合同金额总和
    old_total = old_df['合同金额(adjustRefundMoney)'].sum()
    new_total = new_df['合同金额(adjustRefundMoney)'].sum()
    
    print(f"合同金额总和:")
    print(f"  旧架构: {old_total:,.2f}")
    print(f"  新架构: {new_total:,.2f}")
    
    if abs(old_total - new_total) > 0.01:
        print("⚠️ 合同金额总和不一致")
        return False
    
    # 对比支付金额总和
    old_paid = old_df['支付金额(paidAmount)'].sum()
    new_paid = new_df['支付金额(paidAmount)'].sum()
    
    print(f"支付金额总和:")
    print(f"  旧架构: {old_paid:,.2f}")
    print(f"  新架构: {new_paid:,.2f}")
    
    if abs(old_paid - new_paid) > 0.01:
        print("⚠️ 支付金额总和不一致")
        return False
    
    print("✅ 基础统计一致")
    return True

def compare_reward_statistics(old_df, new_df):
    """对比奖励统计"""
    print("\n🏆 奖励统计对比")
    print("-" * 40)
    
    # 统计各种奖励的数量
    old_lucky = len(old_df[old_df['奖励名称'].str.contains('接好运', na=False)])
    new_lucky = len(new_df[new_df['奖励名称'].str.contains('接好运', na=False)])
    
    old_target = len(old_df[old_df['奖励名称'].str.contains('达标奖', na=False)])
    new_target = len(new_df[new_df['奖励名称'].str.contains('达标奖', na=False)])
    
    old_excellent = len(old_df[old_df['奖励名称'].str.contains('优秀奖', na=False)])
    new_excellent = len(new_df[new_df['奖励名称'].str.contains('优秀奖', na=False)])
    
    print(f"接好运奖励:")
    print(f"  旧架构: {old_lucky} 条")
    print(f"  新架构: {new_lucky} 条")
    
    print(f"达标奖:")
    print(f"  旧架构: {old_target} 条")
    print(f"  新架构: {new_target} 条")
    
    print(f"优秀奖:")
    print(f"  旧架构: {old_excellent} 条")
    print(f"  新架构: {new_excellent} 条")
    
    if old_lucky != new_lucky or old_target != new_target or old_excellent != new_excellent:
        print("⚠️ 奖励统计不一致")
        return False
    
    print("✅ 奖励统计一致")
    return True

def compare_historical_contracts(old_df, new_df):
    """对比历史合同处理"""
    print("\n📚 历史合同对比")
    print("-" * 40)
    
    old_historical = len(old_df[old_df['是否历史合同'] == 'Y'])
    new_historical = len(new_df[new_df['is_historical'] == True])
    
    print(f"历史合同数量:")
    print(f"  旧架构: {old_historical} 条")
    print(f"  新架构: {new_historical} 条")
    
    if old_historical != new_historical:
        print("⚠️ 历史合同数量不一致")
        return False
    
    # 检查历史合同的业绩金额
    old_hist_df = old_df[old_df['是否历史合同'] == 'Y']
    new_hist_df = new_df[new_df['is_historical'] == True]
    
    if len(old_hist_df) > 0 and len(new_hist_df) > 0:
        old_hist_amount = old_hist_df['计入业绩金额'].sum()
        new_hist_amount = new_hist_df['计入业绩金额'].sum()
        
        print(f"历史合同业绩金额:")
        print(f"  旧架构: {old_hist_amount:,.2f}")
        print(f"  新架构: {new_hist_amount:,.2f}")
        
        if abs(old_hist_amount - new_hist_amount) > 0.01:
            print("⚠️ 历史合同业绩金额不一致")
            return False
    
    print("✅ 历史合同处理一致")
    return True

def compare_housekeeper_performance(old_df, new_df):
    """对比管家业绩统计"""
    print("\n👨‍💼 管家业绩对比")
    print("-" * 40)
    
    # 按管家分组统计
    old_hk_stats = old_df.groupby('管家(serviceHousekeeper)').agg({
        '合同金额(adjustRefundMoney)': 'sum',
        '计入业绩金额': 'sum',
        '合同ID(_id)': 'count'
    }).round(2)
    
    new_hk_stats = new_df.groupby('管家(serviceHousekeeper)').agg({
        '合同金额(adjustRefundMoney)': 'sum',
        '计入业绩金额': 'sum',
        '合同ID(_id)': 'count'
    }).round(2)
    
    print(f"管家数量:")
    print(f"  旧架构: {len(old_hk_stats)} 人")
    print(f"  新架构: {len(new_hk_stats)} 人")
    
    if len(old_hk_stats) != len(new_hk_stats):
        print("⚠️ 管家数量不一致")
        return False
    
    # 检查管家名单是否一致
    old_housekeepers = set(old_hk_stats.index)
    new_housekeepers = set(new_hk_stats.index)
    
    if old_housekeepers != new_housekeepers:
        print("⚠️ 管家名单不一致")
        only_old = old_housekeepers - new_housekeepers
        only_new = new_housekeepers - old_housekeepers
        if only_old:
            print(f"  仅在旧架构: {only_old}")
        if only_new:
            print(f"  仅在新架构: {only_new}")
        return False
    
    # 检查业绩金额是否一致
    total_diff = 0
    for hk in old_housekeepers:
        old_amount = old_hk_stats.loc[hk, '计入业绩金额']
        new_amount = new_hk_stats.loc[hk, '计入业绩金额']
        diff = abs(old_amount - new_amount)
        total_diff += diff
        
        if diff > 0.01:
            print(f"⚠️ 管家 {hk} 业绩金额不一致: 旧{old_amount} vs 新{new_amount}")
    
    if total_diff > 0.01:
        print(f"⚠️ 管家业绩总差异: {total_diff:.2f}")
        return False
    
    print("✅ 管家业绩统计一致")
    return True

def compare_contract_details(old_df, new_df):
    """对比合同详细信息"""
    print("\n📋 合同详情对比")
    print("-" * 40)
    
    # 按合同ID排序
    old_sorted = old_df.sort_values('合同ID(_id)')
    new_sorted = new_df.sort_values('合同ID(_id)')
    
    # 检查关键字段
    key_fields = ['合同ID(_id)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '计入业绩金额']
    
    for field in key_fields:
        if field in old_sorted.columns and field in new_sorted.columns:
            old_values = old_sorted[field].values
            new_values = new_sorted[field].values
            
            if field == '合同ID(_id)':
                # 字符串比较
                if not all(str(old) == str(new) for old, new in zip(old_values, new_values)):
                    print(f"⚠️ {field} 不一致")
                    return False
            else:
                # 数值比较
                if not all(abs(float(old) - float(new)) < 0.01 for old, new in zip(old_values, new_values)):
                    print(f"⚠️ {field} 不一致")
                    return False
    
    print("✅ 合同详情一致")
    return True

def main():
    """主函数"""
    print("🔍 北京9月输出结果对比验证")
    print("=" * 60)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 读取数据文件
    old_file = 'state/PerformanceData-BJ-Sep.csv'
    new_file = 'performance_data_BJ-SEP_20250922_075022.csv'
    
    if not os.path.exists(old_file):
        print(f"❌ 旧架构文件不存在: {old_file}")
        return 1
    
    if not os.path.exists(new_file):
        print(f"❌ 新架构文件不存在: {new_file}")
        return 1
    
    print(f"📁 读取数据文件:")
    print(f"  旧架构: {old_file}")
    print(f"  新架构: {new_file}")
    
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)
    
    print(f"  旧架构数据: {len(old_df)} 行 x {len(old_df.columns)} 列")
    print(f"  新架构数据: {len(new_df)} 行 x {len(new_df.columns)} 列")
    
    # 执行各项对比验证
    results = []
    
    results.append(("基础统计", compare_basic_statistics(old_df, new_df)))
    results.append(("奖励统计", compare_reward_statistics(old_df, new_df)))
    results.append(("历史合同", compare_historical_contracts(old_df, new_df)))
    results.append(("管家业绩", compare_housekeeper_performance(old_df, new_df)))
    results.append(("合同详情", compare_contract_details(old_df, new_df)))
    
    # 总结结果
    print(f"\n{'='*60}")
    print("📊 输出结果对比验证总结")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 输出结果对比验证100%通过！")
        print("✅ 新旧架构输出完全等价")
        return 0
    else:
        print("⚠️ 部分验证失败，新旧架构输出存在差异")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
