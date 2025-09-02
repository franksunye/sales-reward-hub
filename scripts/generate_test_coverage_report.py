#!/usr/bin/env python3
"""
测试覆盖率报告生成工具
自动分析功能点测试覆盖情况，生成可视化报告
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestCoverageAnalyzer:
    """测试覆盖率分析器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.test_dir = self.project_root / "tests"
        self.docs_dir = self.project_root / "docs"
        
        # 功能点定义
        self.feature_points = {
            "F01": {"name": "工单金额上限调整", "acceptance_criteria": 3},
            "F02": {"name": "幸运数字机制重构", "acceptance_criteria": 4},
            "F03": {"name": "节节高门槛提升", "acceptance_criteria": 4},
            "F04": {"name": "徽章机制禁用", "acceptance_criteria": 3},
            "F05": {"name": "配置驱动设计", "acceptance_criteria": 3},
            "F06": {"name": "幸运数字逻辑通用化", "acceptance_criteria": 3},
            "F07": {"name": "徽章配置支持", "acceptance_criteria": 3},
            "F08": {"name": "数据处理包装函数", "acceptance_criteria": 3},
            "F09": {"name": "通知包装函数", "acceptance_criteria": 3},
            "F10": {"name": "回归测试保障", "acceptance_criteria": 3}
        }
    
    def analyze_test_file(self, test_file_path):
        """分析测试文件，提取功能点覆盖信息"""
        coverage_data = {}
        
        try:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找功能点测试类
            for feature_id in self.feature_points.keys():
                pattern = rf'class Test{feature_id}.*?:'
                if re.search(pattern, content):
                    coverage_data[feature_id] = self._analyze_feature_tests(content, feature_id)
                else:
                    coverage_data[feature_id] = {"implemented": False, "test_methods": [], "coverage": 0}
        
        except FileNotFoundError:
            print(f"测试文件不存在: {test_file_path}")
            # 初始化空覆盖数据
            for feature_id in self.feature_points.keys():
                coverage_data[feature_id] = {"implemented": False, "test_methods": [], "coverage": 0}
        
        return coverage_data
    
    def _analyze_feature_tests(self, content, feature_id):
        """分析特定功能点的测试方法"""
        # 查找测试类内容
        class_pattern = rf'class Test{feature_id}.*?(?=class|\Z)'
        class_match = re.search(class_pattern, content, re.DOTALL)
        
        if not class_match:
            return {"implemented": False, "test_methods": [], "coverage": 0}
        
        class_content = class_match.group(0)
        
        # 查找验收标准测试方法
        ac_pattern = r'def test_AC\d+_\d+.*?:'
        test_methods = re.findall(ac_pattern, class_content)
        
        # 计算覆盖率
        expected_ac_count = self.feature_points[feature_id]["acceptance_criteria"]
        actual_ac_count = len(test_methods)
        coverage = (actual_ac_count / expected_ac_count) * 100 if expected_ac_count > 0 else 0
        
        return {
            "implemented": True,
            "test_methods": test_methods,
            "coverage": round(coverage, 1),
            "ac_implemented": actual_ac_count,
            "ac_expected": expected_ac_count
        }
    
    def generate_coverage_report(self):
        """生成测试覆盖率报告"""
        # 分析功能点驱动测试文件
        feature_driven_test_file = self.test_dir / "test_beijing_sep_feature_driven.py"
        coverage_data = self.analyze_test_file(feature_driven_test_file)
        
        # 生成报告
        report = self._generate_markdown_report(coverage_data)
        
        # 保存报告
        report_file = self.docs_dir / "beijing_sep_test_coverage_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"测试覆盖率报告已生成: {report_file}")
        return coverage_data
    
    def _generate_markdown_report(self, coverage_data):
        """生成Markdown格式的覆盖率报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算总体统计
        total_features = len(self.feature_points)
        implemented_features_count = sum(1 for data in coverage_data.values() if data["implemented"])
        total_ac_expected = sum(fp["acceptance_criteria"] for fp in self.feature_points.values())
        total_ac_implemented = sum(data.get("ac_implemented", 0) for data in coverage_data.values())
        overall_coverage = (total_ac_implemented / total_ac_expected) * 100 if total_ac_expected > 0 else 0
        
        report = f"""# 北京9月测试覆盖率报告

## 报告信息
- **生成时间**: {timestamp}
- **测试方法**: 功能点驱动测试
- **分析文件**: test_beijing_sep_feature_driven.py

## 总体统计

| 指标 | 数值 | 百分比 |
|------|------|--------|
| 功能点总数 | {total_features} | 100% |
| 已实现功能点 | {implemented_features_count} | {(implemented_features_count/total_features)*100:.1f}% |
| 验收标准总数 | {total_ac_expected} | 100% |
| 已实现验收标准 | {total_ac_implemented} | {overall_coverage:.1f}% |

## 功能点详细覆盖情况

| 功能点 | 功能名称 | 验收标准 | 已实现 | 覆盖率 | 状态 |
|--------|----------|----------|--------|--------|------|
"""
        
        for feature_id, feature_info in self.feature_points.items():
            data = coverage_data[feature_id]
            status_icon = "✅" if data["coverage"] == 100 else "⭕" if data["implemented"] else "❌"
            
            report += f"| {feature_id} | {feature_info['name']} | {feature_info['acceptance_criteria']} | {data.get('ac_implemented', 0)} | {data['coverage']:.1f}% | {status_icon} |\n"
        
        report += f"""
## 详细分析

### 高优先级待实现功能点
"""
        
        # 找出覆盖率低的功能点
        low_coverage_features = [(fid, data) for fid, data in coverage_data.items()
                               if data["coverage"] < 100]
        
        if low_coverage_features:
            for feature_id, data in low_coverage_features:
                feature_name = self.feature_points[feature_id]["name"]
                report += f"- **{feature_id}**: {feature_name} (覆盖率: {data['coverage']:.1f}%)\n"
        else:
            report += "🎉 所有功能点测试覆盖率已达到100%！\n"
        
        report += f"""
### 测试执行建议

#### 按优先级执行测试
```bash
# 1. 执行已实现的功能点测试
"""
        
        implemented_features_list = [fid for fid, data in coverage_data.items() if data["implemented"]]
        for feature_id in implemented_features_list:
            report += f"python -m pytest tests/test_beijing_sep_feature_driven.py::Test{feature_id} -v\n"
        
        report += f"""
# 2. 执行回归测试
python -m pytest tests/test_regression_baseline.py -v

# 3. 执行集成测试
python -m pytest tests/test_beijing_sep_integration.py -v
```

#### 开发优先级建议
"""
        
        if low_coverage_features:
            # 按覆盖率排序，优先开发覆盖率最低的
            sorted_features = sorted(low_coverage_features, key=lambda x: x[1]["coverage"])
            for i, (feature_id, data) in enumerate(sorted_features[:3], 1):
                feature_name = self.feature_points[feature_id]["name"]
                report += f"{i}. **{feature_id}**: {feature_name}\n"
        
        report += f"""
## 质量门禁标准

### 当前状态
- 总体覆盖率: {overall_coverage:.1f}% (目标: 100%)
- 功能点实现率: {(implemented_features_count/total_features)*100:.1f}% (目标: 100%)

### 发布标准
- [ ] 所有功能点覆盖率达到100%
- [ ] 回归测试通过率100%
- [ ] 集成测试通过率100%

---
*本报告由测试覆盖率分析工具自动生成*
"""
        
        return report
    
    def print_summary(self, coverage_data):
        """打印覆盖率摘要"""
        total_ac_expected = sum(fp["acceptance_criteria"] for fp in self.feature_points.values())
        total_ac_implemented = sum(data.get("ac_implemented", 0) for data in coverage_data.values())
        overall_coverage = (total_ac_implemented / total_ac_expected) * 100 if total_ac_expected > 0 else 0
        
        print(f"\n📊 北京9月测试覆盖率摘要")
        print(f"{'='*50}")
        print(f"总体覆盖率: {overall_coverage:.1f}%")
        print(f"验收标准: {total_ac_implemented}/{total_ac_expected}")
        print(f"{'='*50}")
        
        for feature_id, data in coverage_data.items():
            status = "✅" if data["coverage"] == 100 else "⭕" if data["implemented"] else "❌"
            feature_name = self.feature_points[feature_id]["name"]
            print(f"{status} {feature_id}: {feature_name} ({data['coverage']:.1f}%)")


def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    analyzer = TestCoverageAnalyzer(project_root)
    
    print("🔍 分析北京9月测试覆盖率...")
    coverage_data = analyzer.generate_coverage_report()
    analyzer.print_summary(coverage_data)


if __name__ == "__main__":
    main()
