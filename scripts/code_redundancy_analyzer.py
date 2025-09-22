#!/usr/bin/env python3
"""
代码冗余分析工具

分析项目中的冗余代码，包括：
1. 重复的函数
2. 兼容性包装函数
3. 重复的验证工具
4. 无用的配置文件

使用方法:
    python scripts/code_redundancy_analyzer.py
    python scripts/code_redundancy_analyzer.py --output reports/redundancy_analysis.md
"""

import sys
import os
import ast
import re
from typing import Dict, List, Set, Tuple
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class CodeRedundancyAnalyzer:
    """代码冗余分析器"""
    
    def __init__(self):
        self.project_root = Path(project_root)
        self.analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'duplicate_functions': [],
            'wrapper_functions': [],
            'redundant_scripts': [],
            'redundant_configs': [],
            'recommendations': []
        }
    
    def analyze_all(self):
        """执行完整分析"""
        print("🔍 开始代码冗余分析...")
        
        self.analyze_duplicate_functions()
        self.analyze_wrapper_functions()
        self.analyze_redundant_scripts()
        self.analyze_redundant_configs()
        self.generate_recommendations()
        
        print("✅ 分析完成")
    
    def analyze_duplicate_functions(self):
        """分析重复函数"""
        print("📋 分析重复函数...")
        
        # 查找所有Python文件
        python_files = list(self.project_root.rglob("*.py"))
        function_signatures = {}
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析AST
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        # 简单的函数签名（名称+参数数量）
                        signature = f"{func_name}({len(node.args.args)})"
                        
                        if signature not in function_signatures:
                            function_signatures[signature] = []
                        
                        function_signatures[signature].append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'name': func_name,
                            'line': node.lineno
                        })
                        
            except Exception as e:
                print(f"⚠️  解析文件失败 {file_path}: {e}")
        
        # 找出重复的函数
        for signature, locations in function_signatures.items():
            if len(locations) > 1:
                # 过滤掉明显的测试函数和特殊函数
                if not any(loc['name'].startswith(('test_', '__', '_test')) for loc in locations):
                    self.analysis_result['duplicate_functions'].append({
                        'signature': signature,
                        'locations': locations,
                        'count': len(locations)
                    })
    
    def analyze_wrapper_functions(self):
        """分析兼容性包装函数"""
        print("📋 分析兼容性包装函数...")
        
        wrapper_patterns = [
            r'def\s+(\w+)\s*\([^)]*\):\s*"""兼容性包装函数',
            r'def\s+(\w+)\s*\([^)]*\):\s*return\s+\w+_v2\(',
            r'# 兼容性函数',
            r'兼容性包装'
        ]
        
        # 检查特定文件
        wrapper_files = [
            'modules/core/beijing_jobs.py',
            'modules/core/shanghai_jobs.py'
        ]
        
        for file_path in wrapper_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 查找兼容性函数
                    for pattern in wrapper_patterns:
                        matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            self.analysis_result['wrapper_functions'].append({
                                'file': file_path,
                                'line': line_num,
                                'pattern': pattern,
                                'match': match.group(0)
                            })
                            
                except Exception as e:
                    print(f"⚠️  分析包装函数失败 {file_path}: {e}")
    
    def analyze_redundant_scripts(self):
        """分析冗余脚本"""
        print("📋 分析冗余脚本...")
        
        scripts_dir = self.project_root / 'scripts'
        if not scripts_dir.exists():
            return
        
        # 按功能分组脚本
        script_groups = {
            'validation': [],
            'comparison': [],
            'testing': [],
            'cleanup': [],
            'analysis': []
        }
        
        for script_file in scripts_dir.glob("*.py"):
            script_name = script_file.name.lower()
            
            if any(keyword in script_name for keyword in ['valid', 'check', 'verify']):
                script_groups['validation'].append(script_file.name)
            elif any(keyword in script_name for keyword in ['compare', 'diff', 'vs']):
                script_groups['comparison'].append(script_file.name)
            elif any(keyword in script_name for keyword in ['test', 'run']):
                script_groups['testing'].append(script_file.name)
            elif any(keyword in script_name for keyword in ['clean', 'clear', 'remove']):
                script_groups['cleanup'].append(script_file.name)
            elif any(keyword in script_name for keyword in ['analy', 'report', 'generate']):
                script_groups['analysis'].append(script_file.name)
        
        # 识别可能冗余的脚本组
        for group_name, scripts in script_groups.items():
            if len(scripts) > 3:  # 如果某类脚本超过3个，可能有冗余
                self.analysis_result['redundant_scripts'].append({
                    'group': group_name,
                    'scripts': scripts,
                    'count': len(scripts),
                    'recommendation': f'考虑合并{group_name}类脚本'
                })
    
    def analyze_redundant_configs(self):
        """分析冗余配置"""
        print("📋 分析冗余配置...")
        
        config_files = [
            'modules/config.py',
            'modules/core/config_adapter.py',
            'modules/core/production_config.py'
        ]
        
        config_analysis = []
        
        for config_file in config_files:
            full_path = self.project_root / config_file
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 统计配置项数量
                    reward_configs = content.count('REWARD_CONFIGS')
                    api_urls = content.count('API_URL')
                    file_paths = content.count('_FILE')
                    
                    config_analysis.append({
                        'file': config_file,
                        'size': len(content),
                        'lines': content.count('\n'),
                        'reward_configs': reward_configs,
                        'api_urls': api_urls,
                        'file_paths': file_paths
                    })
                    
                except Exception as e:
                    print(f"⚠️  分析配置文件失败 {config_file}: {e}")
        
        self.analysis_result['redundant_configs'] = config_analysis
    
    def generate_recommendations(self):
        """生成建议"""
        recommendations = []
        
        # 重复函数建议
        if self.analysis_result['duplicate_functions']:
            recommendations.append({
                'category': '重复函数',
                'priority': 'high',
                'description': f"发现 {len(self.analysis_result['duplicate_functions'])} 组重复函数",
                'action': '合并或重构重复函数，保留最优实现'
            })
        
        # 包装函数建议
        if self.analysis_result['wrapper_functions']:
            recommendations.append({
                'category': '兼容性包装',
                'priority': 'medium',
                'description': f"发现 {len(self.analysis_result['wrapper_functions'])} 个兼容性包装函数",
                'action': '评估是否仍需要兼容性包装，考虑直接迁移到新架构'
            })
        
        # 冗余脚本建议
        if self.analysis_result['redundant_scripts']:
            recommendations.append({
                'category': '冗余脚本',
                'priority': 'medium',
                'description': f"发现 {len(self.analysis_result['redundant_scripts'])} 组可能冗余的脚本",
                'action': '合并功能相似的脚本，保留最完整的版本'
            })
        
        # 配置文件建议
        if len(self.analysis_result['redundant_configs']) > 2:
            recommendations.append({
                'category': '配置文件',
                'priority': 'high',
                'description': f"发现 {len(self.analysis_result['redundant_configs'])} 个配置文件",
                'action': '统一配置系统，选择一个作为权威源'
            })
        
        self.analysis_result['recommendations'] = recommendations
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        skip_patterns = [
            '__pycache__',
            '.git',
            'venv',
            'env',
            '.pytest_cache',
            'node_modules'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def generate_report(self, output_file: str = None):
        """生成分析报告"""
        report_lines = []
        
        # 报告头部
        report_lines.append("# 代码冗余分析报告")
        report_lines.append("")
        report_lines.append(f"**分析时间**: {self.analysis_result['timestamp']}")
        report_lines.append("")
        
        # 总体概况
        report_lines.append("## 📊 总体概况")
        report_lines.append(f"- **重复函数组**: {len(self.analysis_result['duplicate_functions'])}")
        report_lines.append(f"- **兼容性包装函数**: {len(self.analysis_result['wrapper_functions'])}")
        report_lines.append(f"- **冗余脚本组**: {len(self.analysis_result['redundant_scripts'])}")
        report_lines.append(f"- **配置文件**: {len(self.analysis_result['redundant_configs'])}")
        report_lines.append("")
        
        # 重复函数详情
        if self.analysis_result['duplicate_functions']:
            report_lines.append("## 🔄 重复函数")
            for dup in self.analysis_result['duplicate_functions']:
                report_lines.append(f"### {dup['signature']} ({dup['count']} 个位置)")
                for loc in dup['locations']:
                    report_lines.append(f"- `{loc['file']}:{loc['line']}` - {loc['name']}")
                report_lines.append("")
        
        # 兼容性包装函数
        if self.analysis_result['wrapper_functions']:
            report_lines.append("## 🔗 兼容性包装函数")
            for wrapper in self.analysis_result['wrapper_functions']:
                report_lines.append(f"- `{wrapper['file']}:{wrapper['line']}` - {wrapper['match']}")
            report_lines.append("")
        
        # 冗余脚本
        if self.analysis_result['redundant_scripts']:
            report_lines.append("## 📜 冗余脚本分析")
            for group in self.analysis_result['redundant_scripts']:
                report_lines.append(f"### {group['group']} 类脚本 ({group['count']} 个)")
                for script in group['scripts']:
                    report_lines.append(f"- {script}")
                report_lines.append(f"**建议**: {group['recommendation']}")
                report_lines.append("")
        
        # 配置文件分析
        if self.analysis_result['redundant_configs']:
            report_lines.append("## ⚙️ 配置文件分析")
            for config in self.analysis_result['redundant_configs']:
                report_lines.append(f"### {config['file']}")
                report_lines.append(f"- 文件大小: {config['size']} 字符")
                report_lines.append(f"- 行数: {config['lines']}")
                report_lines.append(f"- 奖励配置: {config['reward_configs']}")
                report_lines.append(f"- API URLs: {config['api_urls']}")
                report_lines.append(f"- 文件路径: {config['file_paths']}")
                report_lines.append("")
        
        # 建议
        if self.analysis_result['recommendations']:
            report_lines.append("## 💡 优化建议")
            for rec in self.analysis_result['recommendations']:
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                emoji = priority_emoji.get(rec['priority'], '⚪')
                report_lines.append(f"### {emoji} {rec['category']} ({rec['priority']})")
                report_lines.append(f"**问题**: {rec['description']}")
                report_lines.append(f"**建议**: {rec['action']}")
                report_lines.append("")
        
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
    
    parser = argparse.ArgumentParser(description='代码冗余分析工具')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    args = parser.parse_args()
    
    analyzer = CodeRedundancyAnalyzer()
    analyzer.analyze_all()
    
    output_file = args.output or f"reports/redundancy_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    analyzer.generate_report(output_file)

if __name__ == "__main__":
    main()
