#!/usr/bin/env python3
"""
文档整理工具

分析和整理项目文档，识别过时、重复或无用的文档。

使用方法:
    python scripts/document_organizer.py
    python scripts/document_organizer.py --output reports/document_analysis.md
"""

import sys
import os
from typing import Dict, List, Set
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class DocumentOrganizer:
    """文档整理器"""
    
    def __init__(self):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / 'docs'
        self.analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'total_docs': 0,
            'categories': {},
            'duplicates': [],
            'outdated': [],
            'core_docs': [],
            'recommendations': []
        }
    
    def analyze_all(self):
        """执行完整分析"""
        print("📚 开始文档分析...")
        
        if not self.docs_dir.exists():
            print("❌ docs目录不存在")
            return
        
        self.categorize_documents()
        self.identify_duplicates()
        self.identify_outdated()
        self.identify_core_docs()
        self.generate_recommendations()
        
        print("✅ 文档分析完成")
    
    def categorize_documents(self):
        """分类文档"""
        print("📋 分类文档...")
        
        categories = {
            'validation': [],
            'planning': [],
            'status': [],
            'guide': [],
            'architecture': [],
            'testing': [],
            'deployment': [],
            'business': [],
            'other': []
        }
        
        # 遍历所有markdown文件
        for doc_file in self.docs_dir.rglob("*.md"):
            if doc_file.is_file():
                doc_name = doc_file.name.lower()
                relative_path = str(doc_file.relative_to(self.project_root))
                
                # 根据文件名分类
                if any(keyword in doc_name for keyword in ['valid', 'verify', 'check', 'test']):
                    categories['validation'].append(relative_path)
                elif any(keyword in doc_name for keyword in ['plan', 'roadmap', 'phase']):
                    categories['planning'].append(relative_path)
                elif any(keyword in doc_name for keyword in ['status', 'update', 'report']):
                    categories['status'].append(relative_path)
                elif any(keyword in doc_name for keyword in ['guide', 'how', 'instruction']):
                    categories['guide'].append(relative_path)
                elif any(keyword in doc_name for keyword in ['architecture', 'design', 'structure']):
                    categories['architecture'].append(relative_path)
                elif any(keyword in doc_name for keyword in ['test', 'spec']):
                    categories['testing'].append(relative_path)
                elif any(keyword in doc_name for keyword in ['deploy', 'install', 'setup']):
                    categories['deployment'].append(relative_path)
                elif any(keyword in doc_name for keyword in ['business', 'rule', 'config']):
                    categories['business'].append(relative_path)
                else:
                    categories['other'].append(relative_path)
        
        self.analysis_result['categories'] = categories
        self.analysis_result['total_docs'] = sum(len(docs) for docs in categories.values())
    
    def identify_duplicates(self):
        """识别重复文档"""
        print("🔍 识别重复文档...")
        
        # 按主题分组
        topic_groups = {
            'beijing_validation': [],
            'shanghai_validation': [],
            'integration_test': [],
            'phase_plan': [],
            'status_report': []
        }
        
        all_docs = []
        for category_docs in self.analysis_result['categories'].values():
            all_docs.extend(category_docs)
        
        for doc_path in all_docs:
            doc_name = Path(doc_path).name.lower()
            
            if 'beijing' in doc_name and 'valid' in doc_name:
                topic_groups['beijing_validation'].append(doc_path)
            elif 'shanghai' in doc_name and 'valid' in doc_name:
                topic_groups['shanghai_validation'].append(doc_path)
            elif 'integration' in doc_name and 'test' in doc_name:
                topic_groups['integration_test'].append(doc_path)
            elif 'phase' in doc_name and 'plan' in doc_name:
                topic_groups['phase_plan'].append(doc_path)
            elif 'status' in doc_name or 'report' in doc_name:
                topic_groups['status_report'].append(doc_path)
        
        # 识别可能重复的组
        for topic, docs in topic_groups.items():
            if len(docs) > 1:
                self.analysis_result['duplicates'].append({
                    'topic': topic,
                    'documents': docs,
                    'count': len(docs)
                })
    
    def identify_outdated(self):
        """识别过时文档"""
        print("📅 识别过时文档...")
        
        # 检查文件修改时间和内容
        outdated_indicators = [
            'TODO',
            '待完成',
            '计划中',
            '准备中',
            'v0.',
            '草稿',
            'draft'
        ]
        
        for category_docs in self.analysis_result['categories'].values():
            for doc_path in category_docs:
                full_path = self.project_root / doc_path
                
                try:
                    # 检查文件内容
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查过时指标
                    outdated_score = 0
                    found_indicators = []
                    
                    for indicator in outdated_indicators:
                        if indicator in content:
                            outdated_score += 1
                            found_indicators.append(indicator)
                    
                    # 检查文件大小
                    if len(content) < 500:  # 内容太少可能是草稿
                        outdated_score += 1
                        found_indicators.append('内容过少')
                    
                    # 如果过时指标较多，标记为过时
                    if outdated_score >= 2:
                        self.analysis_result['outdated'].append({
                            'document': doc_path,
                            'score': outdated_score,
                            'indicators': found_indicators,
                            'size': len(content)
                        })
                        
                except Exception as e:
                    print(f"⚠️  无法分析文档 {doc_path}: {e}")
    
    def identify_core_docs(self):
        """识别核心文档"""
        print("⭐ 识别核心文档...")
        
        # 核心文档的特征
        core_indicators = [
            ('README.md', 10),
            ('architecture', 8),
            ('guide', 7),
            ('plan', 6),
            ('config', 6),
            ('deployment', 7),
            ('validation', 5)
        ]
        
        for category_docs in self.analysis_result['categories'].values():
            for doc_path in category_docs:
                doc_name = Path(doc_path).name.lower()
                
                score = 0
                reasons = []
                
                # 计算核心文档分数
                for indicator, weight in core_indicators:
                    if indicator in doc_name or indicator in doc_path.lower():
                        score += weight
                        reasons.append(f"{indicator}({weight})")
                
                # 检查文件大小（内容丰富的文档更重要）
                try:
                    full_path = self.project_root / doc_path
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if len(content) > 2000:  # 内容丰富
                        score += 3
                        reasons.append("内容丰富(3)")
                    
                    # 检查是否有结构化内容
                    if content.count('#') > 5:  # 有多个标题
                        score += 2
                        reasons.append("结构化(2)")
                        
                except Exception:
                    pass
                
                # 核心文档阈值
                if score >= 8:
                    self.analysis_result['core_docs'].append({
                        'document': doc_path,
                        'score': score,
                        'reasons': reasons
                    })
    
    def generate_recommendations(self):
        """生成整理建议"""
        recommendations = []
        
        # 重复文档建议
        if self.analysis_result['duplicates']:
            recommendations.append({
                'category': '重复文档',
                'priority': 'high',
                'description': f"发现 {len(self.analysis_result['duplicates'])} 组重复主题文档",
                'action': '合并相同主题的文档，保留最完整和最新的版本'
            })
        
        # 过时文档建议
        if self.analysis_result['outdated']:
            recommendations.append({
                'category': '过时文档',
                'priority': 'medium',
                'description': f"发现 {len(self.analysis_result['outdated'])} 个可能过时的文档",
                'action': '更新或删除过时文档，确保文档的时效性'
            })
        
        # 文档结构建议
        total_docs = self.analysis_result['total_docs']
        if total_docs > 20:
            recommendations.append({
                'category': '文档数量',
                'priority': 'medium',
                'description': f"文档总数 {total_docs} 个，可能过多",
                'action': '精简文档数量，保留核心文档，归档历史文档'
            })
        
        # 核心文档建议
        core_count = len(self.analysis_result['core_docs'])
        recommendations.append({
            'category': '核心文档',
            'priority': 'low',
            'description': f"识别出 {core_count} 个核心文档",
            'action': '确保核心文档保持更新，作为项目的主要文档'
        })
        
        self.analysis_result['recommendations'] = recommendations
    
    def generate_report(self, output_file: str = None):
        """生成整理报告"""
        report_lines = []
        
        # 报告头部
        report_lines.append("# 文档整理分析报告")
        report_lines.append("")
        report_lines.append(f"**分析时间**: {self.analysis_result['timestamp']}")
        report_lines.append(f"**文档总数**: {self.analysis_result['total_docs']}")
        report_lines.append("")
        
        # 文档分类
        report_lines.append("## 📚 文档分类")
        for category, docs in self.analysis_result['categories'].items():
            if docs:
                report_lines.append(f"### {category.title()} ({len(docs)} 个)")
                for doc in sorted(docs):
                    report_lines.append(f"- {doc}")
                report_lines.append("")
        
        # 重复文档
        if self.analysis_result['duplicates']:
            report_lines.append("## 🔄 重复文档")
            for dup in self.analysis_result['duplicates']:
                report_lines.append(f"### {dup['topic']} ({dup['count']} 个)")
                for doc in dup['documents']:
                    report_lines.append(f"- {doc}")
                report_lines.append("")
        
        # 过时文档
        if self.analysis_result['outdated']:
            report_lines.append("## 📅 可能过时的文档")
            for outdated in self.analysis_result['outdated']:
                report_lines.append(f"### {outdated['document']}")
                report_lines.append(f"- **过时分数**: {outdated['score']}")
                report_lines.append(f"- **指标**: {', '.join(outdated['indicators'])}")
                report_lines.append(f"- **文件大小**: {outdated['size']} 字符")
                report_lines.append("")
        
        # 核心文档
        if self.analysis_result['core_docs']:
            report_lines.append("## ⭐ 核心文档")
            # 按分数排序
            sorted_core = sorted(self.analysis_result['core_docs'], 
                               key=lambda x: x['score'], reverse=True)
            for core in sorted_core:
                report_lines.append(f"### {core['document']} (分数: {core['score']})")
                report_lines.append(f"- **评分原因**: {', '.join(core['reasons'])}")
                report_lines.append("")
        
        # 整理建议
        if self.analysis_result['recommendations']:
            report_lines.append("## 💡 整理建议")
            for rec in self.analysis_result['recommendations']:
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                emoji = priority_emoji.get(rec['priority'], '⚪')
                report_lines.append(f"### {emoji} {rec['category']} ({rec['priority']})")
                report_lines.append(f"**问题**: {rec['description']}")
                report_lines.append(f"**建议**: {rec['action']}")
                report_lines.append("")
        
        # 推荐的文档结构
        report_lines.append("## 📁 推荐的文档结构")
        report_lines.append("```")
        report_lines.append("docs/")
        report_lines.append("├── README.md                    # 项目概述")
        report_lines.append("├── architecture.md              # 系统架构")
        report_lines.append("├── deployment_guide.md          # 部署指南")
        report_lines.append("├── validation_guide.md          # 验证指南")
        report_lines.append("├── business_rules.md            # 业务规则")
        report_lines.append("├── current_status.md            # 当前状态")
        report_lines.append("├── archived/                    # 归档文档")
        report_lines.append("│   ├── historical_reports/")
        report_lines.append("│   └── old_plans/")
        report_lines.append("└── reports/                     # 分析报告")
        report_lines.append("```")
        
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
    
    parser = argparse.ArgumentParser(description='文档整理工具')
    parser.add_argument('--output', '-o', help='输出报告文件路径')
    args = parser.parse_args()
    
    organizer = DocumentOrganizer()
    organizer.analyze_all()
    
    output_file = args.output or f"reports/document_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    organizer.generate_report(output_file)

if __name__ == "__main__":
    main()
