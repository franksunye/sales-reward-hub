#!/usr/bin/env python3
"""
全面等价性验证工具

这是最严格的等价性验证工具，确保新旧架构100%等价。

验证流程：
1. 清理环境，确保干净状态
2. 使用旧架构获取基线数据
3. 使用新架构处理相同数据
4. 逐字段对比所有输出
5. 分析差异并生成详细报告

使用方法:
    python scripts/comprehensive_equivalence_validator.py --city beijing --month sep
    python scripts/comprehensive_equivalence_validator.py --city shanghai --month sep
    python scripts/comprehensive_equivalence_validator.py --all
"""

import sys
import os
import csv
import json
import logging
import sqlite3
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class ComprehensiveEquivalenceValidator:
    """全面等价性验证器"""
    
    def __init__(self, city: str, month: str):
        # 标准化城市和月份代码
        city_map = {"beijing": "BJ", "shanghai": "SH", "bj": "BJ", "sh": "SH"}
        month_map = {"sep": "SEP", "september": "SEP", "aug": "AUG", "august": "AUG"}

        self.city = city_map.get(city.lower(), city.upper())
        self.month = month_map.get(month.lower(), month.upper())
        self.activity_code = f"{self.city}-{self.month}"
        
        self.project_root = Path(project_root)
        self.baseline_dir = self.project_root / "baseline" / self.activity_code
        self.reports_dir = self.project_root / "reports"
        
        # 确保目录存在
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.validation_result = {
            'timestamp': datetime.now().isoformat(),
            'activity_code': self.activity_code,
            'environment_clean': False,
            'baseline_generated': False,
            'new_system_executed': False,
            'comparison_completed': False,
            'is_equivalent': False,
            'total_records': {'baseline': 0, 'new': 0},
            'perfect_matches': 0,
            'field_differences': [],
            'missing_records': [],
            'extra_records': [],
            'performance_comparison': {},
            'recommendations': []
        }
        
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.reports_dir / f"validation_{self.activity_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def validate_full_equivalence(self) -> bool:
        """执行完整的等价性验证"""
        self.logger.info(f"🚀 开始 {self.activity_code} 全面等价性验证")
        
        try:
            # 步骤1：环境清理
            if not self._clean_environment():
                return False
            
            # 步骤2：生成基线数据
            if not self._generate_baseline():
                return False
            
            # 步骤3：执行新系统
            if not self._execute_new_system():
                return False
            
            # 步骤4：对比数据
            if not self._compare_outputs():
                return False
            
            # 步骤5：生成报告
            self._generate_final_report()
            
            return self.validation_result['is_equivalent']
            
        except Exception as e:
            self.logger.error(f"❌ 验证过程失败: {e}")
            return False
    
    def _clean_environment(self) -> bool:
        """清理验证环境"""
        self.logger.info("🧹 清理验证环境...")
        
        try:
            # 清理数据库
            db_path = self.project_root / "performance_data.db"
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # 删除相关活动的数据
                cursor.execute("DELETE FROM performance_records WHERE activity_code = ?", (self.activity_code,))
                cursor.execute("DELETE FROM notification_queue WHERE activity_code = ?", (self.activity_code,))
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"✅ 数据库清理完成: {self.activity_code}")
            
            # 清理临时文件
            temp_patterns = [
                f"performance_data_{self.activity_code}_*.csv",
                f"ContractData-{self.city}-{self.month}.csv",
                f"PerformanceData-{self.city}-{self.month}.csv"
            ]
            
            for pattern in temp_patterns:
                for file_path in self.project_root.glob(pattern):
                    file_path.unlink()
                    self.logger.info(f"删除临时文件: {file_path}")
            
            self.validation_result['environment_clean'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 环境清理失败: {e}")
            return False
    
    def _generate_baseline(self) -> bool:
        """使用旧架构生成基线数据"""
        self.logger.info("📊 使用旧架构生成基线数据...")
        
        try:
            # 导入旧架构函数
            if self.city == "BJ" and self.month == "SEP":
                from jobs import signing_and_sales_incentive_sep_beijing as old_function
            elif self.city == "SH" and self.month == "SEP":
                from jobs import signing_and_sales_incentive_sep_shanghai as old_function
            else:
                self.logger.error(f"❌ 不支持的活动: {self.activity_code}")
                return False
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 执行旧架构
            self.logger.info("执行旧架构函数...")
            old_function()
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            self.validation_result['performance_comparison']['baseline_time'] = execution_time
            
            # 查找生成的CSV文件
            baseline_csv = self._find_generated_csv("baseline")
            if not baseline_csv:
                self.logger.error("❌ 未找到旧架构生成的CSV文件")
                return False
            
            # 移动到baseline目录
            baseline_target = self.baseline_dir / f"performance_data_{self.activity_code}_baseline.csv"
            baseline_csv.rename(baseline_target)
            
            # 统计记录数
            with open(baseline_target, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # 跳过标题行
                record_count = sum(1 for _ in reader)
            
            self.validation_result['total_records']['baseline'] = record_count
            self.validation_result['baseline_generated'] = True
            
            self.logger.info(f"✅ 基线数据生成完成: {record_count} 条记录, 耗时 {execution_time:.2f} 秒")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 基线数据生成失败: {e}")
            return False
    
    def _execute_new_system(self) -> bool:
        """执行新架构系统"""
        self.logger.info("🆕 执行新架构系统...")
        
        try:
            # 导入新架构函数
            if self.city == "BJ" and self.month == "SEP":
                from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2 as new_function
            elif self.city == "SH" and self.month == "SEP":
                from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2 as new_function
            else:
                self.logger.error(f"❌ 不支持的活动: {self.activity_code}")
                return False
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 执行新架构
            self.logger.info("执行新架构函数...")
            records = new_function()
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            self.validation_result['performance_comparison']['new_time'] = execution_time
            
            # 查找生成的CSV文件
            new_csv = self._find_generated_csv("new")
            if not new_csv:
                self.logger.error("❌ 未找到新架构生成的CSV文件")
                return False
            
            # 移动到reports目录
            new_target = self.reports_dir / f"performance_data_{self.activity_code}_new.csv"
            new_csv.rename(new_target)
            
            # 统计记录数
            self.validation_result['total_records']['new'] = len(records)
            self.validation_result['new_system_executed'] = True
            
            self.logger.info(f"✅ 新系统执行完成: {len(records)} 条记录, 耗时 {execution_time:.2f} 秒")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 新系统执行失败: {e}")
            return False
    
    def _find_generated_csv(self, system_type: str) -> Optional[Path]:
        """查找生成的CSV文件"""
        patterns = [
            f"performance_data_{self.activity_code}_*.csv",
            f"performance_data_*{self.city}*{self.month}*.csv",
            f"PerformanceData-{self.city}-{self.month}.csv"
        ]
        
        for pattern in patterns:
            files = list(self.project_root.glob(pattern))
            if files:
                # 返回最新的文件
                return max(files, key=lambda f: f.stat().st_mtime)
        
        return None
    
    def _compare_outputs(self) -> bool:
        """对比输出数据"""
        self.logger.info("⚖️  对比输出数据...")
        
        try:
            baseline_file = self.baseline_dir / f"performance_data_{self.activity_code}_baseline.csv"
            new_file = self.reports_dir / f"performance_data_{self.activity_code}_new.csv"
            
            if not baseline_file.exists() or not new_file.exists():
                self.logger.error("❌ 缺少对比文件")
                return False
            
            # 读取数据
            baseline_data = self._read_csv_data(baseline_file)
            new_data = self._read_csv_data(new_file)
            
            # 创建索引
            baseline_index = {row['合同ID(_id)']: row for row in baseline_data}
            new_index = {row['合同ID(_id)']: row for row in new_data}
            
            # 对比记录
            all_contract_ids = set(baseline_index.keys()) | set(new_index.keys())
            
            for contract_id in all_contract_ids:
                baseline_record = baseline_index.get(contract_id)
                new_record = new_index.get(contract_id)
                
                if not baseline_record:
                    self.validation_result['extra_records'].append(contract_id)
                elif not new_record:
                    self.validation_result['missing_records'].append(contract_id)
                else:
                    # 逐字段对比
                    differences = self._compare_records(contract_id, baseline_record, new_record)
                    if not differences:
                        self.validation_result['perfect_matches'] += 1
                    else:
                        self.validation_result['field_differences'].append({
                            'contract_id': contract_id,
                            'differences': differences
                        })
            
            # 计算等价性
            total_records = len(all_contract_ids)
            perfect_matches = self.validation_result['perfect_matches']
            
            if (perfect_matches == total_records and 
                not self.validation_result['missing_records'] and 
                not self.validation_result['extra_records']):
                self.validation_result['is_equivalent'] = True
            
            self.validation_result['comparison_completed'] = True
            
            self.logger.info(f"✅ 数据对比完成: {perfect_matches}/{total_records} 完全匹配")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据对比失败: {e}")
            return False
    
    def _read_csv_data(self, file_path: Path) -> List[Dict]:
        """读取CSV数据"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def _compare_records(self, contract_id: str, baseline: Dict, new: Dict) -> List[Dict]:
        """对比单条记录"""
        differences = []
        
        # 获取所有字段
        all_fields = set(baseline.keys()) | set(new.keys())
        
        for field in all_fields:
            baseline_value = baseline.get(field, '')
            new_value = new.get(field, '')
            
            # 标准化值进行比较
            if self._normalize_value(baseline_value) != self._normalize_value(new_value):
                differences.append({
                    'field': field,
                    'baseline_value': baseline_value,
                    'new_value': new_value
                })
        
        return differences
    
    def _normalize_value(self, value: Any) -> str:
        """标准化值用于比较"""
        if value is None:
            return ''
        return str(value).strip()
    
    def _generate_final_report(self):
        """生成最终报告"""
        self.logger.info("📄 生成最终验证报告...")
        
        report_file = self.reports_dir / f"equivalence_validation_{self.activity_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self._format_report())
        
        self.logger.info(f"📄 报告已保存到: {report_file}")
    
    def _format_report(self) -> str:
        """格式化报告"""
        lines = []
        
        lines.append(f"# {self.activity_code} 全面等价性验证报告")
        lines.append("")
        lines.append(f"**验证时间**: {self.validation_result['timestamp']}")
        lines.append(f"**活动代码**: {self.activity_code}")
        lines.append("")
        
        # 验证结果
        if self.validation_result['is_equivalent']:
            lines.append("## ✅ 验证结果：100%完全等价")
        else:
            lines.append("## ❌ 验证结果：发现差异")
        
        lines.append("")
        
        # 统计信息
        lines.append("## 📊 统计信息")
        lines.append(f"- **基线记录数**: {self.validation_result['total_records']['baseline']}")
        lines.append(f"- **新系统记录数**: {self.validation_result['total_records']['new']}")
        lines.append(f"- **完全匹配记录**: {self.validation_result['perfect_matches']}")
        lines.append(f"- **字段差异记录**: {len(self.validation_result['field_differences'])}")
        lines.append(f"- **缺失记录**: {len(self.validation_result['missing_records'])}")
        lines.append(f"- **额外记录**: {len(self.validation_result['extra_records'])}")
        lines.append("")
        
        # 性能对比
        if self.validation_result['performance_comparison']:
            lines.append("## ⚡ 性能对比")
            baseline_time = self.validation_result['performance_comparison'].get('baseline_time', 0)
            new_time = self.validation_result['performance_comparison'].get('new_time', 0)
            lines.append(f"- **旧架构执行时间**: {baseline_time:.2f} 秒")
            lines.append(f"- **新架构执行时间**: {new_time:.2f} 秒")
            if baseline_time > 0:
                improvement = ((baseline_time - new_time) / baseline_time) * 100
                lines.append(f"- **性能改进**: {improvement:.1f}%")
            lines.append("")
        
        # 差异详情
        if self.validation_result['field_differences']:
            lines.append("## 🔍 差异详情")
            for diff in self.validation_result['field_differences'][:10]:  # 只显示前10个
                lines.append(f"### 合同 {diff['contract_id']}")
                for field_diff in diff['differences']:
                    lines.append(f"- **{field_diff['field']}**: `{field_diff['baseline_value']}` → `{field_diff['new_value']}`")
                lines.append("")
        
        return "\n".join(lines)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='全面等价性验证工具')
    parser.add_argument('--city', choices=['beijing', 'shanghai'], help='城市')
    parser.add_argument('--month', choices=['sep'], help='月份')
    parser.add_argument('--all', action='store_true', help='验证所有支持的活动')
    
    args = parser.parse_args()
    
    if args.all:
        activities = [('beijing', 'sep'), ('shanghai', 'sep')]
    elif args.city and args.month:
        activities = [(args.city, args.month)]
    else:
        parser.print_help()
        return 1
    
    all_passed = True
    
    for city, month in activities:
        print(f"\n{'='*60}")
        print(f"验证 {city.upper()}-{month.upper()}")
        print(f"{'='*60}")
        
        validator = ComprehensiveEquivalenceValidator(city, month)
        passed = validator.validate_full_equivalence()
        
        if not passed:
            all_passed = False
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
