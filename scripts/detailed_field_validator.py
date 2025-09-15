#!/usr/bin/env python3
"""
详细字段级验证工具

用于逐字段对比新旧系统的输出结果，确保完全一致性。
这是手工测试的自动化版本，检查每个字段的值。

使用方法:
    python scripts/detailed_field_validator.py --job BJ-SEP --baseline baseline.csv --current current.csv
"""

import sys
import os
import csv
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP

# 添加modules路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'field_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

class FieldValidator:
    """字段级验证器"""
    
    def __init__(self, job_type: str):
        self.job_type = job_type
        self.errors = []
        self.warnings = []
        self.field_stats = {}
        
        # 定义关键字段
        self.critical_fields = [
            '合同ID(_id)',
            '活动编号', 
            '管家(serviceHousekeeper)',
            '服务商(orgName)',
            '合同金额(adjustRefundMoney)',
            '支付金额(paidAmount)',
            '计入业绩金额',
            '活动期内第几个合同',
            '管家累计单数',
            '管家累计金额',
            '奖励类型',
            '奖励名称',
            '激活奖励状态'
        ]
        
        # 定义数值字段（需要精确对比）
        self.numeric_fields = [
            '合同金额(adjustRefundMoney)',
            '支付金额(paidAmount)', 
            '计入业绩金额',
            '活动期内第几个合同',
            '管家累计单数',
            '管家累计金额',
            '激活奖励状态'
        ]
        
        # 定义文本字段（需要完全匹配）
        self.text_fields = [
            '合同ID(_id)',
            '活动编号',
            '管家(serviceHousekeeper)',
            '服务商(orgName)',
            '奖励类型',
            '奖励名称'
        ]

    def load_csv_data(self, filepath: str) -> List[Dict]:
        """加载CSV数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logging.error(f"加载CSV文件失败 {filepath}: {e}")
            return []

    def normalize_value(self, value: Any, field_name: str) -> Any:
        """标准化字段值"""
        if value is None or value == '':
            return None
            
        # 数值字段处理
        if field_name in self.numeric_fields:
            try:
                # 转换为Decimal进行精确计算
                return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except:
                return None
        
        # 文本字段处理
        if field_name in self.text_fields:
            return str(value).strip()
            
        # 其他字段
        return str(value).strip() if value else None

    def compare_field(self, field_name: str, baseline_value: Any, current_value: Any, 
                     contract_id: str) -> bool:
        """对比单个字段"""
        baseline_norm = self.normalize_value(baseline_value, field_name)
        current_norm = self.normalize_value(current_value, field_name)
        
        # 记录字段统计
        if field_name not in self.field_stats:
            self.field_stats[field_name] = {
                'total': 0,
                'matches': 0,
                'mismatches': 0,
                'baseline_nulls': 0,
                'current_nulls': 0
            }
        
        stats = self.field_stats[field_name]
        stats['total'] += 1
        
        # 空值处理
        if baseline_norm is None and current_norm is None:
            stats['matches'] += 1
            return True
        
        if baseline_norm is None:
            stats['baseline_nulls'] += 1
            stats['mismatches'] += 1
            self.errors.append({
                'type': 'field_mismatch',
                'contract_id': contract_id,
                'field': field_name,
                'baseline': baseline_norm,
                'current': current_norm,
                'issue': 'baseline为空但current有值'
            })
            return False
            
        if current_norm is None:
            stats['current_nulls'] += 1
            stats['mismatches'] += 1
            self.errors.append({
                'type': 'field_mismatch',
                'contract_id': contract_id,
                'field': field_name,
                'baseline': baseline_norm,
                'current': current_norm,
                'issue': 'current为空但baseline有值'
            })
            return False
        
        # 值对比
        if baseline_norm == current_norm:
            stats['matches'] += 1
            return True
        else:
            stats['mismatches'] += 1
            self.errors.append({
                'type': 'field_mismatch',
                'contract_id': contract_id,
                'field': field_name,
                'baseline': baseline_norm,
                'current': current_norm,
                'issue': '值不匹配'
            })
            return False

    def validate_business_logic(self, baseline_data: List[Dict], current_data: List[Dict]) -> bool:
        """验证业务逻辑"""
        print("🔍 验证业务逻辑...")
        
        # 创建合同ID索引
        baseline_index = {row['合同ID(_id)']: row for row in baseline_data}
        current_index = {row['合同ID(_id)']: row for row in current_data}
        
        business_logic_passed = True
        
        # 验证5万上限逻辑
        for contract_id, current_row in current_index.items():
            if contract_id not in baseline_index:
                continue
                
            baseline_row = baseline_index[contract_id]
            
            # 检查业绩金额是否超过5万
            try:
                performance_amount = Decimal(str(current_row.get('计入业绩金额', 0)))
                contract_amount = Decimal(str(current_row.get('合同金额(adjustRefundMoney)', 0)))
                
                if performance_amount > 50000:
                    # 应该被限制在5万
                    if contract_amount > 50000:
                        # 合同金额超过5万，业绩应该是5万
                        if performance_amount != 50000:
                            self.errors.append({
                                'type': 'business_logic_error',
                                'contract_id': contract_id,
                                'issue': f'5万上限逻辑错误: 合同{contract_amount}元，业绩应为50000元，实际{performance_amount}元'
                            })
                            business_logic_passed = False
            except:
                pass
        
        # 验证累计统计逻辑
        housekeeper_stats_baseline = {}
        housekeeper_stats_current = {}
        
        # 统计baseline
        for row in baseline_data:
            housekeeper = row.get('管家(serviceHousekeeper)', '')
            if housekeeper not in housekeeper_stats_baseline:
                housekeeper_stats_baseline[housekeeper] = {'count': 0, 'amount': Decimal('0')}
            housekeeper_stats_baseline[housekeeper]['count'] += 1
            try:
                amount = Decimal(str(row.get('计入业绩金额', 0)))
                housekeeper_stats_baseline[housekeeper]['amount'] += amount
            except:
                pass
        
        # 统计current
        for row in current_data:
            housekeeper = row.get('管家(serviceHousekeeper)', '')
            if housekeeper not in housekeeper_stats_current:
                housekeeper_stats_current[housekeeper] = {'count': 0, 'amount': Decimal('0')}
            housekeeper_stats_current[housekeeper]['count'] += 1
            try:
                amount = Decimal(str(row.get('计入业绩金额', 0)))
                housekeeper_stats_current[housekeeper]['amount'] += amount
            except:
                pass
        
        # 对比累计统计
        for housekeeper in housekeeper_stats_baseline:
            if housekeeper not in housekeeper_stats_current:
                self.errors.append({
                    'type': 'business_logic_error',
                    'issue': f'管家累计统计错误: {housekeeper} 在current中缺失'
                })
                business_logic_passed = False
                continue
                
            baseline_stats = housekeeper_stats_baseline[housekeeper]
            current_stats = housekeeper_stats_current[housekeeper]
            
            if baseline_stats['count'] != current_stats['count']:
                self.errors.append({
                    'type': 'business_logic_error',
                    'issue': f'管家累计单数错误: {housekeeper} baseline={baseline_stats["count"]}, current={current_stats["count"]}'
                })
                business_logic_passed = False
                
            if abs(baseline_stats['amount'] - current_stats['amount']) > Decimal('0.01'):
                self.errors.append({
                    'type': 'business_logic_error',
                    'issue': f'管家累计金额错误: {housekeeper} baseline={baseline_stats["amount"]}, current={current_stats["amount"]}'
                })
                business_logic_passed = False
        
        return business_logic_passed

    def validate_data(self, baseline_file: str, current_file: str) -> bool:
        """执行完整的数据验证"""
        print(f"🔍 开始详细字段验证: {self.job_type}")
        print(f"📁 基准文件: {baseline_file}")
        print(f"📁 当前文件: {current_file}")
        
        # 加载数据
        baseline_data = self.load_csv_data(baseline_file)
        current_data = self.load_csv_data(current_file)
        
        if not baseline_data:
            self.errors.append({'type': 'file_error', 'issue': f'无法加载基准文件: {baseline_file}'})
            return False
            
        if not current_data:
            self.errors.append({'type': 'file_error', 'issue': f'无法加载当前文件: {current_file}'})
            return False
        
        print(f"📊 基准数据: {len(baseline_data)} 条记录")
        print(f"📊 当前数据: {len(current_data)} 条记录")
        
        # 记录数量对比
        if len(baseline_data) != len(current_data):
            self.errors.append({
                'type': 'count_mismatch',
                'issue': f'记录数量不匹配: baseline={len(baseline_data)}, current={len(current_data)}'
            })
        
        # 创建合同ID索引
        baseline_index = {row['合同ID(_id)']: row for row in baseline_data}
        current_index = {row['合同ID(_id)']: row for row in current_data}
        
        # 检查缺失的合同
        baseline_contracts = set(baseline_index.keys())
        current_contracts = set(current_index.keys())
        
        missing_in_current = baseline_contracts - current_contracts
        extra_in_current = current_contracts - baseline_contracts
        
        for contract_id in missing_in_current:
            self.errors.append({
                'type': 'missing_contract',
                'contract_id': contract_id,
                'issue': '合同在current中缺失'
            })
        
        for contract_id in extra_in_current:
            self.warnings.append({
                'type': 'extra_contract',
                'contract_id': contract_id,
                'issue': '合同在baseline中不存在'
            })
        
        # 逐字段对比
        common_contracts = baseline_contracts & current_contracts
        total_field_comparisons = 0
        successful_comparisons = 0
        
        print(f"🔍 开始逐字段对比 {len(common_contracts)} 个合同...")
        
        for contract_id in common_contracts:
            baseline_row = baseline_index[contract_id]
            current_row = current_index[contract_id]
            
            # 对比关键字段
            for field_name in self.critical_fields:
                if field_name in baseline_row and field_name in current_row:
                    total_field_comparisons += 1
                    if self.compare_field(field_name, baseline_row[field_name], 
                                        current_row[field_name], contract_id):
                        successful_comparisons += 1
        
        # 验证业务逻辑
        business_logic_passed = self.validate_business_logic(baseline_data, current_data)
        
        # 计算成功率
        if total_field_comparisons > 0:
            success_rate = (successful_comparisons / total_field_comparisons) * 100
            print(f"📊 字段对比成功率: {success_rate:.2f}% ({successful_comparisons}/{total_field_comparisons})")
        
        return len(self.errors) == 0 and business_logic_passed

    def generate_report(self) -> str:
        """生成验证报告"""
        report = []
        report.append(f"# {self.job_type} 详细字段验证报告")
        report.append(f"**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 总体结果
        if len(self.errors) == 0:
            report.append("## ✅ 验证结果: 通过")
        else:
            report.append("## ❌ 验证结果: 失败")
        
        report.append(f"- 错误数: {len(self.errors)}")
        report.append(f"- 警告数: {len(self.warnings)}")
        report.append("")
        
        # 字段统计
        report.append("## 📊 字段验证统计")
        for field_name, stats in self.field_stats.items():
            success_rate = (stats['matches'] / stats['total']) * 100 if stats['total'] > 0 else 0
            report.append(f"- **{field_name}**: {success_rate:.1f}% ({stats['matches']}/{stats['total']})")
        report.append("")
        
        # 错误详情
        if self.errors:
            report.append("## ❌ 错误详情")
            for i, error in enumerate(self.errors[:20]):  # 只显示前20个错误
                report.append(f"### 错误 {i+1}")
                for key, value in error.items():
                    report.append(f"- **{key}**: {value}")
                report.append("")
        
        # 警告详情
        if self.warnings:
            report.append("## ⚠️ 警告详情")
            for i, warning in enumerate(self.warnings[:10]):  # 只显示前10个警告
                report.append(f"### 警告 {i+1}")
                for key, value in warning.items():
                    report.append(f"- **{key}**: {value}")
                report.append("")
        
        return "\n".join(report)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='详细字段级验证工具')
    parser.add_argument('--job', required=True, help='Job类型 (如: BJ-SEP, SH-SEP)')
    parser.add_argument('--baseline', required=True, help='基准CSV文件路径')
    parser.add_argument('--current', required=True, help='当前CSV文件路径')
    parser.add_argument('--output', help='报告输出文件路径')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # 创建验证器
    validator = FieldValidator(args.job)
    
    # 执行验证
    success = validator.validate_data(args.baseline, args.current)
    
    # 生成报告
    report = validator.generate_report()
    
    # 输出报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 验证报告已保存到: {args.output}")
    else:
        print(report)
    
    # 返回结果
    if success:
        print("🎉 验证通过！")
        return 0
    else:
        print("❌ 验证失败，请检查错误详情")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
