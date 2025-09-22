#!/usr/bin/env python3
"""
简化的新架构测试工具

专注于验证新架构的基本功能是否正常工作。

使用方法:
    python scripts/simple_new_arch_test.py
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_config_loading():
    """测试配置加载"""
    print("📋 测试配置加载...")
    
    try:
        from modules.core.config_adapter import ConfigAdapter
        
        # 测试北京9月配置
        bj_config = ConfigAdapter.get_reward_config("BJ-2025-09")
        print(f"✅ 北京9月配置加载成功: {len(bj_config)} 个字段")
        print(f"   - 幸运数字: {bj_config.get('lucky_number')}")
        print(f"   - 奖励映射: {len(bj_config.get('awards_mapping', {}))} 个")
        
        # 测试上海9月配置
        sh_config = ConfigAdapter.get_reward_config("SH-2025-09")
        print(f"✅ 上海9月配置加载成功: {len(sh_config)} 个字段")
        print(f"   - 幸运数字: {sh_config.get('lucky_number')}")
        print(f"   - 奖励映射: {len(sh_config.get('awards_mapping', {}))} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_function_imports():
    """测试函数导入"""
    print("\n🔧 测试函数导入...")
    
    try:
        # 测试北京9月函数
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        print(f"✅ 北京9月函数导入成功: {signing_and_sales_incentive_sep_beijing_v2.__name__}")
        
        # 测试上海9月函数
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        print(f"✅ 上海9月函数导入成功: {signing_and_sales_incentive_sep_shanghai_v2.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 函数导入失败: {e}")
        return False

def test_data_models():
    """测试数据模型"""
    print("\n📊 测试数据模型...")

    try:
        from modules.core.data_models import PerformanceRecord, ContractData, HousekeeperStats, RewardInfo

        # 创建测试合同数据
        contract_data = ContractData(
            contract_id="test_001",
            housekeeper="测试管家",
            service_provider="测试服务商",
            contract_amount=100000.0,
            paid_amount=100000.0
        )

        # 创建测试管家统计
        housekeeper_stats = HousekeeperStats(
            housekeeper_key="测试管家",
            contract_count=1,
            total_amount=100000.0,
            performance_amount=100000.0
        )

        # 创建测试奖励信息
        reward_info = RewardInfo(
            reward_type="幸运数字",
            reward_name="接好运",
            amount=58.0
        )

        # 创建测试记录
        test_record = PerformanceRecord(
            activity_code="BJ-SEP",
            contract_data=contract_data,
            housekeeper_stats=housekeeper_stats,
            rewards=[reward_info],
            performance_amount=100000.0
        )

        print(f"✅ 数据模型创建成功: {test_record.contract_data.contract_id}")
        print(f"   - 合同金额: {test_record.contract_data.contract_amount}")
        print(f"   - 管家: {test_record.contract_data.housekeeper}")
        print(f"   - 奖励: {test_record.rewards[0].reward_name}")

        return True

    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_reward_calculator():
    """测试奖励计算器"""
    print("\n🎯 测试奖励计算器...")

    try:
        from modules.core.reward_calculator import RewardCalculator

        # 直接传递配置键而不是配置对象
        calculator = RewardCalculator("BJ-2025-09")

        # 创建测试数据
        contract_data = ContractData(
            contract_id="test_001",
            housekeeper="测试管家",
            service_provider="测试服务商",
            contract_amount=100000.0,
            paid_amount=100000.0
        )

        housekeeper_stats = HousekeeperStats(
            housekeeper_key="测试管家",
            contract_count=5,
            total_amount=500000.0,
            performance_amount=500000.0
        )

        # 测试奖励计算
        rewards = calculator.calculate(
            contract_data=contract_data,
            housekeeper_stats=housekeeper_stats,
            global_sequence=10,
            personal_sequence=5
        )
        print(f"✅ 奖励计算成功: {len(rewards)} 个奖励")
        for reward in rewards:
            print(f"   - {reward.reward_type}: {reward.reward_name} ({reward.amount}元)")

        return True

    except Exception as e:
        print(f"❌ 奖励计算器测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_basic_execution():
    """测试基本执行"""
    print("\n🚀 测试基本执行...")
    
    try:
        # 测试北京9月函数是否可以调用（不实际执行）
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        
        print("✅ 北京9月函数可调用")
        print(f"   - 函数名: {signing_and_sales_incentive_sep_beijing_v2.__name__}")
        print(f"   - 模块: {signing_and_sales_incentive_sep_beijing_v2.__module__}")
        print(f"   - 文档: {signing_and_sales_incentive_sep_beijing_v2.__doc__[:100] if signing_and_sales_incentive_sep_beijing_v2.__doc__ else 'None'}...")
        
        # 测试上海9月函数
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        
        print("✅ 上海9月函数可调用")
        print(f"   - 函数名: {signing_and_sales_incentive_sep_shanghai_v2.__name__}")
        print(f"   - 模块: {signing_and_sales_incentive_sep_shanghai_v2.__module__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本执行测试失败: {e}")
        return False

def test_configuration_consistency():
    """测试配置一致性"""
    print("\n⚖️ 测试配置一致性...")
    
    try:
        from modules.core.config_adapter import ConfigAdapter
        
        # 获取新配置
        bj_new_config = ConfigAdapter.get_reward_config("BJ-2025-09")
        sh_new_config = ConfigAdapter.get_reward_config("SH-2025-09")
        
        # 检查必要字段
        required_fields = ['lucky_number', 'awards_mapping', 'tiered_rewards']
        
        print("北京9月配置检查:")
        for field in required_fields:
            if field in bj_new_config:
                print(f"   ✅ {field}: 存在")
            else:
                print(f"   ❌ {field}: 缺失")
        
        print("上海9月配置检查:")
        for field in required_fields:
            if field in sh_new_config:
                print(f"   ✅ {field}: 存在")
            else:
                print(f"   ❌ {field}: 缺失")
        
        # 检查奖励金额
        bj_awards = bj_new_config.get('awards_mapping', {})
        sh_awards = sh_new_config.get('awards_mapping', {})
        
        print(f"\n北京9月奖励配置: {bj_awards}")
        print(f"上海9月奖励配置: {sh_awards}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置一致性测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 新架构简化测试")
    print("=" * 60)
    
    tests = [
        ("配置加载", test_config_loading),
        ("函数导入", test_function_imports),
        ("数据模型", test_data_models),
        ("奖励计算器", test_reward_calculator),
        ("基本执行", test_basic_execution),
        ("配置一致性", test_configuration_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新架构基本功能正常")
        return 0
    else:
        print("⚠️ 部分测试失败，需要检查新架构")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
