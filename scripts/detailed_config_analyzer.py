#!/usr/bin/env python3
"""
详细配置分析工具

深入分析新旧配置的具体内容差异，为配置统一提供详细信息。

使用方法:
    python scripts/detailed_config_analyzer.py
    python scripts/detailed_config_analyzer.py --config BJ-2025-09
"""

import sys
import os
import json
from typing import Dict, Any, List
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def analyze_specific_config(config_key: str):
    """分析特定配置的详细内容"""
    print(f"🔍 分析配置: {config_key}")
    print("=" * 60)
    
    # 加载旧配置
    try:
        from modules.config import REWARD_CONFIGS
        old_config = REWARD_CONFIGS.get(config_key)
        print(f"📥 旧配置系统 - {config_key}:")
        if old_config:
            print(json.dumps(old_config, indent=2, ensure_ascii=False))
        else:
            print("   ❌ 配置不存在")
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
    
    print("\n" + "-" * 40 + "\n")
    
    # 加载新配置
    try:
        from modules.core.config_adapter import ConfigAdapter
        new_config = ConfigAdapter.get_reward_config(config_key)
        print(f"📥 新配置系统 - {config_key}:")
        if new_config:
            print(json.dumps(new_config, indent=2, ensure_ascii=False))
        else:
            print("   ❌ 配置不存在")
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")

def analyze_all_configs():
    """分析所有配置"""
    print("🔍 分析所有配置差异")
    print("=" * 60)
    
    # 获取所有配置键
    config_keys = set()
    
    try:
        from modules.config import REWARD_CONFIGS
        config_keys.update(REWARD_CONFIGS.keys())
    except Exception as e:
        print(f"❌ 无法加载旧配置: {e}")
    
    try:
        from modules.core.config_adapter import ConfigAdapter
        test_keys = [
            "BJ-2025-06", "BJ-2025-08", "BJ-2025-09",
            "SH-2025-04", "SH-2025-08", "SH-2025-09"
        ]
        for key in test_keys:
            try:
                ConfigAdapter.get_reward_config(key)
                config_keys.add(key)
            except:
                pass
    except Exception as e:
        print(f"❌ 无法加载新配置: {e}")
    
    print(f"📋 发现配置键: {sorted(config_keys)}")
    print()
    
    # 分析每个配置
    for config_key in sorted(config_keys):
        print(f"\n{'='*20} {config_key} {'='*20}")
        analyze_config_differences(config_key)

def analyze_config_differences(config_key: str):
    """分析单个配置的差异"""
    old_config = None
    new_config = None
    
    # 加载旧配置
    try:
        from modules.config import REWARD_CONFIGS
        old_config = REWARD_CONFIGS.get(config_key)
    except Exception as e:
        print(f"⚠️  旧配置加载失败: {e}")
    
    # 加载新配置
    try:
        from modules.core.config_adapter import ConfigAdapter
        new_config = ConfigAdapter.get_reward_config(config_key)
    except Exception as e:
        print(f"⚠️  新配置加载失败: {e}")
    
    # 对比分析
    if old_config is None and new_config is None:
        print("❌ 两个系统都没有此配置")
    elif old_config is None:
        print("🆕 仅新系统有此配置")
        print("新配置内容:")
        print(json.dumps(new_config, indent=2, ensure_ascii=False))
    elif new_config is None:
        print("🗑️  仅旧系统有此配置")
        print("旧配置内容:")
        print(json.dumps(old_config, indent=2, ensure_ascii=False))
    else:
        # 详细对比
        differences = find_detailed_differences(old_config, new_config)
        if not differences:
            print("✅ 配置完全一致")
        else:
            print(f"❌ 发现 {len(differences)} 个差异:")
            for diff in differences:
                print(f"  - {diff}")

def find_detailed_differences(old_config: Dict, new_config: Dict, path: str = "") -> List[str]:
    """查找详细差异"""
    differences = []
    
    # 获取所有键
    all_keys = set(old_config.keys()) | set(new_config.keys())
    
    for key in all_keys:
        current_path = f"{path}.{key}" if path else key
        
        if key not in old_config:
            differences.append(f"{current_path}: 新增字段 = {new_config[key]}")
        elif key not in new_config:
            differences.append(f"{current_path}: 删除字段 = {old_config[key]}")
        else:
            old_value = old_config[key]
            new_value = new_config[key]
            
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                # 递归比较字典
                sub_differences = find_detailed_differences(old_value, new_value, current_path)
                differences.extend(sub_differences)
            elif old_value != new_value:
                differences.append(f"{current_path}: {old_value} → {new_value}")
    
    return differences

def check_critical_fields():
    """检查关键字段的一致性"""
    print("🎯 检查关键字段一致性")
    print("=" * 60)
    
    critical_configs = ["BJ-2025-09", "SH-2025-09"]
    critical_fields = [
        "lucky_number",
        "awards_mapping",
        "tiered_rewards.min_contracts",
        "tiered_rewards.tiers",
        "performance_limits.single_contract_cap"
    ]
    
    for config_key in critical_configs:
        print(f"\n📋 {config_key} 关键字段检查:")
        
        try:
            from modules.config import REWARD_CONFIGS
            from modules.core.config_adapter import ConfigAdapter
            
            old_config = REWARD_CONFIGS.get(config_key, {})
            new_config = ConfigAdapter.get_reward_config(config_key)
            
            for field_path in critical_fields:
                old_value = get_nested_value(old_config, field_path)
                new_value = get_nested_value(new_config, field_path)
                
                if old_value == new_value:
                    print(f"  ✅ {field_path}: 一致")
                else:
                    print(f"  ❌ {field_path}: {old_value} ≠ {new_value}")
                    
        except Exception as e:
            print(f"  ❌ 检查失败: {e}")

def get_nested_value(config: Dict, path: str):
    """获取嵌套字典的值"""
    keys = path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='详细配置分析工具')
    parser.add_argument('--config', '-c', help='分析特定配置')
    parser.add_argument('--critical', action='store_true', help='只检查关键字段')
    args = parser.parse_args()
    
    if args.critical:
        check_critical_fields()
    elif args.config:
        analyze_specific_config(args.config)
    else:
        analyze_all_configs()
        print("\n" + "="*60)
        check_critical_fields()

if __name__ == "__main__":
    main()
