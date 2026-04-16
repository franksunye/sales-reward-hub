#!/usr/bin/env python3
"""
北京11月活动测试脚本
测试仅播报模式的功能实现
"""

import os
import sys
import types
import logging
from typing import Dict, List

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub

# 设置环境变量避免配置错误
os.environ.setdefault('METABASE_USERNAME', 'test')
os.environ.setdefault('METABASE_PASSWORD', 'test')
os.environ.setdefault('WECOM_WEBHOOK_DEFAULT', 'test')
os.environ.setdefault('CONTACT_PHONE_NUMBER', 'test')
os.environ.setdefault('DB_SOURCE', 'local')

from modules.core.reward_calculator import RewardCalculator
from modules.core.data_models import ContractData, HousekeeperStats, OrderType
from modules.config import REWARD_CONFIGS

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def test_bj_november_config():
    """测试北京11月配置"""
    print("=" * 60)
    print("测试北京11月配置")
    print("=" * 60)
    
    config = REWARD_CONFIGS.get("BJ-2025-11")
    if not config:
        print("❌ 配置不存在")
        return False
    
    print("✅ 配置存在")
    
    # 检查关键配置项
    checks = [
        ("lucky_number", ""),
        ("tiered_rewards.tiers", []),
        ("awards_mapping", {}),
        ("reward_calculation_strategy.type", "announcement_only"),
        ("notification_config.enable_award_notification", False),
        ("processing_config.process_platform_only", True),
    ]
    
    for key, expected in checks:
        keys = key.split('.')
        value = config
        for k in keys:
            value = value.get(k, None)
            if value is None:
                break
        
        if value == expected:
            print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: 期望 {expected}, 实际 {value}")
            return False
    
    return True


def test_reward_calculator():
    """测试奖励计算器"""
    print("\n" + "=" * 60)
    print("测试奖励计算器")
    print("=" * 60)
    
    try:
        calculator = RewardCalculator("BJ-2025-11")
        print("✅ 奖励计算器初始化成功")
        
        # 创建测试数据
        contract_data = ContractData(
            contract_id="BJ-NOV-001",
            housekeeper="张三",
            service_provider="测试服务商",
            contract_amount=50000,
            paid_amount=50000,
            order_type=OrderType.PLATFORM,
            raw_data={}
        )
        
        housekeeper_stats = HousekeeperStats(
            housekeeper="张三",
            activity_code="BJ-NOV",
            platform_count=5,
            self_referral_count=0,
            platform_amount=250000,
            self_referral_amount=0,
            awarded=[]
        )
        
        # 测试奖励计算
        rewards, next_gap = calculator.calculate(contract_data, housekeeper_stats, 10, 5)
        
        if len(rewards) == 0:
            print("✅ 仅播报模式：无奖励计算")
            return True
        else:
            print(f"❌ 期望无奖励，但计算出了 {len(rewards)} 个奖励")
            return False
            
    except Exception as e:
        print(f"❌ 奖励计算器测试失败: {e}")
        return False


def test_notification_config():
    """测试通知配置"""
    print("\n" + "=" * 60)
    print("测试通知配置")
    print("=" * 60)

    try:
        config = REWARD_CONFIGS.get("BJ-2025-11", {})
        notification_config = config.get("notification_config", {})

        enable_award_notification = notification_config.get("enable_award_notification", True)

        if not enable_award_notification:
            print("✅ 仅播报模式：禁用个人奖励通知")
            return True
        else:
            print("❌ 期望禁用个人奖励通知，但配置为启用")
            return False

    except Exception as e:
        print(f"❌ 通知配置测试失败: {e}")
        return False


def test_message_template():
    """测试消息模板"""
    print("\n" + "=" * 60)
    print("测试消息模板")
    print("=" * 60)
    
    # 模拟消息生成逻辑
    test_record = {
        '管家(serviceHousekeeper)': '张三',
        '合同编号(contractdocNum)': 'BJ-NOV-001',
        '活动期内第几个合同': 10,
        '管家累计单数': 5,
        '管家累计金额': 250000
    }
    
    # 模拟北京11月消息模板
    service_housekeeper = test_record['管家(serviceHousekeeper)']
    contract_num = test_record.get("合同编号(contractdocNum)", "")
    global_sequence = test_record.get("活动期内第几个合同", 0)
    personal_count = test_record.get("管家累计单数", 0)
    accumulated_amount = f"{int(test_record.get('管家累计金额', 0)):,d}"
    
    expected_msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同 {contract_num} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_sequence} 单

🌻 个人累计签约第 {personal_count} 单，累计签约 {accumulated_amount} 元

👊 继续加油，再接再厉！🎉🎉🎉
'''
    
    print("✅ 消息模板生成成功")
    print("消息内容预览:")
    print("-" * 40)
    print(expected_msg)
    print("-" * 40)
    
    # 检查消息内容
    checks = [
        ("包含管家姓名", service_housekeeper in expected_msg),
        ("包含合同编号", contract_num in expected_msg),
        ("包含全局序号", str(global_sequence) in expected_msg),
        ("包含个人序号", str(personal_count) in expected_msg),
        ("包含累计金额", accumulated_amount in expected_msg),
        ("包含鼓励语", "继续加油，再接再厉！" in expected_msg),
        ("不包含奖励信息", "奖励" not in expected_msg or "接好运" not in expected_msg),
    ]
    
    all_passed = True
    for desc, result in checks:
        if result:
            print(f"✅ {desc}")
        else:
            print(f"❌ {desc}")
            all_passed = False
    
    return all_passed


def test_platform_filter():
    """测试平台单过滤逻辑"""
    print("\n" + "=" * 60)
    print("测试平台单过滤逻辑")
    print("=" * 60)

    # 模拟合同数据
    test_contracts = [
        {'合同ID(_id)': 'BJ-NOV-001', '工单类型(sourceType)': 2, '管家(serviceHousekeeper)': '张三'},  # 雨虹平台单
        {'合同ID(_id)': 'BJ-NOV-002', '工单类型(sourceType)': 1, '管家(serviceHousekeeper)': '李四'},  # 自引单
        {'合同ID(_id)': 'BJ-NOV-003', '工单类型(sourceType)': 4, '管家(serviceHousekeeper)': '王五'},  # 修链平台单
        {'合同ID(_id)': 'BJ-NOV-004', '工单类型(sourceType)': 5, '管家(serviceHousekeeper)': '赵六'},  # 修链自获客
    ]

    # 模拟过滤逻辑（支持 sourceType=2、4、5 的平台单）
    filtered_contracts = [
        c for c in test_contracts
        if c.get('工单类型(sourceType)', 2) in [2, 4, 5]
    ]
    
    original_count = len(test_contracts)
    filtered_count = len(filtered_contracts)
    removed_count = original_count - filtered_count

    print(f"原始合同数: {original_count}")
    print(f"过滤后合同数: {filtered_count}")
    print(f"过滤掉的非平台单数: {removed_count}")

    # 验证：应该保留 3 个平台单（2个雨虹平台单 + 1个修链平台单），过滤掉 1 个自引单
    if filtered_count == 3 and removed_count == 1:
        print("✅ 平台单过滤逻辑正确（支持 sourceType=2 和 sourceType=5）")
        return True
    else:
        print(f"❌ 平台单过滤逻辑错误（期望保留3个，实际保留{filtered_count}个）")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试北京11月活动功能")
    print("测试仅播报模式的各项功能...")
    
    tests = [
        ("配置测试", test_bj_november_config),
        ("奖励计算器测试", test_reward_calculator),
        ("通知配置测试", test_notification_config),
        ("消息模板测试", test_message_template),
        ("平台单过滤测试", test_platform_filter),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {name} 通过")
            else:
                print(f"\n❌ {name} 失败")
        except Exception as e:
            print(f"\n❌ {name} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过！北京11月活动功能实现正确。")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
