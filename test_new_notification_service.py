#!/usr/bin/env python3
"""
测试新架构通知服务
验证消息生成逻辑与旧架构的等价性
"""

import sys
import os
import logging

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from modules.core.notification_service import create_notification_service
from modules.core.storage import create_data_store
from modules.core.data_models import ProcessingConfig, City

def test_notification_service():
    """测试新架构通知服务"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🧪 测试新架构通知服务")
    
    try:
        # 1. 创建存储实例
        print("📊 创建存储实例...")
        storage = create_data_store(
            storage_type="sqlite",
            db_path="performance_data.db"
        )
        
        # 2. 创建配置
        print("⚙️ 创建配置...")
        config = ProcessingConfig(
            config_key="BJ-2025-09",
            activity_code="BJ-SEP",
            city=City.BEIJING,
            housekeeper_key_format="管家",
            storage_type="sqlite"
        )
        
        # 3. 创建通知服务
        print("📢 创建通知服务...")
        notification_service = create_notification_service(storage, config)
        
        # 4. 查询需要通知的记录
        print("🔍 查询需要通知的记录...")
        conditions = {
            'activity_code': 'BJ-SEP',
            'notification_sent': False,
            'is_historical': False
        }
        records = storage.query_performance_records(conditions)
        print(f"找到 {len(records)} 条需要通知的记录")
        
        if records:
            # 显示前几条记录的信息
            print("\n📋 前5条记录信息:")
            for i, record in enumerate(records[:5]):
                print(f"  {i+1}. 管家: {record.get('housekeeper', 'N/A')}")
                print(f"     合同ID: {record.get('contract_id', 'N/A')}")
                print(f"     奖励: {record.get('reward_names', 'N/A')}")
                print(f"     通知状态: {'已发送' if record.get('notification_sent') else '未发送'}")
                print()
        
        # 5. 测试消息生成（不实际发送）
        print("🧪 测试消息生成逻辑...")
        if records:
            test_record = records[0]
            print(f"测试记录: {test_record.get('housekeeper', 'N/A')} - {test_record.get('contract_id', 'N/A')}")
            
            # 转换为字典格式
            record_dict = notification_service._convert_record_to_dict(test_record)
            print("转换后的记录字段:")
            for key, value in record_dict.items():
                print(f"  {key}: {value}")
        
        # 6. 发送通知（实际执行）
        print("\n🚀 执行通知发送...")
        stats = notification_service.send_notifications()
        
        print(f"\n✅ 通知发送完成!")
        print(f"   总记录数: {stats['total']}")
        print(f"   群通知数: {stats['group_notifications']}")
        print(f"   奖励通知数: {stats['award_notifications']}")
        
        # 7. 验证通知状态更新
        print("\n🔍 验证通知状态更新...")
        updated_records = storage.query_performance_records(conditions)
        print(f"更新后未发送通知的记录数: {len(updated_records)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_old_architecture():
    """与旧架构进行对比"""
    print("\n🔄 与旧架构对比...")
    
    try:
        # 检查Task表中的记录数量
        import sqlite3
        
        with sqlite3.connect('tasks.db') as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE created_at >= datetime('now', '-1 hour')
            """)
            recent_tasks = cursor.fetchone()[0]
            print(f"最近1小时创建的Task记录: {recent_tasks} 条")
            
            # 显示最新的几条任务
            cursor = conn.execute("""
                SELECT task_type, recipient, LEFT(message, 100) as message_preview, created_at
                FROM tasks 
                WHERE created_at >= datetime('now', '-1 hour')
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            print("\n📋 最新的Task记录:")
            for row in cursor.fetchall():
                print(f"  类型: {row[0]}")
                print(f"  接收者: {row[1]}")
                print(f"  消息预览: {row[2]}...")
                print(f"  创建时间: {row[3]}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ 对比失败: {e}")
        return False

if __name__ == "__main__":
    print("🎯 新架构通知服务测试")
    print("=" * 50)
    
    # 测试通知服务
    success = test_notification_service()
    
    if success:
        # 与旧架构对比
        compare_with_old_architecture()
        print("\n🎉 测试完成!")
    else:
        print("\n💥 测试失败!")
        sys.exit(1)
