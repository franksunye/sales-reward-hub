#!/usr/bin/env python3
"""
手工测试10月job函数
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_shanghai_october_job():
    """测试上海10月job"""
    print("🧪 测试上海10月job...")
    
    try:
        from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai
        
        print("  📥 导入上海10月job函数成功")
        print("  🚀 开始执行上海10月job...")
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行job（这会调用真实的API和数据库）
        result = signing_and_sales_incentive_oct_shanghai()
        
        # 记录结束时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"  ✅ 上海10月job执行成功")
        print(f"  📊 处理记录数: {len(result) if result else 0}")
        print(f"  ⏱️  执行时间: {execution_time:.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 上海10月job执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_beijing_october_job():
    """测试北京10月job"""
    print("🧪 测试北京10月job...")
    
    try:
        from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing
        
        print("  📥 导入北京10月job函数成功")
        print("  🚀 开始执行北京10月job...")
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行job（这会调用真实的API和数据库）
        result = signing_and_sales_incentive_oct_beijing()
        
        # 记录结束时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"  ✅ 北京10月job执行成功")
        print(f"  📊 处理记录数: {len(result) if result else 0}")
        print(f"  ⏱️  执行时间: {execution_time:.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 北京10月job执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_run_jobs_serially():
    """测试main.py的run_jobs_serially函数（模拟10月）"""
    print("🧪 测试main.py的run_jobs_serially函数...")
    
    try:
        # 临时修改当前月份为10月进行测试
        import datetime
        original_now = datetime.datetime.now
        
        # 创建一个返回10月的mock函数
        def mock_now():
            return datetime.datetime(2025, 10, 15, 12, 0, 0)
        
        # 替换datetime.now
        datetime.datetime.now = mock_now
        
        try:
            from main import run_jobs_serially
            
            print("  📅 模拟当前月份为10月")
            print("  🚀 执行run_jobs_serially()...")
            
            # 记录开始时间
            start_time = original_now()
            
            # 执行函数
            run_jobs_serially()
            
            # 记录结束时间
            end_time = original_now()
            execution_time = (end_time - start_time).total_seconds()
            
            print(f"  ✅ run_jobs_serially执行成功")
            print(f"  ⏱️  执行时间: {execution_time:.2f}秒")
            
            return True
            
        finally:
            # 恢复原始的datetime.now
            datetime.datetime.now = original_now
        
    except Exception as e:
        print(f"  ❌ run_jobs_serially执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 开始手工测试10月job函数")
    print("=" * 60)
    print("⚠️  注意：这将调用真实的API和数据库！")
    print("=" * 60)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 询问用户是否继续
    response = input("\n是否继续执行真实的job测试？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("测试已取消")
        return True
    
    tests = [
        ("上海10月job测试", test_shanghai_october_job),
        ("北京10月job测试", test_beijing_october_job),
        ("main.py集成测试", test_main_run_jobs_serially),
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
        print("🎉 所有测试通过！10月job运行正常！")
        return True
    else:
        print("⚠️  部分测试失败，请检查job实现")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
