#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手动测试单个服务商的待预约工单提醒
用于小范围验证消息发送功能
"""

import logging
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.log_config import setup_logging
from modules.request_module import send_request_with_managed_session
from modules.notification_module import post_text_to_webhook, post_markdown_v2_to_webhook
from modules.config import API_URL_PENDING_ORDERS_REMINDER, ORG_WEBHOOKS, WEBHOOK_URL_DEFAULT
from jobs import group_orders_by_org, format_pending_orders_message

# 设置日志
setup_logging()

def filter_orders_by_time_threshold(orders_data):
    """
    过滤工单数据，排除：
    - 待预约状态且未超过24小时的工单
    - 暂不上门状态且未超过48小时的工单

    Args:
        orders_data: 原始工单数据列表

    Returns:
        filtered_orders: 过滤后的工单数据列表
    """
    from datetime import datetime, timezone

    filtered_orders = []
    current_time = datetime.now(timezone.utc)

    for order in orders_data:
        try:
            # 解析工单数据
            order_info = {
                'orderNum': order[0],
                'name': order[1],
                'address': order[2],
                'supervisorName': order[3],
                'createTime': order[4],
                'orgName': order[5],
                'orderstatus': order[6]
            }

            # 解析创建时间
            create_time_str = order_info['createTime']
            if '+' in create_time_str:
                create_time = datetime.fromisoformat(create_time_str)
            else:
                create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))

            # 确保创建时间有时区信息
            if create_time.tzinfo is None:
                create_time = create_time.replace(tzinfo=timezone.utc)

            # 计算时间差（小时）
            time_diff = current_time - create_time
            hours_elapsed = time_diff.total_seconds() / 3600

            # 获取工单状态
            order_status = order_info['orderstatus']

            # 过滤逻辑
            should_include = True

            if '待预约' in order_status and hours_elapsed < 24:
                should_include = False
                print(f"过滤掉待预约工单 {order_info['orderNum']} (创建时间: {hours_elapsed:.1f}小时前)")
            elif '暂不上门' in order_status and hours_elapsed < 48:
                should_include = False
                print(f"过滤掉暂不上门工单 {order_info['orderNum']} (创建时间: {hours_elapsed:.1f}小时前)")

            if should_include:
                filtered_orders.append(order)

        except Exception as e:
            print(f"处理工单数据时出错，跳过: {order}, 错误: {e}")
            continue

    return filtered_orders

def test_single_org_reminder(target_org_name=None, max_orders=3):
    """
    测试单个服务商的工单提醒
    
    Args:
        target_org_name: 目标服务商名称，如果为None则选择第一个有工单的服务商
        max_orders: 最大工单数量，用于限制测试消息长度
    """
    print(f"开始测试单个服务商工单提醒...")
    print(f"目标服务商: {target_org_name or '自动选择'}")
    print(f"最大工单数: {max_orders}")
    print("-" * 50)
    
    try:
        # 1. 获取数据
        print("正在获取待预约工单数据...")
        response = send_request_with_managed_session(API_URL_PENDING_ORDERS_REMINDER)
        
        if not response or 'data' not in response:
            print("✗ API请求失败")
            return False
        
        orders_data = response['data']['rows']
        print(f"✓ 获取到 {len(orders_data)} 条原始工单数据")

        if not orders_data:
            print("当前没有待预约工单")
            return False

        # 2. 应用时间过滤
        print("正在应用时间过滤规则...")
        print("- 排除待预约未超过24小时的工单")
        print("- 排除暂不上门未超过48小时的工单")
        filtered_orders_data = filter_orders_by_time_threshold(orders_data)
        print(f"✓ 过滤后剩余 {len(filtered_orders_data)} 条工单数据")

        if not filtered_orders_data:
            print("过滤后没有符合条件的工单")
            return False

        # 3. 分组数据
        grouped_orders = group_orders_by_org(filtered_orders_data)
        print(f"✓ 分组成功，共 {len(grouped_orders)} 个服务商")

        # 4. 选择目标服务商
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

        # 5. 限制工单数量（用于测试）
        if len(selected_orders) > max_orders:
            selected_orders = selected_orders[:max_orders]
            print(f"✓ 限制为前 {max_orders} 个工单进行测试")

        # 6. 格式化消息
        message = format_pending_orders_message(selected_org, selected_orders)
        print("\n生成的消息内容:")
        print("=" * 60)
        print(message)
        print("=" * 60)

        # 7. 获取webhook地址
        webhook_url = ORG_WEBHOOKS.get(selected_org, WEBHOOK_URL_DEFAULT)
        is_default_webhook = webhook_url == WEBHOOK_URL_DEFAULT
        print(f"\nWebhook配置:")
        print(f"  服务商: {selected_org}")
        print(f"  Webhook: {'默认群' if is_default_webhook else '专属群'}")
        print(f"  地址: {webhook_url[:50]}...")

        # 8. 选择发送格式和确认发送
        print(f"\n准备发送测试消息到企微群...")
        print("选择消息格式:")
        print("1. 表格格式 (markdown)")
        print("2. 文本格式 (text)")
        format_choice = input("请选择格式 (1/2): ").strip()

        confirm = input("确认发送？(y/N): ").strip().lower()

        if confirm != 'y':
            print("已取消发送")
            return False

        # 9. 发送消息
        print("正在发送消息...")
        if format_choice == "1":
            post_markdown_v2_to_webhook(message, webhook_url)
            print("✓ 表格格式消息发送完成")
        else:
            # 使用文本格式
            from jobs import format_pending_orders_message_text
            text_message = format_pending_orders_message_text(selected_org, selected_orders)
            post_text_to_webhook(text_message, webhook_url)
            print("✓ 文本格式消息发送完成")
        
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
        # 应用时间过滤
        filtered_orders_data = filter_orders_by_time_threshold(orders_data)
        grouped_orders = group_orders_by_org(filtered_orders_data)
        
        print(f"\n当前有待预约工单的服务商 (共{len(grouped_orders)}个):")
        print("-" * 60)
        
        for i, (org_name, orders) in enumerate(grouped_orders.items(), 1):
            webhook_status = "专属群" if org_name in ORG_WEBHOOKS else "默认群"
            print(f"{i:2d}. {org_name}")
            print(f"     工单数量: {len(orders)}, Webhook: {webhook_status}")
        
    except Exception as e:
        print(f"✗ 获取服务商列表失败: {e}")

def main():
    print("待预约工单提醒 - 单服务商测试工具")
    print("=" * 60)
    
    while True:
        print("\n选择操作:")
        print("1. 列出所有有工单的服务商")
        print("2. 测试指定服务商")
        print("3. 测试第一个服务商（自动选择）")
        print("4. 🚀 执行完整提醒（所有服务商）")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()

        if choice == "1":
            list_available_orgs()

        elif choice == "2":
            org_name = input("请输入服务商名称: ").strip()
            if org_name:
                max_orders = input("最大工单数量 (默认3): ").strip()
                max_orders = int(max_orders) if max_orders.isdigit() else 3
                test_single_org_reminder(org_name, max_orders)
            else:
                print("服务商名称不能为空")

        elif choice == "3":
            max_orders = input("最大工单数量 (默认3): ").strip()
            max_orders = int(max_orders) if max_orders.isdigit() else 3
            test_single_org_reminder(None, max_orders)

        elif choice == "4":
            print("\n🚀 执行完整提醒（所有服务商）")
            print("⚠️  这将向所有有工单的服务商发送真实消息！")
            confirm = input("确认执行？(y/N): ").strip().lower()
            if confirm == 'y':
                print("正在执行完整提醒...")
                send_pending_orders_reminder_with_filter()
                print("✅ 完整提醒执行完成！")
            else:
                print("已取消")

        elif choice == "5":
            print("退出")
            break
            
        else:
            print("无效选择，请重新输入")

def send_pending_orders_reminder_with_filter():
    """带时间过滤的待预约工单提醒任务"""
    from modules.notification_module import post_text_to_webhook

    logging.info('带过滤的待预约工单提醒任务开始...')

    try:
        # 1. 获取数据
        print("正在获取待预约工单数据...")
        response = send_request_with_managed_session(API_URL_PENDING_ORDERS_REMINDER)

        if not response or 'data' not in response:
            print("✗ API请求失败")
            logging.error('API请求失败或数据格式异常')
            return

        orders_data = response['data']['rows']
        total_orders = len(orders_data)
        print(f"✓ 获取到 {total_orders} 条原始工单数据")
        logging.info(f'获取到 {total_orders} 条工单数据')

        if total_orders == 0:
            print("当前没有待预约工单")
            logging.info('没有待预约工单，任务结束')
            return

        # 2. 应用时间过滤
        print("正在应用时间过滤规则...")
        filtered_orders_data = filter_orders_by_time_threshold(orders_data)
        filtered_count = len(filtered_orders_data)
        print(f"✓ 过滤后剩余 {filtered_count} 条工单数据")
        logging.info(f'过滤后剩余 {filtered_count} 条工单数据')

        if filtered_count == 0:
            print("过滤后没有符合条件的工单")
            logging.info('过滤后没有符合条件的工单，任务结束')
            return

        # 3. 数据处理和分组
        print("正在按服务商分组工单数据...")
        grouped_orders = group_orders_by_org(filtered_orders_data)
        org_count = len(grouped_orders)
        print(f"✓ 共分为 {org_count} 个服务商组")
        logging.info(f'共分为 {org_count} 个服务商组')

        # 4. 发送通知
        success_count = 0
        failed_count = 0

        for org_name, orders in grouped_orders.items():
            try:
                print(f"正在为 {org_name} 发送提醒，工单数量: {len(orders)}")
                logging.info(f'正在为 {org_name} 发送提醒，工单数量: {len(orders)}')

                # 格式化消息（使用文字版格式）
                from jobs import format_pending_orders_message_text
                message = format_pending_orders_message_text(org_name, orders)

                # 获取webhook地址
                webhook_url = ORG_WEBHOOKS.get(org_name, WEBHOOK_URL_DEFAULT)

                # 发送消息（使用文字格式）
                post_text_to_webhook(message, webhook_url)

                success_count += 1
                print(f"✓ {org_name} 提醒发送成功")
                logging.info(f'✓ {org_name} 提醒发送成功')

            except Exception as e:
                failed_count += 1
                print(f"✗ {org_name} 提醒发送失败: {e}")
                logging.error(f'✗ {org_name} 提醒发送失败: {e}')

        # 5. 任务总结
        print(f"任务完成 - 成功: {success_count}, 失败: {failed_count}")
        logging.info(f'带过滤的待预约工单提醒任务完成 - 成功: {success_count}, 失败: {failed_count}')

    except Exception as e:
        print(f"✗ 任务执行失败: {e}")
        logging.error(f'带过滤的待预约工单提醒任务失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
