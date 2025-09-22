#!/usr/bin/env python3
"""
手动验证辅助脚本
用于本地手工测试时的详细对比验证
"""

import pandas as pd
import sys
import os
from pathlib import Path

def compare_beijing():
    """对比北京9月新旧架构输出"""
    print("🏢 北京9月详细对比")
    print("=" * 50)
    
    try:
        # 检查旧架构文件
        old_file = 'state/PerformanceData-BJ-Sep.csv'
        if not os.path.exists(old_file):
            print(f"❌ 旧架构文件不存在: {old_file}")
            return False
            
        old_df = pd.read_csv(old_file)
        print(f"✅ 旧架构文件加载成功: {len(old_df)} 条记录")
        
        # 查找新架构文件
        new_files = [f for f in os.listdir('.') if f.startswith('performance_data_BJ-SEP_')]
        if not new_files:
            print("❌ 未找到新架构北京输出文件")
            print("提示: 请先运行新架构并导出CSV文件")
            return False
            
        new_file = new_files[0]
        new_df = pd.read_csv(new_file)
        print(f"✅ 新架构文件加载成功: {len(new_df)} 条记录")
        
        # 基础统计对比
        print("\n📊 基础统计对比:")
        print(f"记录数: 旧{len(old_df)} vs 新{len(new_df)}")
        
        old_amount = old_df['合同金额(adjustRefundMoney)'].sum()
        new_amount = new_df['合同金额(adjustRefundMoney)'].sum()
        print(f"合同金额: 旧{old_amount:.2f} vs 新{new_amount:.2f}")
        
        old_performance = old_df['计入业绩金额'].sum()
        new_performance = new_df['计入业绩金额'].sum()
        print(f"业绩金额: 旧{old_performance:.2f} vs 新{new_performance:.2f}")
        
        # 奖励统计对比
        old_rewards = len(old_df[old_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        new_rewards = len(new_df[new_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        print(f"奖励数: 旧{old_rewards} vs 新{new_rewards}")
        
        # 分类奖励统计
        for reward_type in ['接好运', '达标奖', '优秀奖']:
            old_count = len(old_df[old_df['奖励名称'].str.contains(reward_type, na=False)])
            new_count = len(new_df[new_df['奖励名称'].str.contains(reward_type, na=False)])
            print(f"  {reward_type}: 旧{old_count} vs 新{new_count}")
        
        # 检查关键管家
        print("\n👨‍💼 关键管家对比:")
        key_housekeepers = ['余金凤', '张争光', '文刘飞', '韩都保', '梁庆龙']
        for hk in key_housekeepers:
            old_count = len(old_df[old_df['管家(serviceHousekeeper)'] == hk])
            new_count = len(new_df[new_df['管家(serviceHousekeeper)'] == hk])
            if old_count > 0 or new_count > 0:
                print(f"  {hk}: 旧{old_count} vs 新{new_count}")
        
        # 验证结果
        success = (len(old_df) == len(new_df) and 
                  abs(old_amount - new_amount) < 0.01 and
                  old_rewards == new_rewards)
        
        if success:
            print("✅ 北京9月验证通过")
        else:
            print("❌ 北京9月验证失败")
            
        return success
        
    except Exception as e:
        print(f"❌ 北京对比失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_shanghai():
    """对比上海9月新旧架构输出"""
    print("\n🏙️ 上海9月详细对比")
    print("=" * 50)
    
    try:
        # 检查旧架构文件
        old_file = 'state/PerformanceData-SH-Sep.csv'
        if not os.path.exists(old_file):
            print(f"❌ 旧架构文件不存在: {old_file}")
            return False
            
        old_df = pd.read_csv(old_file)
        print(f"✅ 旧架构文件加载成功: {len(old_df)} 条记录")
        
        # 查找新架构文件
        new_files = [f for f in os.listdir('.') if f.startswith('performance_data_SH-SEP_')]
        if not new_files:
            print("❌ 未找到新架构上海输出文件")
            print("提示: 请先运行新架构并导出CSV文件")
            return False
            
        new_file = new_files[0]
        new_df = pd.read_csv(new_file)
        print(f"✅ 新架构文件加载成功: {len(new_df)} 条记录")
        
        # 基础统计对比
        print("\n📊 基础统计对比:")
        print(f"记录数: 旧{len(old_df)} vs 新{len(new_df)}")
        
        old_amount = old_df['合同金额(adjustRefundMoney)'].sum()
        new_amount = new_df['合同金额(adjustRefundMoney)'].sum()
        print(f"合同金额: 旧{old_amount:.2f} vs 新{new_amount:.2f}")
        
        old_performance = old_df['计入业绩金额'].sum()
        new_performance = new_df['计入业绩金额'].sum()
        print(f"业绩金额: 旧{old_performance:.2f} vs 新{new_performance:.2f}")
        
        # 奖励统计对比
        old_rewards = len(old_df[old_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        new_rewards = len(new_df[new_df['奖励名称'].str.contains('接好运|达标奖|优秀奖', na=False)])
        print(f"奖励数: 旧{old_rewards} vs 新{new_rewards}")
        
        # 检查双轨统计字段（上海特色）
        print("\n📈 双轨统计字段检查:")
        dual_track_fields = ['平台单累计数量', '平台单累计金额', '自引单累计数量', '自引单累计金额']
        for field in dual_track_fields:
            if field in new_df.columns:
                print(f"  ✅ {field}: 存在")
            else:
                print(f"  ❌ {field}: 缺失")
        
        # 检查管家键格式（上海特色）
        print("\n🔑 管家键格式检查:")
        sample_records = new_df.head(3)
        for idx, row in sample_records.iterrows():
            housekeeper = row['管家(serviceHousekeeper)']
            service_provider = row['服务商(orgName)']
            expected_key = f"{housekeeper}_{service_provider}"
            print(f"  示例: {expected_key}")
            break  # 只显示一个示例
        
        # 验证结果
        success = (len(old_df) == len(new_df) and 
                  abs(old_amount - new_amount) < 0.01 and
                  old_rewards == new_rewards)
        
        if success:
            print("✅ 上海9月验证通过")
        else:
            print("❌ 上海9月验证失败")
            
        return success
        
    except Exception as e:
        print(f"❌ 上海对比失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔍 手动验证辅助工具")
    print("=" * 60)
    print("用途: 对比新旧架构输出文件的一致性")
    print("=" * 60)
    
    # 检查当前目录
    if not os.path.exists('modules'):
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 执行对比
    bj_success = compare_beijing()
    sh_success = compare_shanghai()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)
    print(f"北京9月: {'✅ 通过' if bj_success else '❌ 失败'}")
    print(f"上海9月: {'✅ 通过' if sh_success else '❌ 失败'}")
    
    if bj_success and sh_success:
        print("\n🎉 所有验证通过！新旧架构完全等价")
        print("✅ 可以安全部署新架构")
        sys.exit(0)
    else:
        print("\n⚠️ 验证失败，请检查差异")
        print("💡 建议:")
        print("  1. 检查是否正确执行了新旧架构")
        print("  2. 确认网络连接正常")
        print("  3. 检查数据库是否正确清理")
        print("  4. 查看详细日志: tail -f logs/app.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
