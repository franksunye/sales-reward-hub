#!/usr/bin/env python3
"""
边界情况验证工具

验证新旧架构在特殊情况下的处理一致性。
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def check_zero_amount_contracts(old_df, new_df):
    """检查零金额合同处理"""
    print("💰 零金额合同处理验证")
    print("-" * 40)
    
    # 查找零金额合同
    old_zero = old_df[old_df['合同金额(adjustRefundMoney)'] == 0]
    new_zero = new_df[new_df['合同金额(adjustRefundMoney)'] == 0]
    
    print(f"零金额合同数量:")
    print(f"  旧架构: {len(old_zero)} 条")
    print(f"  新架构: {len(new_zero)} 条")
    
    if len(old_zero) != len(new_zero):
        print("⚠️ 零金额合同数量不一致")
        return False
    
    if len(old_zero) > 0:
        # 检查零金额合同是否获得奖励
        old_zero_rewards = old_zero[old_zero['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)]
        new_zero_rewards = new_zero[new_zero['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)]
        
        print(f"零金额合同获得奖励:")
        print(f"  旧架构: {len(old_zero_rewards)} 条")
        print(f"  新架构: {len(new_zero_rewards)} 条")
        
        if len(old_zero_rewards) != len(new_zero_rewards):
            print("⚠️ 零金额合同奖励处理不一致")
            return False
    else:
        print("✅ 当前数据中无零金额合同")
    
    print("✅ 零金额合同处理一致")
    return True

def check_large_amount_contracts(old_df, new_df):
    """检查大金额合同处理"""
    print("\n💎 大金额合同处理验证")
    print("-" * 40)
    
    # 查找大金额合同（>50000）
    old_large = old_df[old_df['合同金额(adjustRefundMoney)'] > 50000]
    new_large = new_df[new_df['合同金额(adjustRefundMoney)'] > 50000]
    
    print(f"大金额合同数量 (>50000):")
    print(f"  旧架构: {len(old_large)} 条")
    print(f"  新架构: {len(new_large)} 条")
    
    if len(old_large) != len(new_large):
        print("⚠️ 大金额合同数量不一致")
        return False
    
    if len(old_large) > 0:
        # 检查大金额合同的业绩金额是否被限制
        old_limited = old_large[old_large['计入业绩金额'] < old_large['合同金额(adjustRefundMoney)']]
        new_limited = new_large[new_large['计入业绩金额'] < new_large['合同金额(adjustRefundMoney)']]
        
        print(f"被限额的大金额合同:")
        print(f"  旧架构: {len(old_limited)} 条")
        print(f"  新架构: {len(new_limited)} 条")
        
        if len(old_limited) != len(new_limited):
            print("⚠️ 大金额合同限额处理不一致")
            return False
    else:
        print("✅ 当前数据中无大金额合同")
    
    print("✅ 大金额合同处理一致")
    return True

def check_duplicate_contracts(old_df, new_df):
    """检查重复合同处理"""
    print("\n🔄 重复合同处理验证")
    print("-" * 40)
    
    # 检查合同ID重复
    old_duplicates = old_df[old_df.duplicated('合同ID(_id)', keep=False)]
    new_duplicates = new_df[new_df.duplicated('合同ID(_id)', keep=False)]
    
    print(f"重复合同ID:")
    print(f"  旧架构: {len(old_duplicates)} 条")
    print(f"  新架构: {len(new_duplicates)} 条")
    
    if len(old_duplicates) != len(new_duplicates):
        print("⚠️ 重复合同处理不一致")
        return False
    
    if len(old_duplicates) > 0:
        print("⚠️ 发现重复合同ID，需要检查数据质量")
        return False
    
    print("✅ 无重复合同，数据质量良好")
    return True

def check_missing_data_handling(old_df, new_df):
    """检查缺失数据处理"""
    print("\n❓ 缺失数据处理验证")
    print("-" * 40)
    
    # 检查关键字段的缺失值
    key_fields = ['管家(serviceHousekeeper)', '合同金额(adjustRefundMoney)', '支付金额(paidAmount)']
    
    for field in key_fields:
        if field in old_df.columns and field in new_df.columns:
            old_missing = old_df[field].isna().sum()
            new_missing = new_df[field].isna().sum()
            
            print(f"{field} 缺失值:")
            print(f"  旧架构: {old_missing} 个")
            print(f"  新架构: {new_missing} 个")
            
            if old_missing != new_missing:
                print(f"⚠️ {field} 缺失值处理不一致")
                return False
    
    print("✅ 缺失数据处理一致")
    return True

def check_extreme_values(old_df, new_df):
    """检查极值处理"""
    print("\n📊 极值处理验证")
    print("-" * 40)
    
    # 检查合同金额的极值
    old_min = old_df['合同金额(adjustRefundMoney)'].min()
    old_max = old_df['合同金额(adjustRefundMoney)'].max()
    new_min = new_df['合同金额(adjustRefundMoney)'].min()
    new_max = new_df['合同金额(adjustRefundMoney)'].max()
    
    print(f"合同金额范围:")
    print(f"  旧架构: {old_min:,.2f} ~ {old_max:,.2f}")
    print(f"  新架构: {new_min:,.2f} ~ {new_max:,.2f}")
    
    if abs(old_min - new_min) > 0.01 or abs(old_max - new_max) > 0.01:
        print("⚠️ 合同金额极值不一致")
        return False
    
    # 检查业绩金额的极值
    old_perf_min = old_df['计入业绩金额'].min()
    old_perf_max = old_df['计入业绩金额'].max()
    new_perf_min = new_df['计入业绩金额'].min()
    new_perf_max = new_df['计入业绩金额'].max()
    
    print(f"业绩金额范围:")
    print(f"  旧架构: {old_perf_min:,.2f} ~ {old_perf_max:,.2f}")
    print(f"  新架构: {new_perf_min:,.2f} ~ {new_perf_max:,.2f}")
    
    if abs(old_perf_min - new_perf_min) > 0.01 or abs(old_perf_max - new_perf_max) > 0.01:
        print("⚠️ 业绩金额极值不一致")
        return False
    
    print("✅ 极值处理一致")
    return True

def check_special_characters(old_df, new_df):
    """检查特殊字符处理"""
    print("\n🔤 特殊字符处理验证")
    print("-" * 40)
    
    # 检查管家名称中的特殊字符
    old_special = old_df[old_df['管家(serviceHousekeeper)'].str.contains(r'[^\u4e00-\u9fa5a-zA-Z0-9]', na=False)]
    new_special = new_df[new_df['管家(serviceHousekeeper)'].str.contains(r'[^\u4e00-\u9fa5a-zA-Z0-9]', na=False)]
    
    print(f"包含特殊字符的管家名称:")
    print(f"  旧架构: {len(old_special)} 条")
    print(f"  新架构: {len(new_special)} 条")
    
    if len(old_special) != len(new_special):
        print("⚠️ 特殊字符处理不一致")
        return False
    
    print("✅ 特殊字符处理一致")
    return True

def main():
    """主函数"""
    print("🔍 北京9月边界情况验证")
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
    
    old_df = pd.read_csv(old_file)
    new_df = pd.read_csv(new_file)
    
    # 执行各项边界情况验证
    results = []
    
    results.append(("零金额合同", check_zero_amount_contracts(old_df, new_df)))
    results.append(("大金额合同", check_large_amount_contracts(old_df, new_df)))
    results.append(("重复合同", check_duplicate_contracts(old_df, new_df)))
    results.append(("缺失数据", check_missing_data_handling(old_df, new_df)))
    results.append(("极值处理", check_extreme_values(old_df, new_df)))
    results.append(("特殊字符", check_special_characters(old_df, new_df)))
    
    # 总结结果
    print(f"\n{'='*60}")
    print("📊 边界情况验证总结")
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
        print("🎉 边界情况验证100%通过！")
        print("✅ 新旧架构在特殊情况下处理一致")
        return 0
    else:
        print("⚠️ 部分边界情况验证失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
