#!/usr/bin/env python3
"""
调试处理管道问题
"""

import os
import sys
import logging

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline
from modules.core.data_models import ContractData

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def debug_processing():
    """调试处理流程"""
    
    # 测试数据
    test_data = [
        {
            '合同ID(_id)': '2025010812345678',
            '管家(serviceHousekeeper)': '张三',
            '服务商(orgName)': '北京优质服务商',
            '合同金额(adjustRefundMoney)': 15000,
            '支付金额(paidAmount)': 10000,
            '工单编号(serviceAppointmentNum)': 'WO-2025-001',
            '款项来源类型(tradeIn)': 0,
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 10:00:00'
        },
        {
            '合同ID(_id)': '2025010812345679',
            '管家(serviceHousekeeper)': '张三',
            '服务商(orgName)': '北京优质服务商',
            '合同金额(adjustRefundMoney)': 25000,
            '支付金额(paidAmount)': 20000,
            '工单编号(serviceAppointmentNum)': 'WO-2025-001',
            '款项来源类型(tradeIn)': 0,
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 11:00:00'
        },
        {
            '合同ID(_id)': '2025010812345680',
            '管家(serviceHousekeeper)': '李四',
            '服务商(orgName)': '北京优质服务商',
            '合同金额(adjustRefundMoney)': 35000,
            '支付金额(paidAmount)': 30000,
            '工单编号(serviceAppointmentNum)': 'WO-2025-002',
            '款项来源类型(tradeIn)': 0,
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 12:00:00'
        }
    ]
    
    print(f"输入数据: {len(test_data)} 条")
    for i, data in enumerate(test_data):
        print(f"  {i+1}. {data['合同ID(_id)']} - {data['管家(serviceHousekeeper)']} - {data['合同金额(adjustRefundMoney)']}")
    
    # 创建处理管道
    pipeline, config, store = create_standard_pipeline(
        config_key="BJ-2025-06",
        activity_code="BJ-JUN",
        city="BJ",
        housekeeper_key_format="管家",
        storage_type="sqlite",
        enable_project_limit=True,
        db_path="debug_performance_data.db"
    )
    
    print(f"\n开始逐条处理...")
    
    # 逐条处理，查看每条的处理结果
    for i, contract_dict in enumerate(test_data):
        print(f"\n--- 处理第 {i+1} 条记录 ---")
        print(f"合同ID: {contract_dict['合同ID(_id)']}")
        
        try:
            # 1. 转换为标准数据结构
            contract_data = ContractData.from_dict(contract_dict)
            print(f"✅ 数据转换成功")
            
            # 2. 检查是否已存在
            exists = store.contract_exists(contract_data.contract_id, config.activity_code)
            print(f"去重检查: {'已存在' if exists else '不存在'}")
            
            if exists:
                print(f"⏭️ 跳过已存在的合同")
                continue
            
            # 3. 获取管家统计
            housekeeper_key = contract_data.housekeeper  # 简化版
            hk_stats = store.get_housekeeper_stats(housekeeper_key, config.activity_code)
            print(f"管家统计: {hk_stats.contract_count}单, {hk_stats.total_amount}元")
            
            # 4. 计算业绩金额
            performance_amount = contract_data.contract_amount
            print(f"业绩金额: {performance_amount}")
            
            # 5. 计算奖励
            rewards = pipeline.reward_calculator.calculate(contract_data, hk_stats)
            print(f"奖励: {[r.reward_name for r in rewards]}")
            
            # 6. 构建记录
            record = pipeline.record_builder.build(
                contract_data=contract_data,
                housekeeper_stats=hk_stats,
                rewards=rewards,
                performance_amount=performance_amount,
                contract_sequence=i + 1
            )
            print(f"✅ 记录构建成功")
            
            # 7. 保存记录
            store.save_performance_record(record)
            print(f"✅ 记录保存成功")
            
        except Exception as e:
            import traceback
            print(f"❌ 处理失败: {e}")
            print(f"详细错误: {traceback.format_exc()}")
    
    print(f"\n=== 最终结果 ===")
    all_records = store.get_all_records(config.activity_code)
    print(f"数据库中的记录: {len(all_records)} 条")
    for record in all_records:
        print(f"  {record['contract_id']} - {record['housekeeper']} - {record['contract_amount']}")


if __name__ == "__main__":
    # 清理旧的调试数据库
    if os.path.exists("debug_performance_data.db"):
        os.remove("debug_performance_data.db")
    
    debug_processing()
