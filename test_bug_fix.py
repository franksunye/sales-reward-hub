#!/usr/bin/env python3
"""
测试幸运数字边界条件BUG修复
"""

import sys
sys.path.insert(0, '.')

from modules.core.reward_calculator import RewardCalculator
from modules.core.data_models import HousekeeperStats, ContractData, OrderType
from modules.config import REWARD_CONFIGS

def test_platform_only_boundary_fix():
    """测试platform_only模式的边界条件修复"""
    
    print("🧪 测试幸运数字边界条件BUG修复")
    print("=" * 50)
    
    # 使用北京10月配置
    calculator = RewardCalculator("BJ-2025-10")
    
    # 测试用例1：只有自引单，平台单数量为0（BUG场景）
    print("\n📋 测试用例1：只有自引单，平台单数量为0")
    stats1 = HousekeeperStats(
        housekeeper="马俊杰",
        activity_code="BJ-OCT",
        platform_count=0,      # 平台单数量为0
        self_referral_count=1  # 自引单数量为1
    )
    
    contract1 = ContractData(
        contract_id="TEST001",
        housekeeper="马俊杰",
        service_provider="测试服务商",
        contract_amount=5000.0,
        order_type=OrderType.SELF_REFERRAL
    )
    
    result1 = calculator._determine_lucky_number_reward(contract1, stats1)
    print(f"  输入：platform_count=0, self_referral_count=1")
    print(f"  结果：{result1}")
    print(f"  预期：('', '') - 不应该获得幸运数字奖励")
    print(f"  状态：{'✅ 通过' if result1 == ('', '') else '❌ 失败'}")
    
    # 测试用例2：平台单数量为5（正常场景）
    print("\n📋 测试用例2：平台单数量为5")
    stats2 = HousekeeperStats(
        housekeeper="测试管家",
        activity_code="BJ-OCT",
        platform_count=5,      # 平台单数量为5
        self_referral_count=2  # 自引单数量为2
    )
    
    contract2 = ContractData(
        contract_id="TEST002",
        housekeeper="测试管家",
        service_provider="测试服务商",
        contract_amount=8000.0,
        order_type=OrderType.PLATFORM
    )
    
    result2 = calculator._determine_lucky_number_reward(contract2, stats2)
    print(f"  输入：platform_count=5, self_referral_count=2")
    print(f"  结果：{result2}")
    print(f"  预期：('幸运数字', '接好运') - 应该获得幸运数字奖励")
    print(f"  状态：{'✅ 通过' if result2 == ('幸运数字', '接好运') else '❌ 失败'}")
    
    # 测试用例3：平台单数量为3（不是5的倍数）
    print("\n📋 测试用例3：平台单数量为3")
    stats3 = HousekeeperStats(
        housekeeper="测试管家2",
        activity_code="BJ-OCT",
        platform_count=3,      # 平台单数量为3
        self_referral_count=1  # 自引单数量为1
    )
    
    contract3 = ContractData(
        contract_id="TEST003",
        housekeeper="测试管家2",
        service_provider="测试服务商",
        contract_amount=7000.0,
        order_type=OrderType.PLATFORM
    )
    
    result3 = calculator._determine_lucky_number_reward(contract3, stats3)
    print(f"  输入：platform_count=3, self_referral_count=1")
    print(f"  结果：{result3}")
    print(f"  预期：('', '') - 不应该获得幸运数字奖励")
    print(f"  状态：{'✅ 通过' if result3 == ('', '') else '❌ 失败'}")
    
    # 测试用例4：平台单数量为10（5的倍数）
    print("\n📋 测试用例4：平台单数量为10")
    stats4 = HousekeeperStats(
        housekeeper="测试管家3",
        activity_code="BJ-OCT",
        platform_count=10,     # 平台单数量为10
        self_referral_count=5  # 自引单数量为5
    )
    
    contract4 = ContractData(
        contract_id="TEST004",
        housekeeper="测试管家3",
        service_provider="测试服务商",
        contract_amount=12000.0,
        order_type=OrderType.PLATFORM
    )
    
    result4 = calculator._determine_lucky_number_reward(contract4, stats4)
    print(f"  输入：platform_count=10, self_referral_count=5")
    print(f"  结果：{result4}")
    print(f"  预期：('幸运数字', '接好运') - 应该获得幸运数字奖励")
    print(f"  状态：{'✅ 通过' if result4 == ('幸运数字', '接好运') else '❌ 失败'}")
    
    # 汇总结果
    test_results = [
        result1 == ('', ''),
        result2 == ('幸运数字', '接好运'),
        result3 == ('', ''),
        result4 == ('幸运数字', '接好运')
    ]
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n🎯 测试结果汇总：")
    print(f"  通过：{passed}/{total}")
    print(f"  状态：{'✅ 全部通过' if passed == total else '❌ 有失败'}")
    
    if passed == total:
        print(f"\n🎉 BUG修复成功！")
        print(f"  ✅ 平台单数量为0时不会错误触发幸运数字奖励")
        print(f"  ✅ 平台单数量为5的倍数时正常触发幸运数字奖励")
        print(f"  ✅ 平台单数量不是5的倍数时不触发幸运数字奖励")
    else:
        print(f"\n❌ BUG修复失败，需要进一步检查")
    
    return passed == total

if __name__ == "__main__":
    test_platform_only_boundary_fix()
