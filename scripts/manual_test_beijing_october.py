#!/usr/bin/env python3
"""
北京2025年10月销售激励活动手工测试脚本

用途：
1. 手工执行北京10月Job函数
2. 查看真实API数据返回内容
3. 验证数据处理和奖励计算逻辑
4. 检查数据库存储结果

使用方法：
python scripts/manual_test_beijing_october.py [--debug] [--no-notifications]
"""

import sys
import os
import json
import sqlite3
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")

def print_section(title):
    """打印章节"""
    print(f"\n{'─'*40}")
    print(f"📋 {title}")
    print(f"{'─'*40}")

def check_environment():
    """检查环境"""
    print_header("环境检查")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查依赖
    try:
        import pandas
        import requests
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        return False
    
    # 检查项目结构
    if not os.path.exists("modules/core/beijing_jobs.py"):
        print("❌ 项目结构错误，请在项目根目录运行")
        return False
    
    print("✅ 环境检查通过")
    return True

def clean_environment():
    """清理环境"""
    print_section("清理环境")
    
    files_to_clean = [
        "performance_data.db",
        "tasks.db",
        "performance_data_BJ-OCT.csv",
        "beijing_october_test_output.csv"
    ]
    
    for file in files_to_clean:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ 删除文件: {file}")
    
    print("✅ 环境清理完成")

def test_api_data():
    """测试API数据获取"""
    print_section("测试API数据获取")
    
    try:
        from modules.core.beijing_jobs import _get_contract_data_with_source_type
        
        print("🌐 正在获取北京10月API数据...")
        contract_data = _get_contract_data_with_source_type()
        
        print(f"📊 获取到 {len(contract_data)} 条合同数据")
        
        if contract_data:
            # 显示前3条数据的关键字段
            print("\n📋 前3条数据示例:")
            for i, contract in enumerate(contract_data[:3]):
                print(f"\n合同 {i+1}:")
                print(f"  合同ID: {contract.get('合同ID(_id)', 'N/A')}")
                print(f"  管家: {contract.get('管家(serviceHousekeeper)', 'N/A')}")
                print(f"  合同金额: {contract.get('合同金额(adjustRefundMoney)', 'N/A')}")
                print(f"  工单类型: {contract.get('工单类型(sourceType)', 'N/A')} ({'自引单' if contract.get('工单类型(sourceType)') == '1' else '平台单' if contract.get('工单类型(sourceType)') == '2' else '未知'})")
                print(f"  项目地址: {contract.get('项目地址(projectAddress)', 'N/A')}")
                print(f"  状态: {contract.get('Status', 'N/A')}")
                print(f"  支付状态: {contract.get('State', 'N/A')}")
            
            # 统计数据类型
            source_type_stats = {}
            status_stats = {}
            state_stats = {}
            
            for contract in contract_data:
                source_type = contract.get('工单类型(sourceType)', 'Unknown')
                status = contract.get('Status', 'Unknown')
                state = contract.get('State', 'Unknown')
                
                source_type_stats[source_type] = source_type_stats.get(source_type, 0) + 1
                status_stats[status] = status_stats.get(status, 0) + 1
                state_stats[state] = state_stats.get(state, 0) + 1
            
            print(f"\n📈 数据统计:")
            print(f"  工单类型分布: {source_type_stats}")
            print(f"  状态分布: {status_stats}")
            print(f"  支付状态分布: {state_stats}")
            
            # 检查关键字段
            print(f"\n🔍 关键字段检查:")
            has_source_type = any('工单类型(sourceType)' in contract for contract in contract_data)
            has_project_address = any('项目地址(projectAddress)' in contract for contract in contract_data)
            print(f"  包含sourceType字段: {'✅' if has_source_type else '❌'}")
            print(f"  包含projectAddress字段: {'✅' if has_project_address else '❌'}")
            
        return contract_data
        
    except Exception as e:
        print(f"❌ API数据获取失败: {e}")
        return None

def execute_beijing_october_job(enable_notifications=True):
    """执行北京10月Job函数"""
    print_section("执行北京10月Job函数")
    
    try:
        from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing_v2
        
        print("🚀 开始执行北京10月销售激励活动...")
        print(f"📢 通知功能: {'启用' if enable_notifications else '禁用'}")
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行Job函数
        result = signing_and_sales_incentive_oct_beijing_v2()
        
        # 记录结束时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"✅ 执行完成，耗时: {execution_time:.2f}秒")
        print(f"📊 处理了 {len(result)} 条记录")
        
        # 统计奖励情况
        reward_count = len([r for r in result if r.rewards])
        total_rewards = sum(len(r.rewards) for r in result)
        
        print(f"🏆 获得奖励的记录: {reward_count} 条")
        print(f"🎁 总奖励数量: {total_rewards} 个")
        
        # 显示前5条有奖励的记录
        reward_records = [r for r in result if r.rewards][:5]
        if reward_records:
            print(f"\n🎉 前5条奖励记录:")
            for i, record in enumerate(reward_records):
                print(f"\n记录 {i+1}:")
                print(f"  管家: {record.housekeeper}")
                print(f"  合同ID: {record.contract_id}")
                print(f"  合同金额: {record.contract_amount}")
                print(f"  订单类型: {record.order_type}")
                print(f"  奖励: {[f'{r.reward_type}-{r.reward_name}' for r in record.rewards]}")
        
        return result
        
    except Exception as e:
        print(f"❌ Job执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_database_results():
    """检查数据库结果"""
    print_section("检查数据库结果")
    
    if not os.path.exists("performance_data.db"):
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect("performance_data.db")
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 数据库表: {[table[0] for table in tables]}")
        
        # 检查performance_data表
        if ('performance_data',) in tables:
            cursor.execute("SELECT COUNT(*) FROM performance_data")
            total_count = cursor.fetchone()[0]
            print(f"📊 总记录数: {total_count}")
            
            # 按活动代码统计
            cursor.execute("SELECT activity_code, COUNT(*) FROM performance_data GROUP BY activity_code")
            activity_stats = cursor.fetchall()
            print(f"📈 按活动统计: {dict(activity_stats)}")
            
            # 按订单类型统计
            cursor.execute("SELECT order_type, COUNT(*) FROM performance_data GROUP BY order_type")
            order_type_stats = cursor.fetchall()
            print(f"📦 按订单类型统计: {dict(order_type_stats)}")
            
            # 奖励统计
            cursor.execute("SELECT COUNT(*) FROM performance_data WHERE rewards IS NOT NULL AND rewards != '[]'")
            reward_count = cursor.fetchone()[0]
            print(f"🏆 有奖励的记录: {reward_count}")
            
            # 显示前5条记录
            cursor.execute("""
                SELECT housekeeper, contract_id, contract_amount, order_type, rewards 
                FROM performance_data 
                WHERE activity_code = 'BJ-OCT' 
                LIMIT 5
            """)
            sample_records = cursor.fetchall()
            
            if sample_records:
                print(f"\n📋 前5条记录:")
                for i, record in enumerate(sample_records):
                    housekeeper, contract_id, amount, order_type, rewards = record
                    print(f"\n记录 {i+1}:")
                    print(f"  管家: {housekeeper}")
                    print(f"  合同ID: {contract_id}")
                    print(f"  金额: {amount}")
                    print(f"  类型: {order_type}")
                    print(f"  奖励: {rewards}")
        
        conn.close()
        print("✅ 数据库检查完成")
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

def export_results():
    """导出结果到CSV"""
    print_section("导出结果")
    
    try:
        from scripts.export_database_to_csv import main as export_main
        
        output_file = "beijing_october_test_output.csv"
        print(f"📤 导出数据到: {output_file}")
        
        # 导出北京10月数据
        export_main(["--activity", "BJ-OCT", "--output", output_file])
        
        if os.path.exists(output_file):
            # 检查文件
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"✅ 导出成功")
            print(f"📊 文件行数: {len(lines)}")
            print(f"📁 文件大小: {os.path.getsize(output_file)} 字节")
            
            # 显示前3行
            if len(lines) > 1:
                print(f"\n📋 文件内容预览:")
                print("表头:", lines[0].strip())
                for i in range(1, min(4, len(lines))):
                    print(f"数据 {i}:", lines[i].strip()[:100] + "..." if len(lines[i]) > 100 else lines[i].strip())
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="北京10月销售激励活动手工测试")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--no-notifications", action="store_true", help="禁用通知发送")
    parser.add_argument("--skip-api-test", action="store_true", help="跳过API测试")
    parser.add_argument("--skip-execution", action="store_true", help="跳过Job执行")
    
    args = parser.parse_args()
    
    print_header("北京2025年10月销售激励活动手工测试")
    print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 环境检查
    if not check_environment():
        return 1
    
    # 清理环境
    clean_environment()
    
    # API数据测试
    if not args.skip_api_test:
        api_data = test_api_data()
        if not api_data:
            print("❌ API数据获取失败，无法继续测试")
            return 1
    
    # 执行Job函数
    if not args.skip_execution:
        result = execute_beijing_october_job(enable_notifications=not args.no_notifications)
        if not result:
            print("❌ Job执行失败")
            return 1
    
    # 检查数据库结果
    check_database_results()
    
    # 导出结果
    export_results()
    
    print_header("测试完成")
    print("✅ 北京10月功能手工测试完成")
    print("\n📋 后续检查建议:")
    print("1. 检查数据库文件: performance_data.db")
    print("2. 检查导出文件: beijing_october_test_output.csv")
    print("3. 验证奖励计算逻辑是否正确")
    print("4. 检查消息通知是否发送（如果启用）")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
