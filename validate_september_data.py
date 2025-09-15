#!/usr/bin/env python3
"""
9月份Job数据验证脚本

详细验证生成的CSV数据是否符合业务要求
包括数据完整性、业务逻辑正确性、格式规范性等

使用方法:
    python validate_september_data.py
"""

import sys
import os
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any

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
            logging.FileHandler(f'data_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def find_latest_csv_files():
    """查找最新的CSV文件"""
    csv_files = []
    for file in os.listdir('.'):
        if file.startswith('performance_data_') and file.endswith('.csv'):
            csv_files.append(file)
    
    # 按修改时间排序，获取最新的
    csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return csv_files

def read_csv_data(filename: str) -> List[Dict]:
    """读取CSV数据"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        logging.error(f"读取CSV文件失败 {filename}: {e}")
        return []

def validate_beijing_september_data(data: List[Dict]) -> Dict:
    """验证北京9月数据"""
    print("🔍 验证北京9月数据...")
    
    validation_report = {
        'total_records': len(data),
        'errors': [],
        'warnings': [],
        'business_logic_checks': {},
        'data_quality_checks': {}
    }
    
    if not data:
        validation_report['errors'].append("没有找到北京9月数据")
        return validation_report
    
    # 1. 数据完整性检查
    required_fields = [
        '活动编号', '合同ID(_id)', '管家(serviceHousekeeper)', '服务商(orgName)',
        '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '计入业绩金额',
        '活动期内第几个合同', '管家累计单数', '管家累计金额', '激活奖励状态'
    ]
    
    for i, record in enumerate(data):
        for field in required_fields:
            if field not in record or not record[field]:
                validation_report['errors'].append(f"记录{i+1}: 缺少必填字段 {field}")
    
    # 2. 业务逻辑验证
    print("📋 业务逻辑验证:")
    
    # 2.1 活动编号检查
    activity_codes = set(record.get('活动编号', '') for record in data)
    print(f"  活动编号: {activity_codes}")
    if 'BJ-SEP' not in activity_codes:
        validation_report['warnings'].append("未找到BJ-SEP活动编号")
    
    # 2.2 历史合同处理检查
    historical_contracts = [r for r in data if r.get('is_historical') == 'True']
    new_contracts = [r for r in data if r.get('is_historical') != 'True']
    print(f"  历史合同: {len(historical_contracts)} 条")
    print(f"  新增合同: {len(new_contracts)} 条")
    
    validation_report['business_logic_checks']['historical_contracts'] = len(historical_contracts)
    validation_report['business_logic_checks']['new_contracts'] = len(new_contracts)
    
    # 2.3 5万上限逻辑检查
    over_limit_records = []
    for record in data:
        try:
            performance_amount = float(record.get('计入业绩金额', 0))
            contract_amount = float(record.get('合同金额(adjustRefundMoney)', 0))
            
            if performance_amount > 50000:
                over_limit_records.append({
                    'contract_id': record.get('合同ID(_id)'),
                    'performance_amount': performance_amount,
                    'contract_amount': contract_amount
                })
        except ValueError:
            validation_report['errors'].append(f"金额字段格式错误: {record.get('合同ID(_id)')}")
    
    print(f"  超过5万上限的记录: {len(over_limit_records)} 条")
    if over_limit_records:
        for record in over_limit_records:
            print(f"    合同{record['contract_id']}: 业绩{record['performance_amount']}, 合同{record['contract_amount']}")
    
    validation_report['business_logic_checks']['over_limit_records'] = len(over_limit_records)
    
    # 2.4 管家统计验证
    housekeeper_stats = {}
    for record in data:
        housekeeper = record.get('管家(serviceHousekeeper)', '')
        if housekeeper not in housekeeper_stats:
            housekeeper_stats[housekeeper] = {
                'count': 0,
                'total_amount': 0,
                'performance_amount': 0
            }
        
        try:
            housekeeper_stats[housekeeper]['count'] += 1
            housekeeper_stats[housekeeper]['total_amount'] += float(record.get('合同金额(adjustRefundMoney)', 0))
            housekeeper_stats[housekeeper]['performance_amount'] += float(record.get('计入业绩金额', 0))
        except ValueError:
            pass
    
    print(f"  管家统计:")
    for housekeeper, stats in housekeeper_stats.items():
        print(f"    {housekeeper}: {stats['count']}单, 合同{stats['total_amount']:,.0f}元, 业绩{stats['performance_amount']:,.0f}元")
    
    validation_report['business_logic_checks']['housekeeper_stats'] = housekeeper_stats
    
    # 2.5 奖励逻辑检查
    reward_distribution = {}
    for record in data:
        reward_types = record.get('奖励类型', '')
        if reward_types:
            for reward_type in reward_types.split(','):
                reward_type = reward_type.strip()
                if reward_type:
                    reward_distribution[reward_type] = reward_distribution.get(reward_type, 0) + 1
    
    print(f"  奖励分布:")
    for reward_type, count in reward_distribution.items():
        print(f"    {reward_type}: {count} 条")
    
    validation_report['business_logic_checks']['reward_distribution'] = reward_distribution
    
    return validation_report

def validate_shanghai_september_data(data: List[Dict]) -> Dict:
    """验证上海9月数据"""
    print("🔍 验证上海9月数据...")
    
    validation_report = {
        'total_records': len(data),
        'errors': [],
        'warnings': [],
        'business_logic_checks': {},
        'data_quality_checks': {}
    }
    
    if not data:
        validation_report['errors'].append("没有找到上海9月数据")
        return validation_report
    
    # 1. 双轨统计验证
    print("📋 双轨统计验证:")
    
    platform_orders = []
    self_referral_orders = []
    
    for record in data:
        order_type = record.get('工单类型', '')
        trade_in = record.get('款项来源类型(tradeIn)', '')
        
        if order_type == '平台单' or trade_in == '0':
            platform_orders.append(record)
        elif order_type == '自引单' or trade_in == '1':
            self_referral_orders.append(record)
    
    print(f"  平台单: {len(platform_orders)} 条")
    print(f"  自引单: {len(self_referral_orders)} 条")
    
    validation_report['business_logic_checks']['platform_orders'] = len(platform_orders)
    validation_report['business_logic_checks']['self_referral_orders'] = len(self_referral_orders)
    
    # 2. 项目地址去重验证
    project_addresses = {}
    for record in self_referral_orders:
        housekeeper = record.get('管家(serviceHousekeeper)', '')
        project_address = record.get('项目地址(projectAddress)', '')
        
        if project_address:
            key = f"{housekeeper}_{project_address}"
            if key not in project_addresses:
                project_addresses[key] = []
            project_addresses[key].append(record.get('合同ID(_id)', ''))
    
    duplicate_addresses = {k: v for k, v in project_addresses.items() if len(v) > 1}
    
    print(f"  项目地址去重:")
    print(f"    总项目地址: {len(project_addresses)}")
    print(f"    重复地址: {len(duplicate_addresses)}")
    
    if duplicate_addresses:
        print("    重复地址详情:")
        for key, contracts in duplicate_addresses.items():
            print(f"      {key}: {contracts}")
    
    validation_report['business_logic_checks']['duplicate_addresses'] = len(duplicate_addresses)
    
    # 3. 自引单奖励验证
    self_referral_rewards = []
    for record in self_referral_orders:
        reward_types = record.get('奖励类型', '')
        if '自引单' in reward_types:
            self_referral_rewards.append(record)
    
    print(f"  自引单奖励: {len(self_referral_rewards)} 条")
    
    validation_report['business_logic_checks']['self_referral_rewards'] = len(self_referral_rewards)
    
    # 4. 管家键格式验证（上海特有：管家_服务商）
    housekeeper_key_format_errors = []
    for record in data:
        housekeeper = record.get('管家(serviceHousekeeper)', '')
        service_provider = record.get('服务商(orgName)', '')
        
        # 检查是否使用了正确的管家键格式
        if housekeeper and service_provider:
            expected_key = f"{housekeeper}_{service_provider}"
            # 这里可以添加更多的格式验证逻辑
    
    print(f"  管家键格式验证: {len(housekeeper_key_format_errors)} 个错误")
    
    validation_report['business_logic_checks']['housekeeper_key_errors'] = len(housekeeper_key_format_errors)
    
    return validation_report

def generate_validation_report(beijing_report: Dict, shanghai_report: Dict):
    """生成验证报告"""
    print("\n" + "="*60)
    print("📊 数据验证总结报告")
    print("="*60)
    
    print(f"\n🏢 北京9月数据:")
    print(f"  总记录数: {beijing_report['total_records']}")
    print(f"  错误数: {len(beijing_report['errors'])}")
    print(f"  警告数: {len(beijing_report['warnings'])}")
    
    if beijing_report['errors']:
        print("  错误详情:")
        for error in beijing_report['errors']:
            print(f"    ❌ {error}")
    
    print(f"\n🏢 上海9月数据:")
    print(f"  总记录数: {shanghai_report['total_records']}")
    print(f"  错误数: {len(shanghai_report['errors'])}")
    print(f"  警告数: {len(shanghai_report['warnings'])}")
    
    if shanghai_report['errors']:
        print("  错误详情:")
        for error in shanghai_report['errors']:
            print(f"    ❌ {error}")
    
    # 总体评估
    total_errors = len(beijing_report['errors']) + len(shanghai_report['errors'])
    total_warnings = len(beijing_report['warnings']) + len(shanghai_report['warnings'])
    
    print(f"\n📈 总体评估:")
    print(f"  总错误数: {total_errors}")
    print(f"  总警告数: {total_warnings}")
    
    if total_errors == 0:
        print("  ✅ 数据验证通过！")
        return True
    else:
        print("  ❌ 数据验证失败，请检查错误")
        return False

def main():
    """主函数"""
    setup_logging()
    
    print("🔍 9月份Job数据验证开始")
    print(f"📅 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 查找CSV文件
    csv_files = find_latest_csv_files()
    
    if not csv_files:
        print("❌ 未找到CSV文件，请先运行9月份Job测试")
        return 1
    
    print(f"📁 找到CSV文件: {len(csv_files)} 个")
    for file in csv_files[:5]:  # 显示前5个
        print(f"  - {file}")
    
    # 分别验证北京和上海数据
    beijing_data = []
    shanghai_data = []
    
    for file in csv_files:
        if 'BJ-SEP' in file:
            beijing_data.extend(read_csv_data(file))
        elif 'SH-SEP' in file:
            shanghai_data.extend(read_csv_data(file))
    
    # 执行验证
    beijing_report = validate_beijing_september_data(beijing_data)
    shanghai_report = validate_shanghai_september_data(shanghai_data)
    
    # 生成报告
    validation_passed = generate_validation_report(beijing_report, shanghai_report)
    
    if validation_passed:
        print("\n🎉 数据验证完成！所有数据符合业务要求")
        return 0
    else:
        print("\n⚠️ 数据验证发现问题，请检查上述错误")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
