#!/usr/bin/env python3
"""
9月份Job真实环境集成测试

这是一个端到端的集成测试，使用真实的生产环境数据：
- 连接真实的Metabase API
- 使用生产环境配置
- 执行完整的数据处理流程
- 不发送消息（消息发送已解耦）

测试类型：Integration Testing / End-to-End Testing

使用方法:
    python integration_test_september_jobs.py
    python integration_test_september_jobs.py --beijing-only
    python integration_test_september_jobs.py --shanghai-only
"""

import sys
import os
import logging
import argparse
import time
from datetime import datetime
from typing import List, Dict, Any

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
            logging.FileHandler(f'integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def test_metabase_connection():
    """测试Metabase连接"""
    print("🔗 测试Metabase连接...")
    
    try:
        from modules.request_module import get_valid_session
        session_id = get_valid_session()
        
        if session_id:
            print(f"✅ Metabase连接成功，Session ID: {session_id[:10]}...")
            return True
        else:
            print("❌ Metabase连接失败")
            return False
            
    except Exception as e:
        print(f"❌ Metabase连接异常: {e}")
        logging.error(f"Metabase连接异常: {e}", exc_info=True)
        return False

def test_beijing_september_integration():
    """北京9月Job集成测试"""
    print("=" * 60)
    print("🏢 北京9月Job集成测试 (真实环境)")
    print("=" * 60)
    
    try:
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        
        logging.info("开始北京9月Job集成测试...")
        start_time = time.time()
        
        # 执行Job（连接真实API）
        records = signing_and_sales_incentive_sep_beijing_v2()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 输出结果
        print(f"✅ 北京9月Job执行成功!")
        print(f"📊 处理记录数: {len(records)}")
        print(f"⏱️  执行时间: {execution_time:.2f} 秒")
        
        # 详细分析
        if records:
            print(f"\n📋 记录详情:")
            
            # 统计业绩金额
            total_performance = sum(record.performance_amount for record in records)
            print(f"💰 总业绩金额: {total_performance:,.2f} 元")
            
            # 统计奖励类型
            reward_stats = {}
            for record in records:
                for reward in record.rewards:
                    reward_type = reward.reward_type
                    if reward_type not in reward_stats:
                        reward_stats[reward_type] = {'count': 0, 'amount': 0}
                    reward_stats[reward_type]['count'] += 1
                    reward_stats[reward_type]['amount'] += (reward.amount or 0)
            
            print(f"🎁 奖励统计:")
            for reward_type, stats in reward_stats.items():
                print(f"  - {reward_type}: {stats['count']} 个, 总额 {stats['amount']:.2f} 元")
            
            # 管家统计
            housekeeper_stats = {}
            for record in records:
                housekeeper = record.contract_data.housekeeper
                if housekeeper not in housekeeper_stats:
                    housekeeper_stats[housekeeper] = {
                        'contracts': 0,
                        'performance': 0,
                        'rewards': 0
                    }
                housekeeper_stats[housekeeper]['contracts'] += 1
                housekeeper_stats[housekeeper]['performance'] += record.performance_amount
                housekeeper_stats[housekeeper]['rewards'] += sum((r.amount or 0) for r in record.rewards)
            
            print(f"👥 管家统计:")
            for housekeeper, stats in housekeeper_stats.items():
                print(f"  - {housekeeper}: {stats['contracts']}单, "
                      f"业绩{stats['performance']:,.0f}元, "
                      f"奖励{stats['rewards']:.0f}元")
            
            # 显示前3条记录
            print(f"\n📋 前3条记录预览:")
            for i, record in enumerate(records[:3]):
                reward_info = ', '.join([f"{r.reward_type}({r.amount or 0}元)" for r in record.rewards])
                print(f"  {i+1}. 合同: {record.contract_data.contract_id}, "
                      f"管家: {record.contract_data.housekeeper}, "
                      f"业绩: {record.performance_amount:,.0f}元, "
                      f"奖励: {reward_info or '无'}")
        
        # 验证关键业务逻辑
        print(f"\n🔍 业务逻辑验证:")
        
        # 5万上限验证
        over_limit = [r for r in records if r.performance_amount > 50000]
        print(f"  - 5万上限检查: {len(over_limit)} 条超限记录")
        
        # 历史合同验证
        historical = [r for r in records if hasattr(r.contract_data, 'is_historical') and r.contract_data.is_historical]
        print(f"  - 历史合同处理: {len(historical)} 条历史合同")
        
        logging.info(f"北京9月Job集成测试完成: {len(records)} 条记录, 耗时 {execution_time:.2f} 秒")
        return True, len(records), execution_time, records
        
    except Exception as e:
        print(f"❌ 北京9月Job执行失败: {e}")
        logging.error(f"北京9月Job执行失败: {e}", exc_info=True)
        return False, 0, 0, []

def test_shanghai_september_integration():
    """上海9月Job集成测试"""
    print("=" * 60)
    print("🏢 上海9月Job集成测试 (真实环境)")
    print("=" * 60)
    
    try:
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        
        logging.info("开始上海9月Job集成测试...")
        start_time = time.time()
        
        # 执行Job（连接真实API）
        records = signing_and_sales_incentive_sep_shanghai_v2()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 输出结果
        print(f"✅ 上海9月Job执行成功!")
        print(f"📊 处理记录数: {len(records)}")
        print(f"⏱️  执行时间: {execution_time:.2f} 秒")
        
        # 详细分析
        if records:
            print(f"\n📋 记录详情:")
            
            # 统计业绩金额
            total_performance = sum(record.performance_amount for record in records)
            print(f"💰 总业绩金额: {total_performance:,.2f} 元")
            
            # 双轨统计分析
            platform_orders = []
            self_referral_orders = []
            
            for record in records:
                # 根据款项来源类型判断
                trade_in = getattr(record.contract_data, 'trade_in', None)
                if trade_in == 0:
                    platform_orders.append(record)
                elif trade_in == 1:
                    self_referral_orders.append(record)
            
            print(f"🔄 双轨统计:")
            print(f"  - 平台单: {len(platform_orders)} 条")
            print(f"  - 自引单: {len(self_referral_orders)} 条")
            
            # 项目地址去重分析
            if self_referral_orders:
                address_stats = {}
                for record in self_referral_orders:
                    housekeeper = record.contract_data.housekeeper
                    address = getattr(record.contract_data, 'project_address', '未知地址')
                    key = f"{housekeeper}_{address}"
                    if key not in address_stats:
                        address_stats[key] = []
                    address_stats[key].append(record.contract_data.contract_id)
                
                duplicate_addresses = {k: v for k, v in address_stats.items() if len(v) > 1}
                print(f"📍 项目地址分析:")
                print(f"  - 总地址数: {len(address_stats)}")
                print(f"  - 重复地址: {len(duplicate_addresses)}")
            
            # 自引单奖励分析
            self_referral_rewards = []
            for record in self_referral_orders:
                for reward in record.rewards:
                    if '自引单' in reward.reward_type:
                        self_referral_rewards.append(reward)
            
            print(f"🎁 自引单奖励: {len(self_referral_rewards)} 个")
            
            # 显示前3条记录
            print(f"\n📋 前3条记录预览:")
            for i, record in enumerate(records[:3]):
                trade_type = "平台单" if getattr(record.contract_data, 'trade_in', None) == 0 else "自引单"
                reward_info = ', '.join([f"{r.reward_type}({r.amount or 0}元)" for r in record.rewards])
                print(f"  {i+1}. 合同: {record.contract_data.contract_id}, "
                      f"管家: {record.contract_data.housekeeper}, "
                      f"类型: {trade_type}, "
                      f"业绩: {record.performance_amount:,.0f}元, "
                      f"奖励: {reward_info or '无'}")
        
        logging.info(f"上海9月Job集成测试完成: {len(records)} 条记录, 耗时 {execution_time:.2f} 秒")
        return True, len(records), execution_time, records
        
    except Exception as e:
        print(f"❌ 上海9月Job执行失败: {e}")
        logging.error(f"上海9月Job执行失败: {e}", exc_info=True)
        return False, 0, 0, []

def validate_csv_output():
    """验证生成的CSV文件"""
    print("\n📁 验证生成的CSV文件...")
    
    csv_files = []
    for file in os.listdir('.'):
        if file.startswith('performance_data_') and file.endswith('.csv'):
            csv_files.append(file)
    
    if csv_files:
        # 按修改时间排序，获取最新的
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        print(f"✅ 找到 {len(csv_files)} 个CSV文件:")
        for file in csv_files[:3]:  # 显示最新的3个
            size = os.path.getsize(file)
            mtime = datetime.fromtimestamp(os.path.getmtime(file))
            print(f"  - {file} ({size} bytes, {mtime.strftime('%H:%M:%S')})")
        return True
    else:
        print("⚠️ 未找到CSV文件")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='9月份Job真实环境集成测试')
    parser.add_argument('--beijing-only', action='store_true', help='只测试北京9月Job')
    parser.add_argument('--shanghai-only', action='store_true', help='只测试上海9月Job')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    print("🚀 9月份Job真实环境集成测试开始")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 测试类型: Integration Testing (端到端测试)")
    print(f"📡 数据源: 真实Metabase API")
    print(f"💬 消息发送: 已解耦（不实际发送）")
    print()
    
    # 测试Metabase连接
    if not test_metabase_connection():
        print("❌ Metabase连接失败，无法进行集成测试")
        return 1
    
    print()
    
    results = []
    
    # 测试北京9月
    if not args.shanghai_only:
        beijing_success, beijing_records, beijing_time, beijing_data = test_beijing_september_integration()
        results.append(('北京9月', beijing_success, beijing_records, beijing_time))
        print()
    
    # 测试上海9月
    if not args.beijing_only:
        shanghai_success, shanghai_records, shanghai_time, shanghai_data = test_shanghai_september_integration()
        results.append(('上海9月', shanghai_success, shanghai_records, shanghai_time))
        print()
    
    # 验证CSV输出
    csv_validation = validate_csv_output()
    
    # 总结报告
    print("=" * 60)
    print("📊 集成测试总结报告")
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
    print(f"📁 CSV文件: {'✅ 正常生成' if csv_validation else '❌ 未生成'}")
    
    if all_success and csv_validation:
        print("\n🎉 集成测试全部通过! 新架构在真实环境中运行正常")
        print("✅ 可以进行下一步: 配置影子模式进行新旧系统对比")
        return 0
    else:
        print("\n⚠️ 集成测试发现问题，请检查错误日志")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
