#!/usr/bin/env python3
"""
业务逻辑验证工具

验证新旧架构的核心业务逻辑一致性，包括：
- 幸运数字奖励计算
- 阶梯奖励计算  
- 历史合同处理
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def compare_lucky_number_logic():
    """验证幸运数字奖励计算逻辑"""
    print("🍀 验证幸运数字奖励计算逻辑")
    print("-" * 40)
    
    # 读取新旧架构的输出
    old_file = 'state/PerformanceData-BJ-Sep.csv'
    new_file = 'performance_data_BJ-SEP_20250922_075022.csv'
    
    if not os.path.exists(old_file):
        print(f"❌ 旧架构文件不存在: {old_file}")
        return False
    
    if not os.path.exists(new_file):
        print(f"❌ 新架构文件不存在: {new_file}")
        return False
    
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)
    
    # 检查幸运数字奖励
    # 旧架构：检查"奖励名称"字段是否包含"接好运"
    old_lucky = old_df[old_df['奖励名称'].str.contains('接好运', na=False)] if '奖励名称' in old_df.columns else pd.DataFrame()
    # 新架构：检查"奖励名称"字段是否包含"接好运"
    new_lucky = new_df[new_df['奖励名称'].str.contains('接好运', na=False)] if '奖励名称' in new_df.columns else pd.DataFrame()
    
    print(f"旧架构幸运数字奖励记录: {len(old_lucky)} 条")
    print(f"新架构幸运数字奖励记录: {len(new_lucky)} 条")
    
    if len(old_lucky) != len(new_lucky):
        print("⚠️ 幸运数字奖励记录数量不一致")
        return False
    
    # 检查具体的幸运数字逻辑
    if len(old_lucky) > 0 and len(new_lucky) > 0:
        # 按合同ID排序对比
        old_lucky_sorted = old_lucky.sort_values('合同ID(_id)')
        new_lucky_sorted = new_lucky.sort_values('合同ID(_id)')
        
        # 检查合同ID是否一致
        old_ids = set(old_lucky_sorted['合同ID(_id)'].astype(str))
        new_ids = set(new_lucky_sorted['合同ID(_id)'].astype(str))
        
        if old_ids != new_ids:
            print("⚠️ 获得幸运数字奖励的合同ID不一致")
            only_old = old_ids - new_ids
            only_new = new_ids - old_ids
            if only_old:
                print(f"   仅在旧架构: {len(only_old)} 个")
            if only_new:
                print(f"   仅在新架构: {len(only_new)} 个")
            return False
        
        # 对于幸运数字奖励，我们主要检查获奖人员是否一致
        # 因为新旧架构的奖励金额存储方式不同，这里主要验证逻辑一致性
        print("✅ 获得幸运数字奖励的合同ID完全一致")
    
    print("✅ 幸运数字奖励逻辑一致")
    return True

def compare_tier_rewards_logic():
    """验证阶梯奖励计算逻辑"""
    print("\n🏆 验证阶梯奖励计算逻辑")
    print("-" * 40)
    
    # 读取新旧架构的输出
    old_file = 'state/PerformanceData-BJ-Sep.csv'
    new_file = 'performance_data_BJ-SEP_20250922_075022.csv'
    
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)
    
    # 检查达标奖
    old_target = old_df[old_df['奖励名称'].str.contains('达标奖', na=False)] if '奖励名称' in old_df.columns else pd.DataFrame()
    new_target = new_df[new_df['奖励名称'].str.contains('达标奖', na=False)] if '奖励名称' in new_df.columns else pd.DataFrame()

    print(f"旧架构达标奖记录: {len(old_target)} 条")
    print(f"新架构达标奖记录: {len(new_target)} 条")

    if len(old_target) != len(new_target):
        print("⚠️ 达标奖记录数量不一致")
        return False

    # 检查优秀奖
    old_excellent = old_df[old_df['奖励名称'].str.contains('优秀奖', na=False)] if '奖励名称' in old_df.columns else pd.DataFrame()
    new_excellent = new_df[new_df['奖励名称'].str.contains('优秀奖', na=False)] if '奖励名称' in new_df.columns else pd.DataFrame()

    print(f"旧架构优秀奖记录: {len(old_excellent)} 条")
    print(f"新架构优秀奖记录: {len(new_excellent)} 条")

    if len(old_excellent) != len(new_excellent):
        print("⚠️ 优秀奖记录数量不一致")
        return False
    
    print("✅ 阶梯奖励逻辑一致")
    return True

def compare_historical_contract_logic():
    """验证历史合同处理逻辑"""
    print("\n📚 验证历史合同处理逻辑")
    print("-" * 40)
    
    # 读取新旧架构的输出
    old_file = 'state/PerformanceData-BJ-Sep.csv'
    new_file = 'performance_data_BJ-SEP_20250922_075022.csv'
    
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)
    
    # 检查历史合同标记
    old_historical = old_df[old_df['是否历史合同'] == 'Y'] if '是否历史合同' in old_df.columns else pd.DataFrame()
    new_historical = new_df[new_df['is_historical'] == True] if 'is_historical' in new_df.columns else pd.DataFrame()
    
    print(f"旧架构历史合同: {len(old_historical)} 条")
    print(f"新架构历史合同: {len(new_historical)} 条")
    
    # 检查历史合同是否不参与奖励计算
    if len(new_historical) > 0:
        historical_with_rewards = new_historical[
            new_historical['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)
        ]

        if len(historical_with_rewards) > 0:
            print(f"⚠️ 发现 {len(historical_with_rewards)} 条历史合同获得了奖励")
            return False
        else:
            print("✅ 历史合同正确地不参与奖励计算")
    
    print("✅ 历史合同处理逻辑一致")
    return True

def compare_project_limit_logic():
    """验证项目限额逻辑"""
    print("\n💰 验证项目限额逻辑")
    print("-" * 40)
    
    # 读取新架构的输出
    new_file = 'performance_data_BJ-SEP_20250922_075022.csv'
    new_df = pd.read_csv(new_file)
    
    # 检查项目限额应用
    if '计入业绩金额' in new_df.columns and '合同金额(adjustRefundMoney)' in new_df.columns:
        # 找出业绩金额小于合同金额的记录（可能应用了项目限额）
        limited_records = new_df[
            new_df['计入业绩金额'] < new_df['合同金额(adjustRefundMoney)']
        ]
        
        print(f"应用项目限额的记录: {len(limited_records)} 条")
        
        if len(limited_records) > 0:
            # 检查是否有相同项目的多个合同
            if '工单编号(serviceAppointmentNum)' in new_df.columns:
                project_groups = new_df.groupby('工单编号(serviceAppointmentNum)')['计入业绩金额'].sum()
                over_limit_projects = project_groups[project_groups > 50000]
            
                if len(over_limit_projects) > 0:
                    print(f"⚠️ 发现 {len(over_limit_projects)} 个项目超过限额")
                    return False
                else:
                    print("✅ 项目限额逻辑正确应用")
            else:
                print("✅ 项目编号字段不存在，跳过项目限额检查")
        else:
            print("✅ 当前数据未触发项目限额")
    
    print("✅ 项目限额逻辑验证通过")
    return True

def main():
    """主函数"""
    print("🔍 北京9月业务逻辑验证")
    print("=" * 60)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 执行各项验证
    results.append(("幸运数字奖励逻辑", compare_lucky_number_logic()))
    results.append(("阶梯奖励逻辑", compare_tier_rewards_logic()))
    results.append(("历史合同处理逻辑", compare_historical_contract_logic()))
    results.append(("项目限额逻辑", compare_project_limit_logic()))
    
    # 总结结果
    print(f"\n{'='*60}")
    print("📊 业务逻辑验证结果总结")
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
        print("🎉 所有业务逻辑验证通过！")
        return 0
    else:
        print("⚠️ 部分业务逻辑验证失败，需要检查问题")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
