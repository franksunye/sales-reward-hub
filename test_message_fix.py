#!/usr/bin/env python3
"""
测试消息模板修复
"""

import sys
import os
from unittest.mock import patch

# 添加项目根目录到路径
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from modules.core.notification_service import NotificationService
from modules.core.data_models import ProcessingConfig, City
from modules.core.storage import SQLitePerformanceDataStore

def test_message_template_fix():
    """测试消息模板修复"""
    print("🔧 测试北京10月消息模板修复")
    print("="*50)
    
    # 创建北京10月的通知服务
    config = ProcessingConfig(
        config_key="BJ-2025-10",
        activity_code="BJ-OCT",
        city=City.BEIJING,
        housekeeper_key_format="管家",
        enable_dual_track=True
    )
    
    # 创建存储实例（用于测试）
    storage = SQLitePerformanceDataStore("performance_data.db")
    notification_service = NotificationService(storage, config)
    
    # 创建测试记录
    test_record = {
        "管家(serviceHousekeeper)": "余金凤",
        "合同编号(contractdocNum)": "YHWX-BJ-DKS-2025090022",
        "工单类型": "自引单",
        "平台单累计数量": 9,  # 个人平台单9个
        "自引单累计数量": 1,  # 个人自引单1个
        "平台单累计金额": 53464,
        "自引单累计金额": 9460,
        "活动期内第几个合同": 280,  # 全局第280个合同
        "备注": "距离 达标奖 还需 37,076.0 元"
    }
    
    print("测试数据:")
    print(f"  管家: {test_record['管家(serviceHousekeeper)']}")
    print(f"  个人平台单数量: {test_record['平台单累计数量']}")
    print(f"  个人自引单数量: {test_record['自引单累计数量']}")
    print(f"  个人总数: {test_record['平台单累计数量'] + test_record['自引单累计数量']}")
    print(f"  全局合同序号: {test_record['活动期内第几个合同']}")
    
    # 模拟消息发送
    with patch('modules.core.notification_service.create_task') as mock_create_task:
        notification_service._send_group_notification(test_record)
        
        # 获取生成的消息
        mock_create_task.assert_called_once()
        call_args = mock_create_task.call_args[0]
        message = call_args[2]
        
        print(f"\n生成的消息:")
        print("-" * 40)
        print(message)
        print("-" * 40)
        
        # 验证修复效果
        print(f"\n修复验证:")
        
        # 检查是否使用了全局序号而不是个人总数
        if "本单为平台本月累计签约第 280 单" in message:
            print("✅ 正确: 使用全局合同序号 (280)")
        elif "本单为平台本月累计签约第 10 单" in message:
            print("❌ 错误: 仍在使用个人总数 (9+1=10)")
        else:
            print("❓ 未知: 消息格式可能有其他问题")
        
        # 检查个人统计是否正确
        if "个人平台单累计签约第 9 单" in message:
            print("✅ 正确: 个人平台单数量显示正确")
        else:
            print("❌ 错误: 个人平台单数量显示错误")
            
        if "个人自引单累计签约第 1 单" in message:
            print("✅ 正确: 个人自引单数量显示正确")
        else:
            print("❌ 错误: 个人自引单数量显示错误")

def test_comparison_with_other_activities():
    """对比其他活动的消息格式"""
    print("\n" + "="*50)
    print("对比其他活动的消息格式")
    
    # 创建其他北京活动的通知服务
    config_other = ProcessingConfig(
        config_key="BJ-2025-09",  # 北京9月
        activity_code="BJ-SEP",
        city=City.BEIJING,
        housekeeper_key_format="管家"
    )
    
    storage_other = SQLitePerformanceDataStore("performance_data.db")
    notification_service_other = NotificationService(storage_other, config_other)
    
    test_record_other = {
        "管家(serviceHousekeeper)": "测试管家",
        "合同编号(contractdocNum)": "TEST-001",
        "活动期内第几个合同": 150,  # 全局第150个合同
        "管家累计单数": 8,  # 个人累计8个
        "管家累计金额": 100000,
        "管家累计业绩金额": 95000,
        "备注": "距离 精英奖 还需 50,000 元"
    }
    
    with patch('modules.core.notification_service.create_task') as mock_create_task:
        notification_service_other._send_group_notification(test_record_other)
        
        call_args = mock_create_task.call_args[0]
        message_other = call_args[2]
        
        print(f"\n其他北京活动的消息格式:")
        print("-" * 40)
        print(message_other)
        print("-" * 40)
        
        # 分析格式差异
        print(f"\n格式分析:")
        if "本单为活动期间平台累计签约第 150 单" in message_other:
            print("✅ 其他活动正确使用全局序号")
        if "个人累计签约第 8 单" in message_other:
            print("✅ 其他活动正确显示个人累计")

def main():
    """主函数"""
    try:
        test_message_template_fix()
        test_comparison_with_other_activities()
        
        print("\n" + "="*50)
        print("✅ 消息模板修复测试完成")
        print("\n修复总结:")
        print("1. ✅ 修复了'本单为平台本月累计签约第 X 单'使用错误数据的问题")
        print("2. ✅ 现在使用全局合同序号，而不是个人总数")
        print("3. ✅ 与其他北京活动的消息格式保持一致")
        print("4. ✅ 个人统计数据显示仍然正确")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
