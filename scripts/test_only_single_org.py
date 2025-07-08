#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全测试单个服务商的待预约工单提醒
只发送到测试群，不影响生产环境
"""

import logging
from modules.log_config import setup_logging
from modules.request_module import send_request_with_managed_session
from modules.notification_module import post_text_to_webhook, post_markdown_v2_to_webhook
from modules.config import API_URL_PENDING_ORDERS_REMINDER, WEBHOOK_URL_DEFAULT
from jobs import group_orders_by_org, format_pending_orders_message, format_pending_orders_message_text

# 设置日志
setup_logging()

# 测试专用webhook（使用默认群作为测试群）
TEST_WEBHOOK_URL = WEBHOOK_URL_DEFAULT

def test_single_org_reminder_safe(target_org_name=None, max_orders=3):
    """
    安全测试单个服务商的工单提醒（只发送到测试群）
    
    Args:
        target_org_name: 目标服务商名称，如果为None则选择第一个有工单的服务商
        max_orders: 最大工单数量，用于限制测试消息长度
    """
    print(f"🧪 安全测试模式 - 只发送到测试群")
    print(f"目标服务商: {target_org_name or '自动选择'}")
    print(f"最大工单数: {max_orders}")
    print(f"测试群: 北京运营企微群")
    print("-" * 50)
    
    try:
        # 1. 获取数据
        print("正在获取待预约工单数据...")
        response = send_request_with_managed_session(API_URL_PENDING_ORDERS_REMINDER)
        
        if not response or 'data' not in response:
            print("✗ API请求失败")
            return False
        
        orders_data = response['data']['rows']
        print(f"✓ 获取到 {len(orders_data)} 条工单数据")
        
        if not orders_data:
            print("当前没有待预约工单")
            return False
        
        # 2. 分组数据
        grouped_orders = group_orders_by_org(orders_data)
        print(f"✓ 分组成功，共 {len(grouped_orders)} 个服务商")
        
        # 3. 选择目标服务商
        if target_org_name:
            if target_org_name not in grouped_orders:
                print(f"✗ 指定的服务商 '{target_org_name}' 没有待预约工单")
                print("可选的服务商:")
                for org in grouped_orders.keys():
                    print(f"  - {org}")
                return False
            selected_org = target_org_name
        else:
            # 自动选择第一个服务商
            selected_org = list(grouped_orders.keys())[0]
        
        selected_orders = grouped_orders[selected_org]
        print(f"✓ 选择服务商: {selected_org}")
        print(f"✓ 该服务商工单数量: {len(selected_orders)}")
        
        # 4. 限制工单数量（用于测试）
        if len(selected_orders) > max_orders:
            selected_orders = selected_orders[:max_orders]
            print(f"✓ 限制为前 {max_orders} 个工单进行测试")
        
        # 5. 格式化消息
        message = format_pending_orders_message(selected_org, selected_orders)
        
        # 添加测试标识
        test_message = f"🧪 **测试消息** - 请忽略\n\n{message}\n\n---\n*这是一条测试消息，请忽略*"
        
        print("\n生成的测试消息内容:")
        print("=" * 60)
        print(test_message)
        print("=" * 60)
        
        # 6. 确认发送到测试群
        print(f"\n🧪 测试配置:")
        print(f"  原始服务商: {selected_org}")
        print(f"  实际发送到: 北京运营企微群（测试群）")
        print(f"  测试Webhook: {TEST_WEBHOOK_URL[:50]}...")
        
        # 7. 选择发送格式和确认发送
        print(f"\n准备发送测试消息到测试群...")
        print("选择消息格式:")
        print("1. 表格格式 (markdown_v2)")
        print("2. 文本格式 (text)")
        format_choice = input("请选择格式 (1/2): ").strip()
        
        confirm = input("确认发送到测试群？(y/N): ").strip().lower()
        
        if confirm != 'y':
            print("已取消发送")
            return False
        
        # 8. 发送消息到测试群
        print("正在发送测试消息到测试群...")
        if format_choice == "1":
            post_markdown_v2_to_webhook(test_message, TEST_WEBHOOK_URL)
            print("✓ 表格格式测试消息发送完成")
        else:
            # 使用文本格式
            text_message = format_pending_orders_message_text(selected_org, selected_orders)
            test_text_message = f"🧪 测试消息 - 请忽略\n\n{text_message}\n\n---\n*这是一条测试消息，请忽略*"

            print("\n生成的文本格式消息内容:")
            print("=" * 60)
            print(test_text_message)
            print("=" * 60)

            post_text_to_webhook(test_text_message, TEST_WEBHOOK_URL)
            print("✓ 文本格式测试消息发送完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def list_available_orgs():
    """列出所有有待预约工单的服务商"""
    print("正在获取服务商列表...")
    
    try:
        response = send_request_with_managed_session(API_URL_PENDING_ORDERS_REMINDER)
        if not response or 'data' not in response:
            print("✗ 无法获取数据")
            return
        
        orders_data = response['data']['rows']
        grouped_orders = group_orders_by_org(orders_data)
        
        print(f"\n当前有待预约工单的服务商 (共{len(grouped_orders)}个):")
        print("-" * 60)
        
        for i, (org_name, orders) in enumerate(grouped_orders.items(), 1):
            print(f"{i:2d}. {org_name}")
            print(f"     工单数量: {len(orders)}")
        
    except Exception as e:
        print(f"✗ 获取服务商列表失败: {e}")

def main():
    print("🧪 安全测试工具 - 待预约工单提醒")
    print("=" * 60)
    print("⚠️  所有消息只会发送到测试群（北京运营企微群）")
    print("⚠️  不会影响服务商的专属群")
    print("=" * 60)
    
    while True:
        print("\n选择操作:")
        print("1. 列出所有有工单的服务商")
        print("2. 测试指定服务商")
        print("3. 测试第一个服务商（自动选择）")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            list_available_orgs()
            
        elif choice == "2":
            org_name = input("请输入服务商名称: ").strip()
            if org_name:
                max_orders = input("最大工单数量 (默认3): ").strip()
                max_orders = int(max_orders) if max_orders.isdigit() else 3
                test_single_org_reminder_safe(org_name, max_orders)
            else:
                print("服务商名称不能为空")
                
        elif choice == "3":
            max_orders = input("最大工单数量 (默认3): ").strip()
            max_orders = int(max_orders) if max_orders.isdigit() else 3
            test_single_org_reminder_safe(None, max_orders)
            
        elif choice == "4":
            print("退出")
            break
            
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
