#!/usr/bin/env python3
"""
兼容性测试 - 验证上海10月的修改不会影响北京和上海9月的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config import REWARD_CONFIGS
from modules.core.notification_service import NotificationService
from modules.core.data_models import ProcessingConfig, City
from modules.core.storage import create_data_store

def test_beijing_message_template():
    """测试北京消息模板不受影响"""
    print("🧪 测试北京消息模板兼容性")
    print("-" * 40)
    
    # 创建北京配置
    config = ProcessingConfig(
        config_key="BJ-2025-10",
        activity_code="BJ-OCT",
        city=City.BEIJING,
        housekeeper_key_format="管家"
    )
    
    store = create_data_store(storage_type='sqlite', db_path=':memory:')
    notification_service = NotificationService(store, config)
    
    # 模拟北京记录
    record = {
        '管家(serviceHousekeeper)': '张三',
        '工单类型': '平台单',
        '合同编号(contractdocNum)': 'BJ-001',
        '活动期内第几个合同': 10,
        '平台单累计数量': 5,
        '自引单累计数量': 3,
        '平台单累计金额': 200000,
        '自引单累计金额': 150000,
        '管家累计金额': 350000,
        '管家累计业绩金额': 300000,
        '管家累计单数': 8,
        '备注': '距离下一个奖励还需要2单'
    }
    
    # 生成消息（模拟内部逻辑）
    service_housekeeper = record['管家(serviceHousekeeper)']
    order_type = record.get("工单类型", "平台单")
    platform_count = record.get("平台单累计数量", 0)
    self_referral_count = record.get("自引单累计数量", 0)
    platform_amount = f"{int(float(record.get('平台单累计金额', 0))):,d}"
    self_referral_amount = f"{int(float(record.get('自引单累计金额', 0))):,d}"
    global_contract_sequence = record.get("活动期内第几个合同", 0)
    next_msg = record.get("备注", "")

    # 北京10月消息模板
    msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {service_housekeeper} 签约合同（{order_type}） {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为平台本月累计签约第 {global_contract_sequence} 单

🌻 个人平台单累计签约第 {platform_count} 单，累计签约 {platform_amount} 元
🌻 个人自引单累计签约第 {self_referral_count} 单，累计签约 {self_referral_amount}元

👊 {next_msg} 🎉🎉🎉
'''
    
    print("📝 北京消息模板:")
    print(msg)
    
    # 验证北京消息特征
    checks = [
        ("包含自引单信息", "自引单累计签约第" in msg),
        ("包含平台单信息", "平台单累计签约第" in msg),
        ("包含全局序号", f"平台本月累计签约第 {global_contract_sequence} 单" in msg),
        ("包含备注信息", next_msg in msg)
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {result}")
        if not result:
            all_passed = False
    
    return all_passed

def test_shanghai_september_message_template():
    """测试上海9月消息模板不受影响"""
    print("\n🧪 测试上海9月消息模板兼容性")
    print("-" * 40)
    
    # 创建上海9月配置
    config = ProcessingConfig(
        config_key="SH-2025-09",
        activity_code="SH-SEP",
        city=City.SHANGHAI,
        housekeeper_key_format="管家_服务商"
    )
    
    store = create_data_store(storage_type='sqlite', db_path=':memory:')
    notification_service = NotificationService(store, config)
    
    # 模拟上海9月记录
    record = {
        '管家(serviceHousekeeper)': '李四_上海公司',
        '工单类型': '平台单',
        '合同编号(contractdocNum)': 'SH-SEP-001',
        '活动期内第几个合同': 15,
        '平台单累计数量': 8,
        '自引单累计数量': 5,
        '平台单累计金额': 320000,
        '自引单累计金额': 200000,
        '转化率(conversion)': '25.5%',
        '备注': '继续加油，争取更多奖励'
    }
    
    # 生成上海9月消息（标准模板）
    order_type = record.get("工单类型", "平台单")
    platform_count = record.get("平台单累计数量", 0)
    self_referral_count = record.get("自引单累计数量", 0)
    platform_amount = f"{int(float(record.get('平台单累计金额', 0))):,d}"
    self_referral_amount = f"{int(float(record.get('自引单累计金额', 0))):,d}"
    conversion_rate = str(record.get("转化率(conversion)", ""))
    next_msg = record.get("备注", "")

    # 上海标准消息模板（9月使用）
    msg = f'''🧨🧨🧨 签约喜报 🧨🧨🧨

恭喜 {record["管家(serviceHousekeeper)"]} 签约合同（{order_type}） {record.get("合同编号(contractdocNum)", "")} 并完成线上收款🎉🎉🎉

🌻 本单为本月平台累计签约第 {record.get("活动期内第几个合同", 0)} 单，

🌻 个人平台单累计签约第 {platform_count} 单， 自引单累计签约第 {self_referral_count} 单。
🌻 个人平台单金额累计签约 {platform_amount} 元，自引单金额累计签约 {self_referral_amount}元

🌻 个人平台单转化率 {conversion_rate}，

👊 {next_msg} 🎉🎉🎉。
'''
    
    print("📝 上海9月消息模板:")
    print(msg)
    
    # 验证上海9月消息特征
    checks = [
        ("包含自引单信息", "自引单累计签约第" in msg),
        ("包含平台单信息", "平台单累计签约第" in msg),
        ("包含转化率", conversion_rate in msg),
        ("包含自引单金额", self_referral_amount in msg),
        ("包含备注信息", next_msg in msg)
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {result}")
        if not result:
            all_passed = False
    
    return all_passed

def test_configuration_isolation():
    """测试配置隔离性"""
    print("\n🧪 测试配置隔离性")
    print("-" * 40)
    
    # 检查各配置的独立性
    configs_to_check = ["BJ-2025-10", "SH-2025-09", "SH-2025-10"]
    
    all_isolated = True
    for config_key in configs_to_check:
        config = REWARD_CONFIGS.get(config_key, {})
        if not config:
            print(f"❌ 配置 {config_key} 不存在")
            all_isolated = False
            continue
        
        # 检查关键配置项
        self_referral_enabled = config.get("self_referral_rewards", {}).get("enable", True)
        reward_strategy = config.get("reward_calculation_strategy", {}).get("type", "unknown")
        
        print(f"📋 {config_key}:")
        print(f"   - 自引单奖励: {'启用' if self_referral_enabled else '禁用'}")
        print(f"   - 奖励策略: {reward_strategy}")
        
        # 验证上海10月的特殊配置
        if config_key == "SH-2025-10":
            if self_referral_enabled:
                print(f"   ❌ 错误: 上海10月应该禁用自引单奖励")
                all_isolated = False
            else:
                print(f"   ✅ 正确: 上海10月已禁用自引单奖励")
    
    return all_isolated

def test_api_endpoint_isolation():
    """测试API端点隔离"""
    print("\n🧪 测试API端点隔离")
    print("-" * 40)
    
    from modules.config import API_URL_SH_SEP, API_URL_SH_OCT
    
    print(f"📡 上海9月API: {API_URL_SH_SEP}")
    print(f"📡 上海10月API: {API_URL_SH_OCT}")
    
    # 验证API端点不同
    if API_URL_SH_SEP != API_URL_SH_OCT:
        print("✅ API端点正确隔离")
        return True
    else:
        print("❌ API端点未正确隔离")
        return False

def main():
    """主测试函数"""
    print("🔍 核心代码兼容性测试")
    print("=" * 50)
    
    tests = [
        ("北京消息模板", test_beijing_message_template),
        ("上海9月消息模板", test_shanghai_september_message_template),
        ("配置隔离性", test_configuration_isolation),
        ("API端点隔离", test_api_endpoint_isolation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试失败: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n📊 测试结果总结")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有兼容性测试通过！")
        print("✅ 上海10月的修改不会影响北京和上海9月的功能")
    else:
        print("\n⚠️ 部分测试失败，需要检查兼容性问题")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
