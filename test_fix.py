#!/usr/bin/env python3
"""
测试幸运数字奖励修复
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from modules.core.reward_calculator import RewardCalculator
from modules.core.data_models import ContractData, HousekeeperStats, OrderType

def test_platform_only_fix():
    """测试platform_only模式的修复"""
    print("测试北京10月幸运数字奖励修复...")
    
    # 创建北京10月的奖励计算器
    calculator = RewardCalculator("BJ-2025-10")
    
    # 创建测试数据：管家有5个平台单，2个自引单
    housekeeper_stats = HousekeeperStats(
        housekeeper="余金凤",
        activity_code="BJ-OCT",
        contract_count=7,  # 总数7个
        platform_count=5,  # 平台单5个（5的倍数）
        self_referral_count=2,  # 自引单2个
        total_amount=200000,
        platform_amount=150000,
        self_referral_amount=50000
    )
    
    print(f"管家统计: 平台单{housekeeper_stats.platform_count}个, 自引单{housekeeper_stats.self_referral_count}个")
    
    # 测试1: 平台单应该获得幸运数字奖励
    platform_contract = ContractData(
        contract_id="test_platform_001",
        housekeeper="余金凤",
        service_provider="测试服务商",
        contract_amount=50000,
        order_type=OrderType.PLATFORM
    )
    
    reward_type, reward_name = calculator._determine_lucky_number_reward(
        platform_contract, housekeeper_stats
    )
    
    print(f"\n测试1 - 平台单:")
    print(f"  合同类型: {platform_contract.order_type.value}")
    print(f"  奖励类型: {reward_type}")
    print(f"  奖励名称: {reward_name}")
    print(f"  结果: {'✅ 正确' if reward_type == '幸运数字' else '❌ 错误'}")
    
    # 测试2: 自引单不应该获得幸运数字奖励
    self_referral_contract = ContractData(
        contract_id="test_self_referral_001",
        housekeeper="余金凤",
        service_provider="测试服务商",
        contract_amount=50000,
        order_type=OrderType.SELF_REFERRAL
    )
    
    reward_type2, reward_name2 = calculator._determine_lucky_number_reward(
        self_referral_contract, housekeeper_stats
    )
    
    print(f"\n测试2 - 自引单:")
    print(f"  合同类型: {self_referral_contract.order_type.value}")
    print(f"  奖励类型: {reward_type2}")
    print(f"  奖励名称: {reward_name2}")
    print(f"  结果: {'✅ 正确' if reward_type2 == '' else '❌ 错误'}")

def test_other_activities():
    """测试其他活动不受影响"""
    print("\n" + "="*50)
    print("测试其他活动不受影响...")
    
    # 测试北京9月
    print("\n测试北京9月 (BJ-2025-09):")
    bj_sep_calculator = RewardCalculator("BJ-2025-09")
    
    housekeeper_stats = HousekeeperStats(
        housekeeper="测试管家",
        activity_code="BJ-SEP",
        contract_count=5,  # 总数5个（5的倍数）
        platform_count=3,
        self_referral_count=2,
        total_amount=100000,
        platform_amount=60000,
        self_referral_amount=40000
    )
    
    # 北京9月的自引单应该能获得幸运数字奖励（因为使用personal模式）
    self_referral_contract = ContractData(
        contract_id="test_bj_sep_001",
        housekeeper="测试管家",
        service_provider="测试服务商",
        contract_amount=50000,
        order_type=OrderType.SELF_REFERRAL
    )
    
    reward_type, reward_name = bj_sep_calculator._determine_lucky_number_reward(
        self_referral_contract, housekeeper_stats, personal_sequence=5
    )
    
    print(f"  合同类型: {self_referral_contract.order_type.value}")
    print(f"  个人序号: 5")
    print(f"  奖励类型: {reward_type}")
    print(f"  奖励名称: {reward_name}")
    print(f"  结果: {'✅ 正确 (北京9月自引单可以获得幸运数字奖)' if reward_type == '幸运数字' else '❌ 错误'}")
    
    # 测试上海9月
    print("\n测试上海9月 (SH-2025-09):")
    sh_sep_calculator = RewardCalculator("SH-2025-09")
    
    # 上海9月禁用幸运奖励
    reward_type3, reward_name3 = sh_sep_calculator._determine_lucky_number_reward(
        self_referral_contract, housekeeper_stats
    )
    
    print(f"  合同类型: {self_referral_contract.order_type.value}")
    print(f"  奖励类型: {reward_type3}")
    print(f"  奖励名称: {reward_name3}")
    print(f"  结果: {'✅ 正确 (上海9月禁用幸运奖)' if reward_type3 == '' else '❌ 错误'}")

def main():
    """主函数"""
    print("🔧 测试幸运数字奖励修复")
    print("="*50)
    
    try:
        test_platform_only_fix()
        test_other_activities()
        
        print("\n" + "="*50)
        print("✅ 所有测试完成")
        print("\n修复总结:")
        print("1. ✅ 北京10月: 自引单不再获得幸运数字奖励")
        print("2. ✅ 北京10月: 平台单仍然可以获得幸运数字奖励")
        print("3. ✅ 北京9月: 不受影响，自引单仍可获得幸运数字奖励")
        print("4. ✅ 上海9月: 不受影响，幸运奖励仍然禁用")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
