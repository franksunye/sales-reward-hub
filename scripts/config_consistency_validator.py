#!/usr/bin/env python3
"""
配置一致性验证工具

检查新旧配置系统的一致性，识别所有差异。
这是全面验证计划的第一步。

使用方法:
    python scripts/config_consistency_validator.py
    python scripts/config_consistency_validator.py --output reports/config_diff.md
"""

import sys
import os
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def load_old_configs():
    """加载旧配置系统的配置"""
    try:
        from modules.config import REWARD_CONFIGS
        return REWARD_CONFIGS
    except ImportError as e:
        print(f"❌ 无法加载旧配置: {e}")
        return {}

def load_new_configs():
    """加载新配置系统的配置"""
    new_configs = {}
    try:
        from modules.core.config_adapter import ConfigAdapter
        
        # 测试所有已知的配置键
        config_keys = [
            "BJ-2025-06", "BJ-2025-08", "BJ-2025-09",
            "SH-2025-04", "SH-2025-08", "SH-2025-09"
        ]
        
        for key in config_keys:
            try:
                config = ConfigAdapter.get_reward_config(key)
                new_configs[key] = config
            except Exception as e:
                print(f"⚠️  无法加载新配置 {key}: {e}")
                
    except ImportError as e:
        print(f"❌ 无法加载新配置系统: {e}")
        
    return new_configs

def compare_configs(old_configs: Dict, new_configs: Dict) -> Dict:
    """对比新旧配置"""
    comparison_result = {
        'timestamp': datetime.now().isoformat(),
        'old_config_count': len(old_configs),
        'new_config_count': len(new_configs),
        'common_keys': [],
        'old_only_keys': [],
        'new_only_keys': [],
        'differences': [],
        'is_consistent': True
    }
    
    all_keys = set(old_configs.keys()) | set(new_configs.keys())
    old_keys = set(old_configs.keys())
    new_keys = set(new_configs.keys())
    
    comparison_result['common_keys'] = list(old_keys & new_keys)
    comparison_result['old_only_keys'] = list(old_keys - new_keys)
    comparison_result['new_only_keys'] = list(new_keys - old_keys)
    
    # 对比共同的配置键
    for key in comparison_result['common_keys']:
        old_config = old_configs[key]
        new_config = new_configs[key]
        
        diff = compare_single_config(key, old_config, new_config)
        if diff['has_differences']:
            comparison_result['differences'].append(diff)
            comparison_result['is_consistent'] = False
    
    # 检查缺失的配置
    if comparison_result['old_only_keys'] or comparison_result['new_only_keys']:
        comparison_result['is_consistent'] = False
    
    return comparison_result

def compare_single_config(key: str, old_config: Dict, new_config: Dict) -> Dict:
    """对比单个配置"""
    diff = {
        'config_key': key,
        'has_differences': False,
        'field_differences': []
    }
    
    # 获取所有字段
    all_fields = set(old_config.keys()) | set(new_config.keys())
    
    for field in all_fields:
        old_value = old_config.get(field)
        new_value = new_config.get(field)
        
        if old_value != new_value:
            diff['has_differences'] = True
            diff['field_differences'].append({
                'field': field,
                'old_value': old_value,
                'new_value': new_value,
                'difference_type': get_difference_type(old_value, new_value)
            })
    
    return diff

def get_difference_type(old_value: Any, new_value: Any) -> str:
    """获取差异类型"""
    if old_value is None and new_value is not None:
        return "新增字段"
    elif old_value is not None and new_value is None:
        return "缺失字段"
    elif type(old_value) != type(new_value):
        return "类型差异"
    elif isinstance(old_value, dict) and isinstance(new_value, dict):
        return "结构差异"
    elif isinstance(old_value, list) and isinstance(new_value, list):
        return "列表差异"
    else:
        return "值差异"

def generate_report(comparison_result: Dict, output_file: str = None):
    """生成对比报告"""
    report_lines = []
    
    # 报告头部
    report_lines.append("# 配置一致性验证报告")
    report_lines.append("")
    report_lines.append(f"**验证时间**: {comparison_result['timestamp']}")
    report_lines.append(f"**旧配置数量**: {comparison_result['old_config_count']}")
    report_lines.append(f"**新配置数量**: {comparison_result['new_config_count']}")
    report_lines.append("")
    
    # 总体结果
    if comparison_result['is_consistent']:
        report_lines.append("## ✅ 验证结果：配置完全一致")
    else:
        report_lines.append("## ❌ 验证结果：发现配置差异")
    
    report_lines.append("")
    
    # 配置键对比
    report_lines.append("## 📋 配置键对比")
    report_lines.append(f"- **共同配置**: {len(comparison_result['common_keys'])} 个")
    report_lines.append(f"- **仅旧配置**: {len(comparison_result['old_only_keys'])} 个")
    report_lines.append(f"- **仅新配置**: {len(comparison_result['new_only_keys'])} 个")
    report_lines.append("")
    
    if comparison_result['common_keys']:
        report_lines.append("### 共同配置键")
        for key in sorted(comparison_result['common_keys']):
            report_lines.append(f"- {key}")
        report_lines.append("")
    
    if comparison_result['old_only_keys']:
        report_lines.append("### ⚠️ 仅在旧配置中存在")
        for key in sorted(comparison_result['old_only_keys']):
            report_lines.append(f"- {key}")
        report_lines.append("")
    
    if comparison_result['new_only_keys']:
        report_lines.append("### ⚠️ 仅在新配置中存在")
        for key in sorted(comparison_result['new_only_keys']):
            report_lines.append(f"- {key}")
        report_lines.append("")
    
    # 详细差异
    if comparison_result['differences']:
        report_lines.append("## 🔍 详细差异分析")
        report_lines.append("")
        
        for diff in comparison_result['differences']:
            report_lines.append(f"### {diff['config_key']}")
            report_lines.append("")
            
            for field_diff in diff['field_differences']:
                report_lines.append(f"#### {field_diff['field']} ({field_diff['difference_type']})")
                report_lines.append(f"- **旧配置**: `{field_diff['old_value']}`")
                report_lines.append(f"- **新配置**: `{field_diff['new_value']}`")
                report_lines.append("")
    
    # 建议
    report_lines.append("## 💡 建议")
    if comparison_result['is_consistent']:
        report_lines.append("- ✅ 配置完全一致，可以安全进行下一步验证")
    else:
        report_lines.append("- ❌ 需要统一配置后再进行等价性验证")
        report_lines.append("- 🔧 建议选择一个配置系统作为权威源")
        report_lines.append("- 📝 更新所有不一致的配置项")
    
    report_content = "\n".join(report_lines)
    
    # 输出报告
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"📄 报告已保存到: {output_file}")
    else:
        print(report_content)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='配置一致性验证工具')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    args = parser.parse_args()
    
    print("🔍 开始配置一致性验证...")
    print()
    
    # 加载配置
    print("📥 加载旧配置系统...")
    old_configs = load_old_configs()
    print(f"   加载了 {len(old_configs)} 个配置")
    
    print("📥 加载新配置系统...")
    new_configs = load_new_configs()
    print(f"   加载了 {len(new_configs)} 个配置")
    print()
    
    # 对比配置
    print("⚖️  对比配置...")
    comparison_result = compare_configs(old_configs, new_configs)
    
    # 生成报告
    output_file = args.output or f"reports/config_consistency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    generate_report(comparison_result, output_file)
    
    # 返回结果
    if comparison_result['is_consistent']:
        print("\n✅ 配置验证通过！")
        return 0
    else:
        print(f"\n❌ 发现 {len(comparison_result['differences'])} 个配置差异")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
