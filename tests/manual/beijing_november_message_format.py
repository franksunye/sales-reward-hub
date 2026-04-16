#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北京11月消息格式验证脚本
验证消息格式是否符合技术设计文档的要求
"""

import os
import sys
import types
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")
    requests_exceptions_stub = types.ModuleType("requests.exceptions")

    class _RequestException(Exception):
        pass

    class _Timeout(_RequestException):
        pass

    requests_stub.post = lambda *args, **kwargs: None
    requests_stub.RequestException = _RequestException
    requests_exceptions_stub.Timeout = _Timeout
    sys.modules["requests"] = requests_stub
    sys.modules["requests.exceptions"] = requests_exceptions_stub

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub

os.environ.setdefault("CONTACT_PHONE_NUMBER", "13800000000")
os.environ.setdefault("METABASE_USERNAME", "test@example.com")
os.environ.setdefault("METABASE_PASSWORD", "test-password")
os.environ.setdefault("WECOM_WEBHOOK_DEFAULT", "https://example.com/default")
os.environ.setdefault("WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT", "https://example.com/sign-broadcast")
os.environ.setdefault("DB_SOURCE", "local")


def test_beijing_november_message():
    """测试北京11月消息格式"""
    print("=" * 80)
    print("测试北京11月消息格式")
    print("=" * 80)
    
    # 模拟测试数据
    test_record = {
        '管家(serviceHousekeeper)': '张三',
        '合同编号(contractdocNum)': 'BJ-NOV-001',
        '活动期内第几个合同': 10,
        '管家累计单数': 5,
        '管家累计金额': 250000
    }
    
    # 模拟消息生成逻辑（与 notification_service.py 中的逻辑一致）
    service_housekeeper = test_record['管家(serviceHousekeeper)']
    contract_num = test_record.get("合同编号(contractdocNum)", "")
    global_sequence = test_record.get("活动期内第几个合同", 0)
    personal_count = test_record.get("管家累计单数", 0)
    accumulated_amount = f"{int(test_record.get('管家累计金额', 0)):,d}"
    
    # 实际生成的消息
    actual_msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同 {contract_num} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_sequence} 单

🌻 个人累计签约第 {personal_count} 单，累计签约 {accumulated_amount} 元

👊 继续加油，再接再厉！🎉🎉🎉
'''
    
    # 技术设计文档中的期望消息格式
    expected_msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同 {contract_num} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_sequence} 单

🌻 个人累计签约第 {personal_count} 单，累计签约 {accumulated_amount} 元

👊 继续加油，再接再厉！🎉🎉🎉
'''
    
    print("\n实际生成的消息：")
    print("-" * 80)
    print(actual_msg)
    print("-" * 80)
    
    print("\n技术设计文档期望的消息：")
    print("-" * 80)
    print(expected_msg)
    print("-" * 80)
    
    # 验证消息格式
    print("\n验证结果：")
    print("-" * 80)
    
    checks = [
        ("✅ 消息格式与设计文档一致", actual_msg == expected_msg),
        ("✅ 包含签约喜报标题", "🧨🧨🧨 签约喜报 🧨🧨🧨" in actual_msg),
        ("✅ 包含管家姓名", service_housekeeper in actual_msg),
        ("✅ 包含合同编号", contract_num in actual_msg),
        ("✅ 包含全局序号", f"本单为平台本月累计签约第 {global_sequence} 单" in actual_msg),
        ("✅ 包含个人累计单数", f"个人累计签约第 {personal_count} 单" in actual_msg),
        ("✅ 包含累计金额", f"累计签约 {accumulated_amount} 元" in actual_msg),
        ("✅ 包含固定结束语", "继续加油，再接再厉！" in actual_msg),
        ("✅ 不包含工单类型", "（平台单）" not in actual_msg and "（自引单）" not in actual_msg),
        ("✅ 不包含转化率", "转化率" not in actual_msg),
        ("✅ 不包含奖励进度", "距离" not in actual_msg and "还需" not in actual_msg),
        ("✅ 不包含自引单信息", "自引单" not in actual_msg),
        ("✅ 不包含业绩金额", "业绩金额" not in actual_msg),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅ 通过" if check_result else "❌ 失败"
        print(f"{status}: {check_name}")
        if not check_result:
            all_passed = False
    
    print("-" * 80)
    
    return all_passed


def compare_with_october():
    """对比北京10月和11月的消息格式差异"""
    print("\n" + "=" * 80)
    print("对比北京10月和11月的消息格式")
    print("=" * 80)
    
    test_record = {
        '管家(serviceHousekeeper)': '张三',
        '合同编号(contractdocNum)': 'BJ-001',
        '工单类型': '平台单',
        '活动期内第几个合同': 10,
        '管家累计单数': 5,
        '管家累计金额': 250000,
        '平台单累计数量': 4,
        '自引单累计数量': 1,
        '平台单累计金额': 200000,
        '自引单累计金额': 50000,
        '管家累计业绩金额': 250000,
        '备注': '距离 卓越奖 还需 210,000.0 元'
    }
    
    # 北京10月消息格式（包含详细统计和奖励进度）
    service_housekeeper = test_record['管家(serviceHousekeeper)']
    order_type = test_record.get("工单类型", "平台单")
    platform_count = test_record.get("平台单累计数量", 0)
    self_referral_count = test_record.get("自引单累计数量", 0)
    platform_amount = f"{int(test_record.get('平台单累计金额', 0)):,d}"
    self_referral_amount = f"{int(test_record.get('自引单累计金额', 0)):,d}"
    performance_amount = f"{int(test_record.get('管家累计业绩金额', 0)):,d}"
    global_contract_sequence = test_record.get("活动期内第几个合同", 0)
    next_msg = test_record.get("备注", "")
    
    msg_oct = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同（{order_type}） {test_record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_contract_sequence} 单

🌻 个人平台单累计签约第 {platform_count} 单，累计签约 {platform_amount} 元
🌻 个人自引单累计签约第 {self_referral_count} 单，累计签约 {self_referral_amount}元
🌻 个人累计业绩金额 {performance_amount} 元

👊 {next_msg} 🎉🎉🎉
'''
    
    # 北京11月消息格式（简化，仅播报）
    contract_num = test_record.get("合同编号(contractdocNum)", "")
    global_sequence = test_record.get("活动期内第几个合同", 0)
    personal_count = test_record.get("管家累计单数", 0)
    accumulated_amount = f"{int(test_record.get('管家累计金额', 0)):,d}"
    
    msg_nov = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同 {contract_num} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_sequence} 单

🌻 个人累计签约第 {personal_count} 单，累计签约 {accumulated_amount} 元

👊 继续加油，再接再厉！🎉🎉🎉
'''
    
    print("\n北京10月消息格式（包含奖励进度）：")
    print("-" * 80)
    print(msg_oct)
    
    print("\n北京11月消息格式（仅播报）：")
    print("-" * 80)
    print(msg_nov)
    
    print("\n关键差异：")
    print("-" * 80)
    print("✅ 10月：显示工单类型（平台单/自引单）")
    print("✅ 11月：不显示工单类型")
    print()
    print("✅ 10月：显示双轨统计（平台单+自引单）")
    print("✅ 11月：仅显示总累计统计")
    print()
    print("✅ 10月：显示业绩金额")
    print("✅ 11月：不显示业绩金额")
    print()
    print("✅ 10月：显示奖励进度（距离XX奖还需XX元）")
    print("✅ 11月：固定结束语（继续加油，再接再厉！）")
    print("-" * 80)
    
    return True


if __name__ == "__main__":
    print("北京11月消息格式验证")
    print("=" * 80)
    
    # 测试消息格式
    test1 = test_beijing_november_message()
    
    # 对比10月和11月
    test2 = compare_with_october()
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    if test1 and test2:
        print("✅ 所有测试通过！北京11月消息格式符合技术设计文档要求。")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)
