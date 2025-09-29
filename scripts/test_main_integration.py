#!/usr/bin/env python3
"""
测试main.py中新架构10月job的整合
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_october_jobs_integration():
    """测试10月job在main.py中的整合"""
    print("🧪 测试main.py中10月job的整合...")

    try:
        # 直接测试导入是否成功
        import main

        # 检查是否能找到10月job函数
        from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai
        from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing

        print("  ✅ main.py导入成功")
        print("  ✅ 10月job函数导入成功")

        # 检查main.py中是否包含10月的逻辑
        import inspect
        source = inspect.getsource(main.run_jobs_serially)

        if "current_month == 10" in source:
            print("  ✅ main.py包含10月逻辑分支")
        else:
            print("  ❌ main.py缺少10月逻辑分支")
            return False

        if "signing_and_sales_incentive_oct_shanghai" in source:
            print("  ✅ main.py调用上海10月job")
        else:
            print("  ❌ main.py未调用上海10月job")
            return False

        if "signing_and_sales_incentive_oct_beijing" in source:
            print("  ✅ main.py调用北京10月job")
        else:
            print("  ❌ main.py未调用北京10月job")
            return False

        print("  🎉 整合测试通过！")
        return True

    except Exception as e:
        print(f"  ❌ 整合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_import_statements():
    """测试导入语句是否正确"""
    print("🧪 测试导入语句...")
    
    try:
        # 测试能否正确导入新架构的job函数
        from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing
        from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai
        
        print("  ✅ 北京10月job函数导入成功")
        print("  ✅ 上海10月job函数导入成功")
        
        # 验证函数是可调用的
        assert callable(signing_and_sales_incentive_oct_beijing), "北京10月job函数不可调用"
        assert callable(signing_and_sales_incentive_oct_shanghai), "上海10月job函数不可调用"
        
        print("  ✅ 函数可调用性验证通过")
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_month_logic():
    """测试月份逻辑分支"""
    print("🧪 测试月份逻辑分支...")

    try:
        # 检查main.py源码中的月份逻辑
        import main
        import inspect

        source = inspect.getsource(main.run_jobs_serially)

        # 检查各月份分支
        month_checks = [
            ("8月", "current_month == 8"),
            ("9月", "current_month == 9"),
            ("10月", "current_month == 10"),
        ]

        for month_name, condition in month_checks:
            if condition in source:
                print(f"  ✅ {month_name}逻辑分支存在")
            else:
                print(f"  ❌ {month_name}逻辑分支缺失")
                return False

        # 检查10月job调用
        oct_job_checks = [
            ("上海10月job", "signing_and_sales_incentive_oct_shanghai"),
            ("北京10月job", "signing_and_sales_incentive_oct_beijing"),
        ]

        for job_name, job_call in oct_job_checks:
            if job_call in source:
                print(f"  ✅ {job_name}调用存在")
            else:
                print(f"  ❌ {job_name}调用缺失")
                return False

        print("  🎉 月份逻辑测试通过！")
        return True

    except Exception as e:
        print(f"  ❌ 月份逻辑测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试main.py中10月job的整合")
    print("=" * 60)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    tests = [
        ("导入语句测试", test_import_statements),
        ("月份逻辑测试", test_month_logic),
        ("10月job整合测试", test_october_jobs_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！main.py整合成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查整合代码")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
