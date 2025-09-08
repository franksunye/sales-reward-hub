"""
调试北京9月个人序列幸运数字问题
"""

import tempfile
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline


def debug_beijing_september_personal_sequence():
    """调试北京9月个人序列幸运数字"""
    print("=== 调试北京9月个人序列幸运数字 ===")
    
    # 测试数据：同一管家的5个合同
    test_data = [
        # 第1个合同
        {
            '合同ID(_id)': '2025090912345680',
            '管家(serviceHousekeeper)': '北京赵六',
            '服务商(orgName)': '北京精品服务A',
            '合同金额(adjustRefundMoney)': 80000,
            '支付金额(paidAmount)': 65000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ004',
            '工单编号(serviceAppointmentNum)': 'WD005',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-09-09 10:00:00'
        },
        # 第2个合同（历史合同）
        {
            '合同ID(_id)': '2025090912345681',
            'pcContractdocNum': 'PC2024123001',
            '管家(serviceHousekeeper)': '北京赵六',
            '服务商(orgName)': '北京精品服务A',
            '合同金额(adjustRefundMoney)': 35000,
            '支付金额(paidAmount)': 28000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ004',
            '工单编号(serviceAppointmentNum)': 'WD006',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-09-09 11:00:00'
        },
        # 第3个合同
        {
            '合同ID(_id)': '2025090912345682',
            '管家(serviceHousekeeper)': '北京赵六',
            '服务商(orgName)': '北京精品服务A',
            '合同金额(adjustRefundMoney)': 22000,
            '支付金额(paidAmount)': 18000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ004',
            '工单编号(serviceAppointmentNum)': 'WD007',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-09-09 12:00:00'
        },
        # 第4个合同
        {
            '合同ID(_id)': '2025090912345683',
            '管家(serviceHousekeeper)': '北京赵六',
            '服务商(orgName)': '北京精品服务A',
            '合同金额(adjustRefundMoney)': 28000,
            '支付金额(paidAmount)': 22000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ004',
            '工单编号(serviceAppointmentNum)': 'WD008',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-09-09 13:00:00'
        },
        # 第5个合同（应该有幸运奖励）
        {
            '合同ID(_id)': '2025090912345684',
            '管家(serviceHousekeeper)': '北京赵六',
            '服务商(orgName)': '北京精品服务A',
            '合同金额(adjustRefundMoney)': 30000,
            '支付金额(paidAmount)': 24000,
            '款项来源类型(tradeIn)': 0,
            '管家ID(serviceHousekeeperId)': 'BJ004',
            '工单编号(serviceAppointmentNum)': 'WD009',
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-09-09 14:00:00'
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
                enable_project_limit=True,
                enable_historical_contracts=True
            )
            
            print(f"配置信息:")
            print(f"  配置对象: {type(config)}")
            # 直接查看配置内容
            from modules.core.config_adapter import ConfigAdapter
            raw_config = ConfigAdapter.get_reward_config("BJ-2025-09")
            print(f"  幸运数字: {raw_config.get('lucky_number', 'None')}")
            print(f"  幸运策略: {raw_config.get('lucky_strategy', 'None')}")
            print(f"  幸运奖励: {raw_config.get('lucky_rewards', {})}")
            
            # 处理数据
            processed_records = pipeline.process(test_data)
            
            print(f"\n处理结果: {len(processed_records)}条记录")
            
            # 详细分析每条记录
            for i, record in enumerate(processed_records):
                print(f"\n记录 {i+1}:")
                print(f"  合同ID: {record.contract_data.contract_id}")
                print(f"  管家: {record.housekeeper_stats.housekeeper}")
                print(f"  合同序号: {record.housekeeper_stats.contract_count}")
                print(f"  是否历史合同: {record.contract_data.is_historical}")
                print(f"  奖励数量: {len(record.rewards)}")
                
                for j, reward in enumerate(record.rewards):
                    print(f"    奖励{j+1}: {reward.reward_type} - {reward.reward_name}")
                    if '接好运' in reward.reward_name:
                        print(f"      *** 这是幸运数字奖励 ***")
                
                # 检查第5个合同
                if record.housekeeper_stats.contract_count == 5:
                    print(f"  *** 这是第5个合同，应该有幸运奖励 ***")
                    has_lucky = any('接好运' in reward.reward_name for reward in record.rewards)
                    print(f"  实际是否有幸运奖励: {has_lucky}")
            
            # 统计幸运数字奖励
            lucky_records = [r for r in processed_records if any('接好运' in reward.reward_name for reward in r.rewards)]
            print(f"\n幸运数字奖励统计:")
            print(f"  期望: 1个（第5个合同）")
            print(f"  实际: {len(lucky_records)}个")
            
            if len(lucky_records) == 0:
                print(f"\n❌ 问题：没有找到幸运数字奖励")
                print(f"可能原因：")
                print(f"1. 个人序列幸运数字逻辑未正确实现")
                print(f"2. 配置中的幸运策略不正确")
                print(f"3. 第5个合同的序号计算错误")
            else:
                print(f"\n✅ 找到幸运数字奖励")
                for record in lucky_records:
                    print(f"  合同ID: {record.contract_data.contract_id}, 序号: {record.housekeeper_stats.contract_count}")
        
        finally:
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)


def main():
    """主函数"""
    print("北京9月个人序列幸运数字调试")
    print("=" * 50)
    
    debug_beijing_september_personal_sequence()
    
    print("\n" + "=" * 50)
    print("调试完成！")


if __name__ == "__main__":
    main()
