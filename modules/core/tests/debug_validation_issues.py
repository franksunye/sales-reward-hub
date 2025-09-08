"""
销售激励系统重构 - 调试验证问题
版本: v1.0
创建日期: 2025-01-08

调试深度功能验证中发现的问题
"""

import tempfile
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline


def debug_beijing_june_lucky_number():
    """调试北京6月幸运数字问题"""
    print("=== 调试北京6月幸运数字问题 ===")
    
    test_data = [
        # 幸运数字8，万元以上
        {
            '合同ID(_id)': '2025010812345678',
            '管家(serviceHousekeeper)': '张三',
            '服务商(orgName)': '北京优质服务',
            '合同金额(adjustRefundMoney)': 15000,
            '支付金额(paidAmount)': 12000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ001',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 10:00:00'
        },
        # 幸运数字8，万元以下
        {
            '合同ID(_id)': '2025010812345688',
            '管家(serviceHousekeeper)': '李四',
            '服务商(orgName)': '北京优质服务',
            '合同金额(adjustRefundMoney)': 8000,
            '支付金额(paidAmount)': 6000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ002',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 11:00:00'
        },
        # 非幸运数字
        {
            '合同ID(_id)': '2025010812345679',
            '管家(serviceHousekeeper)': '王五',
            '服务商(orgName)': '北京优质服务',
            '合同金额(adjustRefundMoney)': 12000,
            '支付金额(paidAmount)': 10000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ003',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 12:00:00'
        }
    ]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()
        
        try:
            # 创建处理管道
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-06",
                activity_code="BJ-JUN",
                city="BJ",
                db_path=temp_db.name,
                enable_project_limit=True
            )
            
            # 处理数据
            processed_records = pipeline.process(test_data)
            
            print(f"处理记录数: {len(processed_records)}")
            
            # 详细分析每条记录
            for i, record in enumerate(processed_records):
                print(f"\n记录 {i+1}:")
                print(f"  合同ID: {record.contract_data.contract_id}")
                print(f"  管家: {record.housekeeper_stats.housekeeper}")
                print(f"  合同金额: {record.contract_data.contract_amount}")
                print(f"  奖励数量: {len(record.rewards)}")
                
                for j, reward in enumerate(record.rewards):
                    print(f"    奖励{j+1}: {reward.reward_type} - {reward.reward_name}")
                    if '接好运' in reward.reward_name:
                        print(f"      *** 这是幸运数字奖励 ***")
            
            # 统计幸运数字奖励
            lucky_records = [r for r in processed_records if any('接好运' in reward.reward_name for reward in r.rewards)]
            print(f"\n幸运数字奖励统计:")
            print(f"  期望: 2个（合同ID末位为8的）")
            print(f"  实际: {len(lucky_records)}个")
            
            # 分析为什么会有3个
            print(f"\n详细分析:")
            for record in processed_records:
                contract_id = record.contract_data.contract_id
                last_digit = contract_id[-1]
                has_lucky = any('接好运' in reward.reward_name for reward in record.rewards)
                print(f"  {contract_id} (末位{last_digit}): {'有' if has_lucky else '无'}幸运奖励")
        
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


def debug_beijing_september_amount_limit():
    """调试北京9月工单金额上限问题"""
    print("\n=== 调试北京9月工单金额上限问题 ===")
    
    test_data = [
        # 超过5万上限的合同
        {
            '合同ID(_id)': '2025010912345680',
            '管家(serviceHousekeeper)': '赵六',
            '服务商(orgName)': '北京优质服务',
            '合同金额(adjustRefundMoney)': 80000,  # 8万，超过5万上限
            '支付金额(paidAmount)': 60000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ004',
            '工单编号(serviceAppointmentNum)': 'PROJECT001',  # 添加工单编号
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-09 10:00:00'
        },
        # 未超过上限的合同
        {
            '合同ID(_id)': '2025010912345681',
            '管家(serviceHousekeeper)': '赵六',
            '服务商(orgName)': '北京优质服务',
            '合同金额(adjustRefundMoney)': 30000,  # 3万，未超过上限
            '支付金额(paidAmount)': 25000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ004',
            '工单编号(serviceAppointmentNum)': 'PROJECT002',  # 添加工单编号
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-09 11:00:00'
        }
    ]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()
        
        try:
            # 创建处理管道
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-09",
                activity_code="BJ-SEP",
                city="BJ",
                db_path=temp_db.name,
                enable_project_limit=True
            )
            
            # 处理数据
            processed_records = pipeline.process(test_data)
            
            print(f"处理记录数: {len(processed_records)}")
            
            # 详细分析每条记录
            for i, record in enumerate(processed_records):
                print(f"\n记录 {i+1}:")
                print(f"  合同ID: {record.contract_data.contract_id}")
                print(f"  合同金额: {record.contract_data.contract_amount}")
                print(f"  计入业绩金额: {record.performance_amount}")
                
                if record.contract_data.contract_amount > 50000:
                    print(f"  *** 这是超过5万上限的合同 ***")
                    if record.performance_amount == 50000:
                        print(f"  ✅ 正确：计入业绩金额被限制为5万")
                    else:
                        print(f"  ❌ 错误：计入业绩金额应该是5万，实际是{record.performance_amount}")
            
            # 统计超限处理
            over_limit_records = [r for r in processed_records 
                                if r.performance_amount == 50000 and r.contract_data.contract_amount > 50000]
            print(f"\n工单金额上限处理统计:")
            print(f"  期望: 1个（8万合同被限制为5万）")
            print(f"  实际: {len(over_limit_records)}个")
        
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


def debug_duplicate_contract_handling():
    """调试重复合同ID处理问题"""
    print("\n=== 调试重复合同ID处理问题 ===")
    
    duplicate_data = [
        {
            '合同ID(_id)': '2025010912345888',
            '管家(serviceHousekeeper)': '测试管家1',
            '服务商(orgName)': '测试服务商',
            '合同金额(adjustRefundMoney)': 10000,
            '支付金额(paidAmount)': 8000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'TEST001',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 10:00:00'
        },
        {
            '合同ID(_id)': '2025010912345888',  # 重复ID
            '管家(serviceHousekeeper)': '测试管家2',
            '服务商(orgName)': '测试服务商',
            '合同金额(adjustRefundMoney)': 12000,
            '支付金额(paidAmount)': 10000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'TEST002',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 11:00:00'
        }
    ]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()
        
        try:
            # 创建处理管道
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-06",
                activity_code="BJ-JUN",
                city="BJ",
                db_path=temp_db.name
            )
            
            # 处理数据
            processed_records = pipeline.process(duplicate_data)
            
            print(f"输入记录数: {len(duplicate_data)}")
            print(f"处理记录数: {len(processed_records)}")
            
            if len(processed_records) == 1:
                print("✅ 重复合同ID去重正确")
                record = processed_records[0]
                print(f"  处理的合同: {record.contract_data.contract_id}")
                print(f"  管家: {record.housekeeper_stats.housekeeper}")
                print(f"  合同金额: {record.contract_data.contract_amount}")
            else:
                print("❌ 重复合同ID去重失败")
                for i, record in enumerate(processed_records):
                    print(f"  记录{i+1}: {record.contract_data.contract_id} - {record.housekeeper_stats.housekeeper}")
        
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


def main():
    """主函数"""
    print("销售激励系统重构 - 调试验证问题")
    print("=" * 60)
    
    # 调试各个问题
    debug_beijing_june_lucky_number()
    debug_beijing_september_amount_limit()
    debug_duplicate_contract_handling()
    
    print("\n" + "=" * 60)
    print("调试完成！")
    print("\n根据调试结果，需要检查：")
    print("1. 幸运数字逻辑是否正确（为什么3个合同都有幸运奖励）")
    print("2. 工单金额上限逻辑是否启用（为什么8万合同没有被限制）")
    print("3. 重复合同去重逻辑是否正常工作")


if __name__ == "__main__":
    main()
