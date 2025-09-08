"""
销售激励系统重构 - 轻量化性能基准测试
版本: v1.0
创建日期: 2025-01-08

注意：性能不是重点！数据量小，此测试仅作为参考
重点：功能正确性，性能测试只是为了确认没有明显的性能退化
"""

import time
import tempfile
import os
import sys
import statistics
from typing import List, Dict, Tuple

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline


class LightweightPerformanceReference:
    """轻量化性能基准测试 - 仅作参考，不是重点"""
    
    def __init__(self):
        self.results = []
    
    def create_sample_data(self, count: int = 10) -> List[Dict]:
        """创建样本数据（小数据量）"""
        sample_data = []
        
        for i in range(count):
            sample_data.append({
                '合同ID(_id)': f'2025010812345{i:03d}',
                '管家(serviceHousekeeper)': f'测试管家{i%3+1}',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 10000 + (i * 1000),
                '支付金额(paidAmount)': 8000 + (i * 800),
                '款项来源类型(tradeIn)': i % 2,
                '管家ID(serviceHousekeeperId)': f'TEST{i:03d}',
                '活动城市(province)': '北京' if i % 2 == 0 else '上海',
                'Status': '已签约',
                '创建时间(createTime)': f'2025-01-08 {10+i%12:02d}:00:00'
            })
        
        return sample_data
    
    def measure_processing_time(self, config_key: str, activity_code: str, 
                              data: List[Dict], runs: int = 3) -> Dict[str, float]:
        """测量处理时间（多次运行取平均值）"""
        times = []
        
        for run in range(runs):
            # 创建临时数据库
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
                temp_db.close()
                
                try:
                    start_time = time.time()
                    
                    # 创建处理管道
                    pipeline, config, store = create_standard_pipeline(
                        config_key=config_key,
                        activity_code=activity_code,
                        city=config_key.split('-')[0],
                        db_path=temp_db.name,
                        enable_project_limit=(config_key.startswith('BJ')),
                        enable_dual_track=(config_key == 'SH-2025-09')
                    )
                    
                    # 处理数据
                    processed_records = pipeline.process(data)
                    
                    end_time = time.time()
                    processing_time = end_time - start_time
                    times.append(processing_time)
                    
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_db.name):
                        os.unlink(temp_db.name)
        
        return {
            'average_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
            'runs': runs,
            'records_processed': len(data)
        }
    
    def run_performance_reference(self) -> Dict[str, Dict]:
        """运行性能基准测试（轻量化）"""
        print("运行轻量化性能基准测试...")
        print("注意：性能不是重点，此测试仅作参考")
        print("-" * 50)
        
        # 测试配置
        test_configs = [
            ('BJ-2025-06', 'BJ-JUN', '北京6月'),
            ('BJ-2025-09', 'BJ-SEP', '北京9月'),
            ('SH-2025-09', 'SH-SEP', '上海9月')
        ]
        
        # 测试数据量（小数据量）
        data_sizes = [5, 10, 20]  # 小数据量，符合实际使用场景
        
        results = {}
        
        for config_key, activity_code, name in test_configs:
            print(f"\n测试 {name} ({config_key}):")
            results[config_key] = {}
            
            for size in data_sizes:
                print(f"  数据量: {size} 条记录")
                
                # 创建测试数据
                test_data = self.create_sample_data(size)
                
                # 测量处理时间
                timing_result = self.measure_processing_time(
                    config_key, activity_code, test_data, runs=3
                )
                
                results[config_key][size] = timing_result
                
                # 输出结果
                avg_time = timing_result['average_time']
                per_record = avg_time / size * 1000  # 毫秒/记录
                
                print(f"    平均处理时间: {avg_time:.3f}秒")
                print(f"    每条记录: {per_record:.1f}毫秒")
                print(f"    标准差: {timing_result['std_dev']:.3f}秒")
        
        return results
    
    def generate_performance_report(self, results: Dict[str, Dict]) -> str:
        """生成性能基准报告"""
        report = f"""
轻量化性能基准测试报告
====================
测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
重要说明: 性能不是重点！数据量小，此报告仅作参考

测试环境:
- 数据量: 5, 10, 20 条记录（符合实际小数据量场景）
- 运行次数: 每个测试3次取平均值
- 存储: SQLite临时数据库

性能基准结果:
"""
        
        for config_key, config_results in results.items():
            report += f"\n{config_key}:\n"
            
            for size, timing in config_results.items():
                avg_time = timing['average_time']
                per_record = avg_time / size * 1000
                
                report += f"  {size}条记录: {avg_time:.3f}秒 ({per_record:.1f}毫秒/记录)\n"
        
        # 性能评估
        report += "\n性能评估:\n"
        
        # 计算总体平均性能
        all_per_record_times = []
        for config_results in results.values():
            for size, timing in config_results.items():
                per_record = timing['average_time'] / size * 1000
                all_per_record_times.append(per_record)
        
        if all_per_record_times:
            avg_per_record = statistics.mean(all_per_record_times)
            report += f"- 平均处理速度: {avg_per_record:.1f}毫秒/记录\n"
            
            if avg_per_record < 10:
                report += "- ✅ 性能优秀（<10毫秒/记录）\n"
            elif avg_per_record < 50:
                report += "- ✅ 性能良好（<50毫秒/记录）\n"
            elif avg_per_record < 100:
                report += "- ⚠️ 性能一般（<100毫秒/记录）\n"
            else:
                report += "- ❌ 性能较慢（>100毫秒/记录）\n"
        
        report += """
重要提醒:
- 本项目数据量很小，性能不是重点关注项
- 功能正确性是首要目标
- 此性能测试仅作为参考，不作为评估标准
- 实际生产环境性能可能因环境差异而不同
"""
        
        return report
    
    def run_comparison_with_csv_simulation(self) -> str:
        """模拟与CSV处理的性能对比（仅作参考）"""
        print("\n模拟CSV vs SQLite性能对比...")
        print("注意：这只是理论对比，不是重点")
        
        # 模拟CSV处理时间（基于文件I/O开销）
        csv_simulation = {
            5: 0.050,   # 50毫秒（文件读取开销）
            10: 0.080,  # 80毫秒
            20: 0.120   # 120毫秒
        }
        
        # 运行SQLite测试
        sqlite_results = self.run_performance_reference()
        
        comparison_report = "\nCSV vs SQLite 性能对比（模拟）:\n"
        comparison_report += "=" * 40 + "\n"
        
        for config_key, config_results in sqlite_results.items():
            comparison_report += f"\n{config_key}:\n"
            
            for size in [5, 10, 20]:
                if size in config_results:
                    sqlite_time = config_results[size]['average_time']
                    csv_time = csv_simulation[size]
                    improvement = ((csv_time - sqlite_time) / csv_time * 100)
                    
                    comparison_report += f"  {size}条记录:\n"
                    comparison_report += f"    CSV模拟: {csv_time:.3f}秒\n"
                    comparison_report += f"    SQLite: {sqlite_time:.3f}秒\n"
                    comparison_report += f"    改善: {improvement:+.1f}%\n"
        
        comparison_report += "\n注意：CSV时间为模拟值，实际对比需要真实的旧系统测试\n"
        
        return comparison_report


def main():
    """主函数"""
    print("销售激励系统重构 - 轻量化性能基准测试")
    print("重要：性能不是重点！此测试仅作参考")
    print("=" * 60)
    
    # 创建性能测试器
    perf_tester = LightweightPerformanceReference()
    
    try:
        # 运行性能基准测试
        results = perf_tester.run_performance_reference()
        
        # 生成报告
        report = perf_tester.generate_performance_report(results)
        print(report)
        
        # 保存报告
        with open('lightweight_performance_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 运行对比测试
        comparison = perf_tester.run_comparison_with_csv_simulation()
        print(comparison)
        
        print("\n📋 性能报告已保存: lightweight_performance_report.txt")
        print("\n重要提醒：")
        print("- 性能不是本项目的重点关注项")
        print("- 功能正确性是首要目标")
        print("- 此测试仅作为参考，不作为评估标准")
        
    except Exception as e:
        print(f"❌ 性能测试出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print("轻量化性能基准测试完成！")


if __name__ == "__main__":
    main()
