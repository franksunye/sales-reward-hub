"""
上海9月双轨激励测试套件
整合所有上海9月相关的测试用例
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所有上海9月相关的测试模块
from test_shanghai_sep_data_processing import TestShanghaiSepDataProcessing
from test_shanghai_sep_job_integration import TestShanghaiSepJobIntegration
from test_shanghai_sep_notification import TestShanghaiSepNotification
from test_shanghai_sep_self_referral import TestSelfReferralRewards

def create_test_suite():
    """创建上海9月测试套件"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 1. 核心数据处理测试（包含完整字段验证）
    suite.addTest(loader.loadTestsFromTestCase(TestShanghaiSepDataProcessing))

    # 2. 自引单功能测试
    suite.addTest(loader.loadTestsFromTestCase(TestSelfReferralRewards))

    # 3. 通知功能测试
    suite.addTest(loader.loadTestsFromTestCase(TestShanghaiSepNotification))

    # 4. 集成测试
    suite.addTest(loader.loadTestsFromTestCase(TestShanghaiSepJobIntegration))

    return suite

def run_all_tests():
    """运行所有上海9月测试"""
    print("=" * 60)
    print("上海9月双轨激励功能测试套件")
    print("=" * 60)
    
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)
    
    return result.wasSuccessful()

def run_core_tests():
    """只运行核心功能测试（快速验证）"""
    print("=" * 60)
    print("上海9月核心功能快速测试")
    print("=" * 60)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestShanghaiSepDataProcessing))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='上海9月测试套件')
    parser.add_argument('--core', action='store_true', help='只运行核心测试')
    args = parser.parse_args()
    
    if args.core:
        success = run_core_tests()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)
