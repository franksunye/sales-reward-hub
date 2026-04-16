#!/usr/bin/env python3
"""
上海11月活动测试脚本
验证上海11月配置与10月一致，功能正确
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

from modules.config import REWARD_CONFIGS

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def test_shanghai_november_config():
    """测试上海11月配置"""
    print("=" * 60)
    print("测试上海11月配置")
    print("=" * 60)
    
    config_nov = REWARD_CONFIGS.get("SH-2025-11")
    config_oct = REWARD_CONFIGS.get("SH-2025-10")
    
    if not config_nov:
        print("❌ 上海11月配置不存在")
        return False
    
    if not config_oct:
        print("❌ 上海10月配置不存在")
        return False
    
    print("✅ 上海11月和10月配置都存在")
    
    # 检查关键配置项是否一致
    checks = [
        ("lucky_number", "lucky_number"),
        ("tiered_rewards.min_contracts", "tiered_rewards.min_contracts"),
        ("tiered_rewards.tiers", "tiered_rewards.tiers"),
        ("awards_mapping", "awards_mapping"),
        ("self_referral_rewards.enable", "self_referral_rewards.enable"),
        ("reward_calculation_strategy.type", "reward_calculation_strategy.type"),
    ]
    
    all_match = True
    for key_path, _ in checks:
        keys = key_path.split('.')
        
        # 获取11月配置值
        value_nov = config_nov
        for k in keys:
            value_nov = value_nov.get(k, None)
            if value_nov is None:
                break
        
        # 获取10月配置值
        value_oct = config_oct
        for k in keys:
            value_oct = value_oct.get(k, None)
            if value_oct is None:
                break
        
        if value_nov == value_oct:
            print(f"✅ {key_path}: 一致")
        else:
            print(f"❌ {key_path}: 不一致")
            print(f"   11月: {value_nov}")
            print(f"   10月: {value_oct}")
            all_match = False
    
    return all_match


def test_shanghai_november_constants():
    """测试上海11月常量"""
    print("\n" + "=" * 60)
    print("测试上海11月常量")
    print("=" * 60)
    
    try:
        from modules.config import (
            API_URL_SH_NOV,
            TEMP_CONTRACT_DATA_FILE_SH_NOV,
            PERFORMANCE_DATA_FILENAME_SH_NOV,
            STATUS_FILENAME_SH_NOV
        )
        
        print(f"✅ API_URL_SH_NOV: {API_URL_SH_NOV}")
        print(f"✅ TEMP_CONTRACT_DATA_FILE_SH_NOV: {TEMP_CONTRACT_DATA_FILE_SH_NOV}")
        print(f"✅ PERFORMANCE_DATA_FILENAME_SH_NOV: {PERFORMANCE_DATA_FILENAME_SH_NOV}")
        print(f"✅ STATUS_FILENAME_SH_NOV: {STATUS_FILENAME_SH_NOV}")
        
        # 检查常量格式
        if not API_URL_SH_NOV.endswith("/query"):
            print("❌ API_URL_SH_NOV 格式不正确")
            return False
        
        if "SH-Nov" not in TEMP_CONTRACT_DATA_FILE_SH_NOV:
            print("❌ TEMP_CONTRACT_DATA_FILE_SH_NOV 格式不正确")
            return False
        
        print("✅ 所有常量格式正确")
        return True
        
    except ImportError as e:
        print(f"❌ 常量导入失败: {e}")
        return False


def test_job_function_exists():
    """测试job函数是否存在"""
    print("\n" + "=" * 60)
    print("测试job函数")
    print("=" * 60)
    
    try:
        from modules.core.shanghai_jobs import (
            signing_and_sales_incentive_nov_shanghai_v2,
            signing_and_sales_incentive_nov_shanghai
        )
        
        print("✅ signing_and_sales_incentive_nov_shanghai_v2 函数存在")
        print("✅ signing_and_sales_incentive_nov_shanghai 函数存在")
        
        # 检查函数是否可调用
        if callable(signing_and_sales_incentive_nov_shanghai_v2):
            print("✅ signing_and_sales_incentive_nov_shanghai_v2 可调用")
        else:
            print("❌ signing_and_sales_incentive_nov_shanghai_v2 不可调用")
            return False
        
        if callable(signing_and_sales_incentive_nov_shanghai):
            print("✅ signing_and_sales_incentive_nov_shanghai 可调用")
        else:
            print("❌ signing_and_sales_incentive_nov_shanghai 不可调用")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ job函数导入失败: {e}")
        return False


def test_main_import():
    """测试main.py是否正确导入"""
    print("\n" + "=" * 60)
    print("测试main.py导入")
    print("=" * 60)
    
    try:
        # 检查main.py中是否导入了上海11月函数
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'signing_and_sales_incentive_nov_shanghai' in content:
            print("✅ main.py 中导入了上海11月函数")
        else:
            print("❌ main.py 中未导入上海11月函数")
            return False
        
        if 'current_month == 11' in content:
            print("✅ main.py 中有11月的调度逻辑")
        else:
            print("❌ main.py 中缺少11月的调度逻辑")
            return False
        
        if 'signing_and_sales_incentive_nov_shanghai()' in content:
            print("✅ main.py 中调用了上海11月函数")
        else:
            print("❌ main.py 中未调用上海11月函数")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ main.py 检查失败: {e}")
        return False


def test_configuration_consistency():
    """测试配置一致性详细检查"""
    print("\n" + "=" * 60)
    print("测试配置一致性详细检查")
    print("=" * 60)
    
    config_nov = REWARD_CONFIGS.get("SH-2025-11")
    config_oct = REWARD_CONFIGS.get("SH-2025-10")
    
    # 检查奖励等级
    tiers_nov = config_nov.get("tiered_rewards", {}).get("tiers", [])
    tiers_oct = config_oct.get("tiered_rewards", {}).get("tiers", [])
    
    if len(tiers_nov) != len(tiers_oct):
        print(f"❌ 奖励等级数量不一致: 11月{len(tiers_nov)}个, 10月{len(tiers_oct)}个")
        return False
    
    print(f"✅ 奖励等级数量一致: {len(tiers_nov)}个")
    
    # 检查每个奖励等级
    for i, (tier_nov, tier_oct) in enumerate(zip(tiers_nov, tiers_oct)):
        if tier_nov != tier_oct:
            print(f"❌ 第{i+1}个奖励等级不一致")
            print(f"   11月: {tier_nov}")
            print(f"   10月: {tier_oct}")
            return False
    
    print("✅ 所有奖励等级完全一致")
    
    # 检查奖励映射
    awards_nov = config_nov.get("awards_mapping", {})
    awards_oct = config_oct.get("awards_mapping", {})
    
    if awards_nov != awards_oct:
        print(f"❌ 奖励映射不一致")
        print(f"   11月: {awards_nov}")
        print(f"   10月: {awards_oct}")
        return False
    
    print("✅ 奖励映射完全一致")
    
    return True


def main():
    """主测试函数"""
    print("🚀 开始测试上海11月活动功能")
    print("验证上海11月配置与10月一致...")
    
    tests = [
        ("配置一致性测试", test_shanghai_november_config),
        ("常量测试", test_shanghai_november_constants),
        ("Job函数测试", test_job_function_exists),
        ("Main导入测试", test_main_import),
        ("配置详细一致性测试", test_configuration_consistency),
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
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过！上海11月活动功能实现正确。")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
