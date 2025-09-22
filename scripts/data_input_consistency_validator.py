#!/usr/bin/env python3
"""
数据输入一致性验证工具

验证新旧架构使用相同的输入数据，确保对比的公平性。
"""

import sys
import os
import logging
from datetime import datetime
import pandas as pd

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_old_arch_data():
    """获取旧架构的数据"""
    logger = setup_logging()
    
    print("📥 获取旧架构数据...")
    
    try:
        # 导入旧架构
        from jobs import signing_and_sales_incentive_sep_beijing
        
        # 清理之前的临时文件
        temp_files = ['ContractData-BJ-SEP.csv', 'PerformanceData-BJ-SEP.csv']
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
        
        print("🚀 执行旧架构北京9月函数...")
        
        # 执行旧架构函数
        signing_and_sales_incentive_sep_beijing()
        
        # 检查生成的文件
        performance_file = 'state/PerformanceData-BJ-Sep.csv'

        if not os.path.exists(performance_file):
            raise FileNotFoundError(f"旧架构未生成业绩数据文件: {performance_file}")

        # 读取数据
        performance_data = pd.read_csv(performance_file)

        print(f"✅ 旧架构数据获取成功:")
        print(f"   - 业绩数据: {len(performance_data)} 条")

        return {
            'performance_data': performance_data,
            'performance_file': performance_file
        }
        
    except Exception as e:
        print(f"❌ 旧架构数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_new_arch_data():
    """获取新架构的数据"""
    print("\n📥 获取新架构数据...")
    
    try:
        # 导入新架构
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        
        print("🚀 执行新架构北京9月函数...")
        
        # 执行新架构函数
        result = signing_and_sales_incentive_sep_beijing_v2()
        
        # 查找生成的CSV文件
        import glob
        csv_files = glob.glob('performance_data_BJ-SEP_*.csv')
        
        if not csv_files:
            raise FileNotFoundError("新架构未生成CSV文件")
        
        # 使用最新的文件
        latest_file = max(csv_files, key=os.path.getctime)
        performance_data = pd.read_csv(latest_file)
        
        print(f"✅ 新架构数据获取成功:")
        print(f"   - 业绩数据: {len(performance_data)} 条")
        print(f"   - 返回对象: {len(result)} 条记录")
        
        return {
            'performance_data': performance_data,
            'performance_file': latest_file,
            'result_objects': result
        }
        
    except Exception as e:
        print(f"❌ 新架构数据获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_input_data(old_data, new_data):
    """对比输入数据的一致性"""
    print("\n⚖️ 对比输入数据一致性...")
    
    issues = []
    
    # 检查记录数量
    old_count = len(old_data['performance_data'])
    new_count = len(new_data['performance_data'])

    print(f"📊 记录数量对比:")
    print(f"   - 旧架构业绩数据: {old_count} 条")
    print(f"   - 新架构业绩数据: {new_count} 条")
    
    if old_count != new_count:
        issues.append(f"记录数量不一致: 旧架构{old_count}条 vs 新架构{new_count}条")
    else:
        print("✅ 记录数量一致")
    
    # 检查合同ID一致性
    if '合同ID(_id)' in old_data['performance_data'].columns:
        old_contract_ids = set(old_data['performance_data']['合同ID(_id)'].astype(str))
        
        if '合同ID(_id)' in new_data['performance_data'].columns:
            new_contract_ids = set(new_data['performance_data']['合同ID(_id)'].astype(str))
            
            print(f"\n🔍 合同ID对比:")
            print(f"   - 旧架构合同ID数量: {len(old_contract_ids)}")
            print(f"   - 新架构合同ID数量: {len(new_contract_ids)}")
            
            # 找出差异
            only_in_old = old_contract_ids - new_contract_ids
            only_in_new = new_contract_ids - old_contract_ids
            
            if only_in_old:
                issues.append(f"仅在旧架构中的合同ID: {len(only_in_old)}个")
                print(f"   ⚠️ 仅在旧架构: {len(only_in_old)}个")
                
            if only_in_new:
                issues.append(f"仅在新架构中的合同ID: {len(only_in_new)}个")
                print(f"   ⚠️ 仅在新架构: {len(only_in_new)}个")
                
            if not only_in_old and not only_in_new:
                print("✅ 合同ID完全一致")
        else:
            issues.append("新架构数据中缺少合同ID字段")
    else:
        issues.append("旧架构数据中缺少合同ID字段")
    
    # 检查关键字段存在性
    print(f"\n📋 关键字段检查:")
    
    key_fields = [
        '合同ID(_id)', '管家(serviceHousekeeper)', '合同金额(adjustRefundMoney)',
        '支付金额(paidAmount)', '合同编号(contractdocNum)'
    ]
    
    for field in key_fields:
        old_has = field in old_data['performance_data'].columns
        new_has = field in new_data['performance_data'].columns
        
        if old_has and new_has:
            print(f"   ✅ {field}: 两边都有")
        elif old_has and not new_has:
            print(f"   ⚠️ {field}: 仅旧架构有")
            issues.append(f"新架构缺少字段: {field}")
        elif not old_has and new_has:
            print(f"   ⚠️ {field}: 仅新架构有")
        else:
            print(f"   ❌ {field}: 两边都没有")
            issues.append(f"两边都缺少字段: {field}")
    
    return issues

def main():
    """主函数"""
    print("🔍 北京9月数据输入一致性验证")
    print("=" * 60)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取旧架构数据
    old_data = get_old_arch_data()
    if not old_data:
        print("❌ 无法获取旧架构数据，验证失败")
        return 1
    
    # 获取新架构数据
    new_data = get_new_arch_data()
    if not new_data:
        print("❌ 无法获取新架构数据，验证失败")
        return 1
    
    # 对比数据一致性
    issues = compare_input_data(old_data, new_data)
    
    # 生成报告
    print(f"\n{'='*60}")
    print("📊 验证结果总结")
    print("-" * 30)
    
    if not issues:
        print("🎉 数据输入一致性验证通过！")
        print("✅ 新旧架构使用相同的输入数据")
        return 0
    else:
        print(f"⚠️ 发现 {len(issues)} 个数据一致性问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n💡 建议:")
        print("   - 检查数据获取逻辑是否一致")
        print("   - 确认API调用参数相同")
        print("   - 验证数据预处理步骤")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
