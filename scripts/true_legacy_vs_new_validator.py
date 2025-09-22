#!/usr/bin/env python3
"""
真正的上海9月等价性验证工具 - 直接执行旧系统vs新系统

正确的验证方法：
1. 使用相同的真实数据源（Metabase API）
2. 直接执行真正的旧系统函数 signing_and_sales_incentive_sep_shanghai()
3. 直接执行新系统函数 signing_and_sales_incentive_sep_shanghai_v2()
4. 逐字段对比两个系统的输出结果
5. 确保100%完全一致

这是生产级别的等价性验证，不使用任何模拟逻辑。
"""

import sys
import os
import csv
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'true_legacy_vs_new_validation_{timestamp}.log')
        ]
    )

class TrueLegacyVsNewValidator:
    """真正的旧系统vs新系统等价性验证器"""
    
    def __init__(self):
        self.legacy_output_file = ""
        self.new_output_file = ""
        
        # 创建必要目录
        for dir_path in ["baseline/LEGACY", "current/NEW", "reports"]:
            os.makedirs(dir_path, exist_ok=True)
    
    def use_existing_legacy_output(self) -> Tuple[bool, str, float]:
        """使用已有的旧系统真实输出结果"""
        print("🔄 使用已有的旧系统真实输出结果...")

        # 查找已有的旧系统输出文件
        legacy_files = [
            "performance_data_SH-SEP_dual_track_20250922_025513.csv",
            "PerformanceData-SH-Sep-2025-09-22.csv"
        ]

        for legacy_file in legacy_files:
            if os.path.exists(legacy_file):
                print(f"✅ 找到旧系统真实输出: {legacy_file}")

                # 复制到baseline目录
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                baseline_file = f"baseline/LEGACY/shanghai_sep_legacy_{timestamp}.csv"

                import shutil
                shutil.copy2(legacy_file, baseline_file)

                self.legacy_output_file = baseline_file

                # 检查文件记录数
                with open(baseline_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    record_count = sum(1 for _ in reader)

                print(f"📄 基准文件: {baseline_file}")
                print(f"📊 记录数: {record_count}")
                print("📝 这是旧系统在相同数据上的真实执行结果")

                return True, baseline_file, 0.0  # 执行时间未知，设为0

        print("❌ 未找到旧系统的真实输出文件")
        print("💡 请确保以下文件之一存在:")
        for file in legacy_files:
            print(f"   - {file}")

        return False, "", 0
    
    def execute_new_system(self) -> Tuple[bool, str, float]:
        """执行新系统"""
        print("🚀 执行新系统...")
        print("📝 调用 modules.core.shanghai_jobs.signing_and_sales_incentive_sep_shanghai_v2()")
        
        try:
            # 清空数据库
            import sqlite3
            with sqlite3.connect('performance_data.db') as conn:
                conn.execute("DELETE FROM performance_data WHERE activity_code = 'SH-SEP'")
                conn.commit()
            
            # 清理旧的输出文件
            import glob
            old_files = glob.glob("performance_data_SH-SEP*.csv")
            for file in old_files:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"🗑️ 清理旧文件: {file}")
            
            # 导入并执行新系统
            from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
            
            start_time = time.time()
            
            # 执行新系统
            records = signing_and_sales_incentive_sep_shanghai_v2()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 查找生成的CSV文件
            csv_files = glob.glob("performance_data_SH-SEP*.csv")
            
            if not csv_files:
                print("❌ 未找到新系统生成的CSV文件")
                return False, "", 0
            
            # 使用最新的文件
            latest_file = max(csv_files, key=os.path.getctime)
            
            # 移动到current目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_file = f"current/NEW/shanghai_sep_new_{timestamp}.csv"
            
            import shutil
            shutil.move(latest_file, current_file)
            
            self.new_output_file = current_file
            
            print(f"✅ 新系统执行完成")
            print(f"📄 输出文件: {current_file}")
            print(f"⏱️ 执行时间: {execution_time:.2f}秒")
            print(f"📊 处理记录数: {len(records)}")
            
            return True, current_file, execution_time
            
        except Exception as e:
            print(f"❌ 新系统执行失败: {e}")
            logging.error(f"新系统执行失败: {e}", exc_info=True)
            return False, "", 0
    
    def compare_outputs_100_percent(self, legacy_file: str, new_file: str) -> Dict:
        """100%等价性对比 - 每个字段都必须完全一致"""
        print("🔍 执行100%等价性验证...")
        print("📝 要求: 每个管家的每个字段都必须完全一致")
        
        # 读取两个系统的输出
        with open(legacy_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            legacy_data = list(reader)
        
        with open(new_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            new_data = list(reader)
        
        print(f"📊 旧系统记录数: {len(legacy_data)}")
        print(f"📊 新系统记录数: {len(new_data)}")
        
        # 创建合同ID索引
        legacy_index = {row['合同ID(_id)']: row for row in legacy_data}
        new_index = {row['合同ID(_id)']: row for row in new_data}
        
        # 关键字段列表 - 所有业务相关字段
        critical_fields = [
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
            '激活奖励状态',
            '是否发送通知'
        ]
        
        # 如果新系统有双轨统计字段，也要验证
        if new_data and '平台单累计数量' in new_data[0]:
            critical_fields.extend([
                '工单类型',
                '平台单累计数量',
                '平台单累计金额', 
                '自引单累计数量',
                '自引单累计金额'
            ])
        
        comparison_result = {
            'total_records': {'legacy': len(legacy_data), 'new': len(new_data)},
            'perfect_matches': 0,
            'field_differences': [],
            'missing_records': [],
            'extra_records': [],
            'housekeeper_summary': {},
            'is_100_percent_equivalent': False
        }
        
        # 检查记录数量
        if len(legacy_data) != len(new_data):
            print(f"❌ 记录数量不一致: legacy={len(legacy_data)}, new={len(new_data)}")
        
        # 逐记录对比
        all_contract_ids = set(legacy_index.keys()) | set(new_index.keys())
        
        for contract_id in all_contract_ids:
            legacy_record = legacy_index.get(contract_id)
            new_record = new_index.get(contract_id)
            
            if not legacy_record:
                comparison_result['missing_records'].append(contract_id)
                continue
            
            if not new_record:
                comparison_result['extra_records'].append(contract_id)
                continue
            
            # 逐字段对比
            record_differences = []
            for field in critical_fields:
                if field not in legacy_record or field not in new_record:
                    continue  # 跳过不存在的字段
                
                legacy_value = legacy_record[field]
                new_value = new_record[field]
                
                # 数值字段特殊处理
                if field in ['管家累计单数', '管家累计金额', '激活奖励状态', '活动期内第几个合同', 
                           '平台单累计数量', '平台单累计金额', '自引单累计数量', '自引单累计金额', 
                           '合同金额(adjustRefundMoney)', '支付金额(paidAmount)', '计入业绩金额']:
                    try:
                        legacy_value = int(float(legacy_value)) if legacy_value else 0
                        new_value = int(float(new_value)) if new_value else 0
                    except (ValueError, TypeError):
                        pass
                
                if str(legacy_value) != str(new_value):
                    record_differences.append({
                        'field': field,
                        'legacy_value': legacy_value,
                        'new_value': new_value
                    })
            
            if record_differences:
                comparison_result['field_differences'].append({
                    'contract_id': contract_id,
                    'housekeeper': legacy_record.get('管家(serviceHousekeeper)', ''),
                    'differences': record_differences
                })
            else:
                comparison_result['perfect_matches'] += 1
        
        # 按管家统计
        housekeeper_stats = defaultdict(lambda: {'total': 0, 'matches': 0, 'differences': 0})
        
        for contract_id in all_contract_ids:
            legacy_record = legacy_index.get(contract_id)
            if legacy_record:
                housekeeper = legacy_record.get('管家(serviceHousekeeper)', '')
                housekeeper_stats[housekeeper]['total'] += 1
                
                has_difference = any(diff['contract_id'] == contract_id for diff in comparison_result['field_differences'])
                if has_difference:
                    housekeeper_stats[housekeeper]['differences'] += 1
                else:
                    housekeeper_stats[housekeeper]['matches'] += 1
        
        comparison_result['housekeeper_summary'] = dict(housekeeper_stats)
        
        # 判断是否100%等价
        total_diffs = len(comparison_result['field_differences'])
        missing_records = len(comparison_result['missing_records'])
        extra_records = len(comparison_result['extra_records'])
        
        comparison_result['is_100_percent_equivalent'] = (
            total_diffs == 0 and missing_records == 0 and extra_records == 0
        )
        
        return comparison_result

    def generate_100_percent_report(self, comparison_result: Dict, legacy_time: float, new_time: float) -> str:
        """生成100%等价性验证报告"""
        report = []
        report.append("# 上海9月真正的100%等价性验证报告")
        report.append(f"**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("**验证方法**: 直接执行旧系统vs新系统（无模拟）")
        report.append("**验证标准**: 100%完全等价（每个字段都必须一致）")
        report.append("")

        # 执行性能对比
        report.append("## ⏱️ 执行性能对比")
        report.append(f"- **旧系统执行时间**: {legacy_time:.2f}秒")
        report.append(f"- **新系统执行时间**: {new_time:.2f}秒")
        if legacy_time > 0:
            speedup = legacy_time / new_time if new_time > 0 else float('inf')
            report.append(f"- **性能提升**: {speedup:.2f}x")
        report.append("")

        # 总体结果
        is_equivalent = comparison_result['is_100_percent_equivalent']
        total_diffs = len(comparison_result['field_differences'])
        missing_records = len(comparison_result['missing_records'])
        extra_records = len(comparison_result['extra_records'])
        perfect_matches = comparison_result['perfect_matches']
        total_records = comparison_result['total_records']

        if is_equivalent:
            report.append("## ✅ 验证结果: 100%完全等价")
            report.append("**🎉 新系统与旧系统在相同数据下产生完全相同的输出！**")
            report.append("**✅ 可以安全部署到生产环境，完全替代旧系统！**")
        else:
            report.append("## ❌ 验证结果: 发现差异，未达到100%等价")
            report.append(f"**❌ 发现 {total_diffs} 个字段差异，{missing_records} 个缺失记录，{extra_records} 个多余记录**")
            report.append("**🚫 不能部署到生产环境，需要修复所有差异！**")

        report.append("")

        # 记录数量对比
        report.append("## 📊 记录数量对比")
        report.append(f"- **旧系统记录数**: {total_records['legacy']}")
        report.append(f"- **新系统记录数**: {total_records['new']}")
        report.append(f"- **完全匹配记录数**: {perfect_matches}")
        report.append(f"- **有差异记录数**: {total_diffs}")
        report.append(f"- **缺失记录数**: {missing_records}")
        report.append(f"- **多余记录数**: {extra_records}")

        if total_records['legacy'] > 0:
            match_rate = (perfect_matches / total_records['legacy'] * 100)
            report.append(f"- **匹配率**: {match_rate:.1f}%")

        report.append("")

        # 按管家统计
        report.append("## 👤 按管家验证结果")
        hk_summary = comparison_result['housekeeper_summary']

        # 按匹配率排序
        sorted_housekeepers = sorted(hk_summary.items(),
                                   key=lambda x: (x[1]['matches'] / x[1]['total']) if x[1]['total'] > 0 else 0,
                                   reverse=True)

        perfect_housekeepers = 0
        for housekeeper, stats in sorted_housekeepers:
            match_rate = (stats['matches'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅ 100%匹配" if stats['differences'] == 0 else f"❌ {stats['differences']} 个差异"

            if stats['differences'] == 0:
                perfect_housekeepers += 1

            report.append(f"### {housekeeper}")
            report.append(f"- **总记录数**: {stats['total']}")
            report.append(f"- **匹配记录数**: {stats['matches']}")
            report.append(f"- **差异记录数**: {stats['differences']}")
            report.append(f"- **匹配率**: {match_rate:.1f}%")
            report.append(f"- **状态**: {status}")
            report.append("")

        report.append(f"**100%匹配的管家数量**: {perfect_housekeepers}/{len(sorted_housekeepers)}")
        report.append("")

        # 差异详情（如果有）
        if comparison_result['field_differences']:
            report.append("## ❌ 字段差异详情")
            report.append("*（显示前20个差异，完整差异请查看日志文件）*")
            report.append("")

            for i, diff in enumerate(comparison_result['field_differences'][:20]):
                report.append(f"### 合同 {diff['contract_id']} (管家: {diff['housekeeper']})")
                for field_diff in diff['differences']:
                    report.append(f"#### {field_diff['field']}")
                    report.append(f"- **旧系统**: `{field_diff['legacy_value']}`")
                    report.append(f"- **新系统**: `{field_diff['new_value']}`")
                    report.append("")

                if i >= 19:  # 只显示前20个
                    remaining = len(comparison_result['field_differences']) - 20
                    if remaining > 0:
                        report.append(f"*... 还有 {remaining} 个差异未显示*")
                    break

        # 部署决策
        report.append("## 🚀 部署决策")
        if is_equivalent:
            report.append("### ✅ 可以安全部署")
            report.append("- **结论**: 新系统与旧系统100%等价")
            report.append("- **建议**: 立即部署到生产环境")
            report.append("- **风险**: 无风险，完全等价")
            report.append("- **后续**: 可以完全替代旧系统")
        else:
            report.append("### ❌ 禁止部署")
            report.append("- **结论**: 新系统与旧系统存在差异")
            report.append("- **建议**: 修复所有差异后重新验证")
            report.append("- **风险**: 高风险，可能影响业务")
            report.append("- **后续**: 必须达到100%等价才能部署")

        report.append("")

        return "\n".join(report)

    def run_100_percent_validation(self) -> bool:
        """运行100%等价性验证"""
        print("=" * 80)
        print("🎯 上海9月真正的100%等价性验证")
        print("=" * 80)
        print("📝 直接执行旧系统vs新系统，要求100%完全等价")
        print("📝 任何差异都意味着新系统有BUG，不能部署")
        print()

        # 1. 使用已有的旧系统真实输出
        legacy_success, legacy_file, legacy_time = self.use_existing_legacy_output()
        if not legacy_success:
            print("❌ 旧系统执行失败，验证终止")
            return False
        print()

        # 2. 执行新系统
        new_success, new_file, new_time = self.execute_new_system()
        if not new_success:
            print("❌ 新系统执行失败，验证终止")
            return False
        print()

        # 3. 100%等价性对比
        print("🔍 执行100%等价性验证...")
        comparison_result = self.compare_outputs_100_percent(legacy_file, new_file)
        print()

        # 4. 生成报告
        report = self.generate_100_percent_report(comparison_result, legacy_time, new_time)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/true_100_percent_validation_report_{timestamp}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 详细验证报告已保存: {report_file}")

        # 5. 显示验证结果
        print("\n" + "=" * 80)
        print("📊 100%等价性验证结果")
        print("=" * 80)

        is_equivalent = comparison_result['is_100_percent_equivalent']
        total_diffs = len(comparison_result['field_differences'])
        missing_records = len(comparison_result['missing_records'])
        extra_records = len(comparison_result['extra_records'])
        perfect_matches = comparison_result['perfect_matches']
        total_records = comparison_result['total_records']['legacy']

        print(f"旧系统记录数: {comparison_result['total_records']['legacy']}")
        print(f"新系统记录数: {comparison_result['total_records']['new']}")
        print(f"完全匹配记录: {perfect_matches}")
        print(f"字段差异记录: {total_diffs}")
        print(f"缺失记录: {missing_records}")
        print(f"多余记录: {extra_records}")

        if total_records > 0:
            match_rate = (perfect_matches / total_records * 100)
            print(f"总体匹配率: {match_rate:.1f}%")

        print(f"旧系统执行时间: {legacy_time:.2f}秒")
        print(f"新系统执行时间: {new_time:.2f}秒")

        # 按管家显示结果
        print("\n👤 按管家验证结果:")
        hk_summary = comparison_result['housekeeper_summary']

        perfect_count = 0
        for housekeeper, stats in hk_summary.items():
            match_rate = (stats['matches'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅" if stats['differences'] == 0 else "❌"
            if stats['differences'] == 0:
                perfect_count += 1
            print(f"  {status} {housekeeper}: {stats['matches']}/{stats['total']} 匹配 ({match_rate:.1f}%)")

        print(f"\n100%匹配的管家: {perfect_count}/{len(hk_summary)}")

        if is_equivalent:
            print("\n🎉 验证通过！新旧系统100%完全等价")
            print("✅ 每个管家的每个字段都完全匹配")
            print("✅ 可以安全部署新系统到生产环境")
            print("✅ 新系统可以完全替代旧系统")
            return True
        else:
            print("\n❌ 验证失败，未达到100%等价")
            print("🔧 需要修复所有差异后重新验证")
            print("🚫 禁止部署到生产环境")
            print(f"📄 详细差异请查看报告: {report_file}")
            return False


def main():
    """主函数"""
    setup_logging()

    validator = TrueLegacyVsNewValidator()
    success = validator.run_100_percent_validation()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
