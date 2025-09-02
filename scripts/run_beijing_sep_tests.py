#!/usr/bin/env python3
"""
北京9月系统性测试执行脚本
按照功能点清单执行测试，确保测试结果 = 功能完全正确
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class BeijingSepTestRunner:
    """北京9月测试执行器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.test_dir = self.project_root / "tests"
        
        # 测试阶段定义
        self.test_phases = {
            "phase1_unit": {
                "name": "阶段1: 单元测试（功能点级别）",
                "tests": [
                    "tests/test_beijing_sep_feature_driven.py::TestF01ProjectAmountLimit",
                    "tests/test_beijing_sep_feature_driven.py::TestF02PersonalSequenceLucky",
                    "tests/test_beijing_sep_feature_driven.py::TestF03TieredRewardsNewThreshold",
                    "tests/test_beijing_sep_feature_driven.py::TestF04BadgeDisabled",
                    "tests/test_beijing_sep_feature_driven.py::TestF05ConfigDriven",
                ],
                "required": True
            },
            "phase2_integration": {
                "name": "阶段2: 集成测试（跨功能点）",
                "tests": [
                    "tests/test_beijing_sep_integration.py",
                ],
                "required": True
            },
            "phase3_regression": {
                "name": "阶段3: 回归测试（保障现有功能）",
                "tests": [
                    "tests/test_regression_baseline.py",
                ],
                "required": True
            },
            "phase4_e2e": {
                "name": "阶段4: 端到端测试（完整流程）",
                "tests": [
                    "tests/test_beijing_sep_e2e.py",
                ],
                "required": False  # 可选，因为可能尚未实现
            }
        }
    
    def run_test_phase(self, phase_id, phase_config):
        """执行单个测试阶段"""
        print(f"\n🚀 {phase_config['name']}")
        print("=" * 60)
        
        phase_results = []
        
        for test_path in phase_config["tests"]:
            print(f"\n📋 执行测试: {test_path}")
            result = self._run_pytest(test_path)
            phase_results.append({
                "test_path": test_path,
                "success": result["success"],
                "output": result["output"],
                "duration": result["duration"]
            })
            
            if result["success"]:
                print(f"✅ 测试通过: {test_path}")
            else:
                print(f"❌ 测试失败: {test_path}")
                if phase_config["required"]:
                    print(f"⚠️  必需阶段测试失败，建议修复后继续")
        
        return phase_results
    
    def _run_pytest(self, test_path):
        """执行pytest命令"""
        start_time = datetime.now()
        
        try:
            # 构建pytest命令
            cmd = [
                sys.executable, "-m", "pytest",
                test_path,
                "-v",
                "--tb=short",
                "--no-header",
                "--quiet"
            ]
            
            # 执行测试
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "duration": duration
            }
            
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "output": "测试执行超时（5分钟）",
                "duration": duration
            }
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "output": f"测试执行异常: {str(e)}",
                "duration": duration
            }
    
    def run_all_tests(self):
        """执行所有测试阶段"""
        print("🎯 开始执行北京9月系统性测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = {}
        overall_success = True
        
        for phase_id, phase_config in self.test_phases.items():
            phase_results = self.run_test_phase(phase_id, phase_config)
            all_results[phase_id] = {
                "config": phase_config,
                "results": phase_results
            }
            
            # 检查阶段是否成功
            phase_success = all(r["success"] for r in phase_results)
            if not phase_success and phase_config["required"]:
                overall_success = False
        
        # 生成测试报告
        self._generate_test_report(all_results, overall_success)
        
        return overall_success
    
    def _generate_test_report(self, all_results, overall_success):
        """生成测试报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n📊 测试执行报告")
        print("=" * 60)
        print(f"执行时间: {timestamp}")
        print(f"总体结果: {'✅ 通过' if overall_success else '❌ 失败'}")
        
        # 统计信息
        total_tests = 0
        passed_tests = 0
        total_duration = 0
        
        for phase_id, phase_data in all_results.items():
            phase_config = phase_data["config"]
            phase_results = phase_data["results"]
            
            phase_total = len(phase_results)
            phase_passed = sum(1 for r in phase_results if r["success"])
            phase_duration = sum(r["duration"] for r in phase_results)
            
            total_tests += phase_total
            passed_tests += phase_passed
            total_duration += phase_duration
            
            status = "✅" if phase_passed == phase_total else "❌"
            print(f"\n{status} {phase_config['name']}")
            print(f"   通过率: {phase_passed}/{phase_total} ({(phase_passed/phase_total)*100:.1f}%)")
            print(f"   耗时: {phase_duration:.1f}秒")
            
            # 显示失败的测试
            failed_tests = [r for r in phase_results if not r["success"]]
            if failed_tests:
                print(f"   失败测试:")
                for failed_test in failed_tests:
                    print(f"     - {failed_test['test_path']}")
        
        print(f"\n📈 总体统计:")
        print(f"   测试总数: {total_tests}")
        print(f"   通过数量: {passed_tests}")
        print(f"   通过率: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   总耗时: {total_duration:.1f}秒")
        
        # 质量门禁检查
        print(f"\n🚪 质量门禁检查:")
        if overall_success:
            print("✅ 所有必需测试通过，可以继续开发")
        else:
            print("❌ 存在测试失败，建议修复后再继续")
            print("💡 建议:")
            print("   1. 查看失败测试的详细输出")
            print("   2. 修复相关功能实现")
            print("   3. 重新运行测试")
    
    def run_specific_feature(self, feature_id):
        """执行特定功能点的测试"""
        test_path = f"tests/test_beijing_sep_feature_driven.py::TestF{feature_id.upper()}"
        
        print(f"🎯 执行功能点 {feature_id} 的测试")
        result = self._run_pytest(test_path)
        
        if result["success"]:
            print(f"✅ 功能点 {feature_id} 测试通过")
        else:
            print(f"❌ 功能点 {feature_id} 测试失败")
            print(f"输出:\n{result['output']}")
        
        return result["success"]


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="北京9月系统性测试执行器")
    parser.add_argument("--feature", help="执行特定功能点测试 (如: 01, 02, 03...)")
    parser.add_argument("--phase", help="执行特定阶段测试 (如: phase1_unit, phase2_integration...)")
    parser.add_argument("--all", action="store_true", help="执行所有测试阶段")
    
    args = parser.parse_args()
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    runner = BeijingSepTestRunner(project_root)
    
    if args.feature:
        # 执行特定功能点测试
        success = runner.run_specific_feature(args.feature)
        sys.exit(0 if success else 1)
    
    elif args.phase:
        # 执行特定阶段测试
        if args.phase in runner.test_phases:
            phase_config = runner.test_phases[args.phase]
            results = runner.run_test_phase(args.phase, phase_config)
            success = all(r["success"] for r in results)
            sys.exit(0 if success else 1)
        else:
            print(f"❌ 未知测试阶段: {args.phase}")
            print(f"可用阶段: {', '.join(runner.test_phases.keys())}")
            sys.exit(1)
    
    elif args.all:
        # 执行所有测试
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    
    else:
        # 默认执行所有测试
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
