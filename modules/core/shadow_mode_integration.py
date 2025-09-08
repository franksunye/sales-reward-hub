"""
销售激励系统重构 - 影子模式集成
版本: v1.0
创建日期: 2025-01-08

影子模式：新旧系统并行运行，对比验证，确保安全迁移。
"""

import logging
import time
import json
import traceback
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# 导入新系统
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core.beijing_jobs import (
    signing_and_sales_incentive_jun_beijing_v2,
    signing_and_sales_incentive_sep_beijing_v2
)
from modules.core.shanghai_jobs import (
    signing_and_sales_incentive_apr_shanghai_v2,
    signing_and_sales_incentive_sep_shanghai_v2
)
from modules.core.production_config import production_metrics


class ShadowModeValidator:
    """影子模式验证器"""
    
    def __init__(self):
        self.tolerance = 0.01  # 数值比较容差
        self.comparison_log = []
    
    def compare_results(self, old_result: List[Dict], new_result: List[Dict], 
                       job_name: str) -> Dict[str, Any]:
        """对比新旧系统结果"""
        comparison = {
            'job_name': job_name,
            'timestamp': datetime.now().isoformat(),
            'old_count': len(old_result) if old_result else 0,
            'new_count': len(new_result) if new_result else 0,
            'is_equivalent': True,
            'differences': [],
            'summary': {}
        }
        
        try:
            # 记录数量对比
            if comparison['old_count'] != comparison['new_count']:
                diff = f"记录数量不一致: 旧系统{comparison['old_count']}条 vs 新系统{comparison['new_count']}条"
                comparison['differences'].append(diff)
                comparison['is_equivalent'] = False
                logging.warning(f"[影子模式] {job_name}: {diff}")
            
            # 详细字段对比（如果记录数量一致）
            if comparison['old_count'] == comparison['new_count'] and old_result and new_result:
                field_differences = self._compare_fields(old_result, new_result)
                comparison['differences'].extend(field_differences)
                if field_differences:
                    comparison['is_equivalent'] = False
            
            # 生成摘要
            comparison['summary'] = {
                'equivalent_records': comparison['old_count'] if comparison['is_equivalent'] else 0,
                'total_differences': len(comparison['differences']),
                'equivalence_rate': 1.0 if comparison['is_equivalent'] else 0.0
            }
            
            # 记录结果
            status = "✅ 等价" if comparison['is_equivalent'] else "❌ 不等价"
            logging.info(f"[影子模式] {job_name}: {status}, 旧系统{comparison['old_count']}条, 新系统{comparison['new_count']}条")
            
            if not comparison['is_equivalent']:
                logging.warning(f"[影子模式] {job_name}: 发现{len(comparison['differences'])}个差异")
                for diff in comparison['differences'][:3]:  # 只记录前3个差异
                    logging.warning(f"[影子模式] {job_name}: {diff}")
        
        except Exception as e:
            comparison['error'] = str(e)
            comparison['is_equivalent'] = False
            logging.error(f"[影子模式] {job_name}: 对比过程出错 - {e}")
        
        self.comparison_log.append(comparison)
        return comparison
    
    def _compare_fields(self, old_result: List[Dict], new_result: List[Dict]) -> List[str]:
        """详细字段对比"""
        differences = []
        
        # 关键字段列表
        key_fields = [
            '合同ID(_id)', '管家(serviceHousekeeper)', '合同金额(adjustRefundMoney)',
            '管家累计单数', '管家累计金额', '计入业绩金额', '奖励类型', '奖励名称'
        ]
        
        for i, (old_record, new_record) in enumerate(zip(old_result, new_result)):
            for field in key_fields:
                if field in old_record and field in new_record:
                    old_val = old_record[field]
                    new_val = new_record[field]
                    
                    if not self._values_equivalent(old_val, new_val, field):
                        diff = f"记录{i+1} {field}: '{old_val}' vs '{new_val}'"
                        differences.append(diff)
                elif field in old_record or field in new_record:
                    diff = f"记录{i+1} {field}: 字段缺失"
                    differences.append(diff)
        
        return differences
    
    def _values_equivalent(self, old_val: Any, new_val: Any, field_name: str) -> bool:
        """判断两个值是否等价"""
        # 数值字段使用容差比较
        if field_name in ['管家累计金额', '计入业绩金额', '合同金额(adjustRefundMoney)']:
            try:
                old_float = float(old_val) if old_val else 0.0
                new_float = float(new_val) if new_val else 0.0
                return abs(old_float - new_float) <= self.tolerance
            except (ValueError, TypeError):
                return str(old_val).strip() == str(new_val).strip()
        
        # 字符串字段精确比较
        return str(old_val).strip() == str(new_val).strip()
    
    def get_summary_report(self) -> Dict[str, Any]:
        """获取汇总报告"""
        if not self.comparison_log:
            return {'status': 'no_data'}
        
        total_comparisons = len(self.comparison_log)
        equivalent_comparisons = len([c for c in self.comparison_log if c['is_equivalent']])
        
        return {
            'total_comparisons': total_comparisons,
            'equivalent_comparisons': equivalent_comparisons,
            'equivalence_rate': equivalent_comparisons / total_comparisons,
            'total_differences': sum(len(c['differences']) for c in self.comparison_log),
            'last_comparison': self.comparison_log[-1]['timestamp'] if self.comparison_log else None,
            'status': 'healthy' if equivalent_comparisons / total_comparisons >= 0.95 else 'warning'
        }


# 全局验证器实例
shadow_validator = ShadowModeValidator()


def shadow_mode_wrapper(new_function, old_function, job_name: str):
    """影子模式包装器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        old_result = None
        new_result = None
        success = True
        
        try:
            # 运行旧系统（主要业务逻辑）
            logging.info(f"[影子模式] {job_name}: 开始运行旧系统")
            old_start = time.time()
            old_result = old_function(*args, **kwargs)
            old_time = time.time() - old_start
            logging.info(f"[影子模式] {job_name}: 旧系统完成，耗时{old_time:.2f}s，{len(old_result) if old_result else 0}条记录")
            
        except Exception as e:
            logging.error(f"[影子模式] {job_name}: 旧系统执行失败 - {e}")
            success = False
            raise  # 旧系统失败需要抛出异常
        
        try:
            # 运行新系统（影子验证）
            logging.info(f"[影子模式] {job_name}: 开始运行新系统")
            new_start = time.time()
            new_result = new_function(*args, **kwargs)
            new_time = time.time() - new_start
            
            # 转换新系统结果格式
            if new_result and hasattr(new_result[0], 'to_dict'):
                new_result = [record.to_dict() for record in new_result]
            
            logging.info(f"[影子模式] {job_name}: 新系统完成，耗时{new_time:.2f}s，{len(new_result) if new_result else 0}条记录")
            
            # 对比结果
            comparison = shadow_validator.compare_results(old_result, new_result, job_name)
            
            # 记录性能对比
            performance_improvement = ((old_time - new_time) / old_time * 100) if old_time > 0 else 0
            logging.info(f"[影子模式] {job_name}: 性能对比 - 旧系统{old_time:.2f}s vs 新系统{new_time:.2f}s (改善{performance_improvement:.1f}%)")
            
        except Exception as e:
            logging.error(f"[影子模式] {job_name}: 新系统执行失败 - {e}")
            logging.error(f"[影子模式] {job_name}: 新系统错误详情 - {traceback.format_exc()}")
            # 新系统失败不影响业务，只记录日志
        
        # 记录指标
        total_time = time.time() - start_time
        record_count = len(old_result) if old_result else 0
        production_metrics.record_processing(total_time, record_count, success)
        
        # 返回旧系统结果（保证业务连续性）
        return old_result
    
    return wrapper


# 影子模式Job函数定义

def shadow_signing_and_sales_incentive_jun_beijing(old_function):
    """北京6月影子模式Job函数"""
    return shadow_mode_wrapper(
        signing_and_sales_incentive_jun_beijing_v2,
        old_function,
        "北京6月销售激励"
    )


def shadow_signing_and_sales_incentive_sep_beijing(old_function):
    """北京9月影子模式Job函数"""
    return shadow_mode_wrapper(
        signing_and_sales_incentive_sep_beijing_v2,
        old_function,
        "北京9月销售激励"
    )


def shadow_signing_and_sales_incentive_apr_shanghai(old_function):
    """上海4月影子模式Job函数"""
    return shadow_mode_wrapper(
        signing_and_sales_incentive_apr_shanghai_v2,
        old_function,
        "上海4月销售激励"
    )


def shadow_signing_and_sales_incentive_sep_shanghai(old_function):
    """上海9月影子模式Job函数"""
    return shadow_mode_wrapper(
        signing_and_sales_incentive_sep_shanghai_v2,
        old_function,
        "上海9月销售激励"
    )


def generate_shadow_mode_report() -> str:
    """生成影子模式报告"""
    report = shadow_validator.get_summary_report()
    
    if report.get('status') == 'no_data':
        return "影子模式报告：暂无数据"
    
    report_text = f"""
影子模式运行报告
================
报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

总体统计:
- 总对比次数: {report['total_comparisons']}
- 等价对比次数: {report['equivalent_comparisons']}
- 等价率: {report['equivalence_rate']:.1%}
- 总差异数: {report['total_differences']}
- 状态: {report['status']}

性能统计:
{production_metrics.get_summary()}

建议:
"""
    
    if report['equivalence_rate'] >= 0.95:
        report_text += "✅ 新系统表现优秀，建议考虑正式迁移"
    elif report['equivalence_rate'] >= 0.8:
        report_text += "⚠️ 新系统基本稳定，建议继续观察并修复差异"
    else:
        report_text += "❌ 新系统存在较多问题，建议暂停迁移并深入调查"
    
    return report_text


if __name__ == "__main__":
    # 测试影子模式
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("影子模式集成模块测试")
    print("="*50)
    
    # 模拟测试
    def mock_old_function():
        return [{'test': 'old_result'}]
    
    def mock_new_function():
        return [{'test': 'new_result'}]
    
    # 测试包装器
    wrapped_function = shadow_mode_wrapper(mock_new_function, mock_old_function, "测试Job")
    result = wrapped_function()
    
    print(f"测试结果: {result}")
    print(generate_shadow_mode_report())
    print("="*50)
    print("影子模式集成模块就绪！")
