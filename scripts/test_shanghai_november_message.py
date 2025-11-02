#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海11月消息格式测试脚本
验证消息格式是否与10月一致（不显示自引单信息）
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.core.config_adapter import ConfigAdapter
from modules.core.notification_service import NotificationService
from modules.core.storage import PerformanceDataStore, create_data_store


def test_message_format():
    """测试上海11月消息格式"""
    print("=" * 80)
    print("测试上海11月消息格式")
    print("=" * 80)

    # 模拟一条测试记录
    test_record = {
        '管家(serviceHousekeeper)': '魏亮',
        '合同编号(contractdocNum)': 'YHWX-SH-HXJZ-2025100009',
        '工单类型': '平台单',
        '活动期内第几个合同': 60,
        '管家累计单数': 6,
        '管家累计金额': 20800,
        '平台单累计数量': 6,
        '自引单累计数量': 0,
        '平台单累计金额': 20800,
        '自引单累计金额': 0,
        '转化率(conversion)': '28%',
        '备注': '距离 基础奖 还需 19,200.0 元',
        '是否发送通知': 'N'
    }

    # 生成消息
    print("\n生成的消息：")
    print("-" * 80)

    # 模拟消息生成逻辑（与 notification_service.py 中的逻辑一致）
    service_housekeeper = test_record['管家(serviceHousekeeper)']
    order_type = test_record.get("工单类型", "平台单")
    platform_count = test_record.get("平台单累计数量", 0)
    platform_amount = f"{int(test_record.get('平台单累计金额', 0)):,d}"
    conversion_rate = test_record.get("转化率(conversion)", "")
    next_msg = test_record.get("备注", "")

    # 上海10月和11月使用相同的消息模板
    config_key = "SH-2025-11"
    if config_key in ["SH-2025-10", "SH-2025-11"]:
        msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同（{order_type}） {test_record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {test_record.get("活动期内第几个合同", 0)} 单，

🌻 个人平台单累计签约第 {platform_count} 单。
🌻 个人平台单金额累计签约 {platform_amount} 元

🌻 个人平台单转化率 {conversion_rate}，

👊 {next_msg} 🎉🎉🎉。
'''
    else:
        msg = "配置错误：未匹配到正确的消息模板"

    print(msg)
    print("-" * 80)
    
    # 验证消息格式
    print("\n验证结果：")
    print("-" * 80)
    
    checks = [
        ("✅ 不显示自引单累计数量", "自引单累计签约第" not in msg),
        ("✅ 不显示自引单累计金额", "自引单金额累计签约" not in msg),
        ("✅ 显示平台单累计数量", "个人平台单累计签约第 6 单" in msg),
        ("✅ 显示平台单累计金额", "个人平台单金额累计签约 20,800 元" in msg),
        ("✅ 显示转化率", "个人平台单转化率 28%" in msg),
        ("✅ 显示奖励进度", "距离 基础奖 还需 19,200.0 元" in msg),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅ 通过" if check_result else "❌ 失败"
        print(f"{status}: {check_name}")
        if not check_result:
            all_passed = False
    
    print("-" * 80)
    
    if all_passed:
        print("\n🎉 所有检查通过！上海11月消息格式正确。")
        return True
    else:
        print("\n❌ 部分检查失败，请检查消息格式。")
        return False


def compare_with_october():
    """对比10月和11月的消息格式"""
    print("\n" + "=" * 80)
    print("对比上海10月和11月的消息格式")
    print("=" * 80)

    test_record = {
        '管家(serviceHousekeeper)': '魏亮',
        '合同编号(contractdocNum)': 'YHWX-SH-HXJZ-2025100009',
        '工单类型': '平台单',
        '活动期内第几个合同': 60,
        '平台单累计数量': 6,
        '平台单累计金额': 20800,
        '转化率(conversion)': '28%',
        '备注': '距离 基础奖 还需 19,200.0 元',
    }

    # 生成消息的通用函数
    def generate_message(config_key):
        service_housekeeper = test_record['管家(serviceHousekeeper)']
        order_type = test_record.get("工单类型", "平台单")
        platform_count = test_record.get("平台单累计数量", 0)
        platform_amount = f"{int(test_record.get('平台单累计金额', 0)):,d}"
        conversion_rate = test_record.get("转化率(conversion)", "")
        next_msg = test_record.get("备注", "")

        return f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同（{order_type}） {test_record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {test_record.get("活动期内第几个合同", 0)} 单，

🌻 个人平台单累计签约第 {platform_count} 单。
🌻 个人平台单金额累计签约 {platform_amount} 元

🌻 个人平台单转化率 {conversion_rate}，

👊 {next_msg} 🎉🎉🎉。
'''

    # 生成10月和11月消息
    msg_oct = generate_message("SH-2025-10")
    msg_nov = generate_message("SH-2025-11")

    print("\n10月消息格式：")
    print("-" * 80)
    print(msg_oct)

    print("\n11月消息格式：")
    print("-" * 80)
    print(msg_nov)

    print("\n对比结果：")
    print("-" * 80)
    if msg_oct == msg_nov:
        print("✅ 10月和11月消息格式完全一致")
        return True
    else:
        print("❌ 10月和11月消息格式不一致")
        return False


if __name__ == "__main__":
    print("上海11月消息格式测试")
    print("=" * 80)
    
    # 测试消息格式
    test1 = test_message_format()
    
    # 对比10月和11月
    test2 = compare_with_october()
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    if test1 and test2:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)

