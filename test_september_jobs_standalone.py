#!/usr/bin/env python3
"""
9月份Job单独测试脚本

用于在本地环境测试北京和上海9月份Job的新架构实现
确保它们可以独立运行，为影子模式部署做准备

使用方法:
    python test_september_jobs_standalone.py
    python test_september_jobs_standalone.py --beijing-only
    python test_september_jobs_standalone.py --shanghai-only
"""

import sys
import os
import logging
import argparse
import time
from datetime import datetime

# 添加modules路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'september_jobs_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def test_beijing_september():
    """测试北京9月Job"""
    print("=" * 60)
    print("🏢 测试北京9月Job (新架构)")
    print("=" * 60)
    
    try:
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        
        logging.info("开始执行北京9月Job...")
        start_time = time.time()
        
        # 执行Job
        records = signing_and_sales_incentive_sep_beijing_v2()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 输出结果
        print(f"✅ 北京9月Job执行成功!")
        print(f"📊 处理记录数: {len(records)}")
        print(f"⏱️  执行时间: {execution_time:.2f} 秒")
        
        # 显示前几条记录的关键信息
        if records:
            print(f"\n📋 前3条记录预览:")
            for i, record in enumerate(records[:3]):
                print(f"  {i+1}. 合同号: {record.contract_number}, "
                      f"奖励: {record.reward_amount}, "
                      f"类型: {record.reward_type}")
        
        # 统计信息
        total_reward = sum(record.reward_amount for record in records)
        print(f"\n💰 总奖励金额: {total_reward:,.2f}")
        
        # 按奖励类型统计
        reward_types = {}
        for record in records:
            reward_types[record.reward_type] = reward_types.get(record.reward_type, 0) + 1
        
        print(f"📈 奖励类型分布:")
        for reward_type, count in reward_types.items():
            print(f"  - {reward_type}: {count} 条")
        
        logging.info(f"北京9月Job测试完成: {len(records)} 条记录, 耗时 {execution_time:.2f} 秒")
        return True, len(records), execution_time
        
    except Exception as e:
        print(f"❌ 北京9月Job执行失败: {e}")
        logging.error(f"北京9月Job执行失败: {e}", exc_info=True)
        return False, 0, 0

def test_shanghai_september():
    """测试上海9月Job"""
    print("=" * 60)
    print("🏢 测试上海9月Job (新架构)")
    print("=" * 60)
    
    try:
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        
        logging.info("开始执行上海9月Job...")
        start_time = time.time()
        
        # 执行Job
        records = signing_and_sales_incentive_sep_shanghai_v2()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 输出结果
        print(f"✅ 上海9月Job执行成功!")
        print(f"📊 处理记录数: {len(records)}")
        print(f"⏱️  执行时间: {execution_time:.2f} 秒")
        
        # 显示前几条记录的关键信息
        if records:
            print(f"\n📋 前3条记录预览:")
            for i, record in enumerate(records[:3]):
                print(f"  {i+1}. 合同号: {record.contract_number}, "
                      f"奖励: {record.reward_amount}, "
                      f"类型: {record.reward_type}")
        
        # 统计信息
        total_reward = sum(record.reward_amount for record in records)
        print(f"\n💰 总奖励金额: {total_reward:,.2f}")
        
        # 按奖励类型统计
        reward_types = {}
        for record in records:
            reward_types[record.reward_type] = reward_types.get(record.reward_type, 0) + 1
        
        print(f"📈 奖励类型分布:")
        for reward_type, count in reward_types.items():
            print(f"  - {reward_type}: {count} 条")
        
        # 上海9月特殊统计（双轨统计）
        platform_orders = [r for r in records if '平台单' in r.reward_type]
        self_referral_orders = [r for r in records if '自引单' in r.reward_type]
        
        print(f"\n🔄 双轨统计:")
        print(f"  - 平台单: {len(platform_orders)} 条")
        print(f"  - 自引单: {len(self_referral_orders)} 条")
        
        logging.info(f"上海9月Job测试完成: {len(records)} 条记录, 耗时 {execution_time:.2f} 秒")
        return True, len(records), execution_time
        
    except Exception as e:
        print(f"❌ 上海9月Job执行失败: {e}")
        logging.error(f"上海9月Job执行失败: {e}", exc_info=True)
        return False, 0, 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='9月份Job单独测试')
    parser.add_argument('--beijing-only', action='store_true', help='只测试北京9月Job')
    parser.add_argument('--shanghai-only', action='store_true', help='只测试上海9月Job')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    print("🚀 9月份Job单独测试开始")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 测试北京9月
    if not args.shanghai_only:
        beijing_success, beijing_records, beijing_time = test_beijing_september()
        results.append(('北京9月', beijing_success, beijing_records, beijing_time))
        print()
    
    # 测试上海9月
    if not args.beijing_only:
        shanghai_success, shanghai_records, shanghai_time = test_shanghai_september()
        results.append(('上海9月', shanghai_success, shanghai_records, shanghai_time))
        print()
    
    # 总结报告
    print("=" * 60)
    print("📊 测试总结报告")
    print("=" * 60)
    
    all_success = True
    total_records = 0
    total_time = 0
    
    for job_name, success, records, exec_time in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{job_name}: {status} | 记录数: {records} | 时间: {exec_time:.2f}秒")
        
        if success:
            total_records += records
            total_time += exec_time
        else:
            all_success = False
    
    print(f"\n📈 总计: 记录数: {total_records} | 总时间: {total_time:.2f}秒")
    
    if all_success:
        print("\n🎉 所有测试通过! 9月份Job新架构运行正常")
        print("✅ 可以进行下一步: 配置影子模式")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查错误日志")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
