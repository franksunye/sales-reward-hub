#!/usr/bin/env python3
"""
上海9月双轨激励测试运行脚本
快速运行测试的便捷入口
"""

import sys
import os
import subprocess

def run_core_tests():
    """运行核心测试"""
    print("🚀 运行上海9月核心功能测试...")
    result = subprocess.run([
        sys.executable, "tests/test_shanghai_sep_suite.py", "--core"
    ], cwd=os.getcwd())
    return result.returncode == 0

def run_all_tests():
    """运行所有测试"""
    print("🚀 运行上海9月完整测试套件...")
    result = subprocess.run([
        sys.executable, "tests/test_shanghai_sep_suite.py"
    ], cwd=os.getcwd())
    return result.returncode == 0

def run_specific_test(test_name):
    """运行特定测试"""
    test_files = {
        "data": "tests/test_shanghai_sep_data_processing.py",
        "notification": "tests/test_shanghai_sep_notification.py",
        "self_referral": "tests/test_shanghai_sep_self_referral.py",
        "integration": "tests/test_shanghai_sep_job_integration.py"
    }
    
    if test_name not in test_files:
        print(f"❌ 未知的测试名称: {test_name}")
        print(f"可用的测试: {', '.join(test_files.keys())}")
        return False
    
    print(f"🚀 运行 {test_name} 测试...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", test_files[test_name], "-v"
    ], cwd=os.getcwd())
    return result.returncode == 0

def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 默认运行核心测试
        success = run_core_tests()
    elif sys.argv[1] == "all":
        success = run_all_tests()
    elif sys.argv[1] == "core":
        success = run_core_tests()
    elif sys.argv[1] in ["data", "notification", "self_referral", "integration"]:
        success = run_specific_test(sys.argv[1])
    else:
        print("用法:")
        print("  python run_tests.py          # 运行核心测试")
        print("  python run_tests.py core     # 运行核心测试")
        print("  python run_tests.py all      # 运行所有测试")
        print("  python run_tests.py data            # 运行核心数据处理测试")
        print("  python run_tests.py notification    # 运行通知测试")
        print("  python run_tests.py self_referral   # 运行自引单测试")
        print("  python run_tests.py integration     # 运行集成测试")
        return
    
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
