#!/usr/bin/env python3
"""
新架构执行测试工具

测试新架构函数的实际执行能力，验证是否能正常运行并产生输出。

使用方法:
    python scripts/new_arch_execution_test.py --city beijing
    python scripts/new_arch_execution_test.py --city shanghai
    python scripts/new_arch_execution_test.py --all
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_beijing_execution():
    """测试北京9月新架构执行"""
    logger = setup_test_logging()
    
    print("🏢 测试北京9月新架构执行")
    print("=" * 50)
    
    try:
        # 导入函数
        from modules.core.beijing_jobs import signing_and_sales_incentive_sep_beijing_v2
        print("✅ 函数导入成功")
        
        # 检查函数是否可调用
        if not callable(signing_and_sales_incentive_sep_beijing_v2):
            print("❌ 函数不可调用")
            return False
        
        print("🚀 开始执行北京9月新架构函数...")
        print("注意：这将尝试实际执行函数，可能需要网络连接和数据库")
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行函数
        try:
            result = signing_and_sales_incentive_sep_beijing_v2()
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ 执行成功！")
            print(f"   - 执行时间: {execution_time:.2f} 秒")
            print(f"   - 返回结果类型: {type(result)}")
            
            if hasattr(result, '__len__'):
                print(f"   - 结果数量: {len(result)} 条记录")
            
            if result and hasattr(result[0], '__dict__'):
                print(f"   - 第一条记录类型: {type(result[0])}")
                
            return True
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ 执行失败 (耗时 {execution_time:.2f} 秒)")
            print(f"   错误: {e}")
            
            # 分析错误类型
            error_type = type(e).__name__
            if "ModuleNotFoundError" in error_type:
                print("   🔍 分析: 缺少依赖模块")
            elif "ConnectionError" in error_type or "requests" in str(e).lower():
                print("   🔍 分析: 网络连接问题")
            elif "database" in str(e).lower() or "sqlite" in str(e).lower():
                print("   🔍 分析: 数据库相关问题")
            elif "config" in str(e).lower():
                print("   🔍 分析: 配置相关问题")
            else:
                print("   🔍 分析: 其他执行错误")
            
            return False
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_shanghai_execution():
    """测试上海9月新架构执行"""
    logger = setup_test_logging()
    
    print("\n🏙️ 测试上海9月新架构执行")
    print("=" * 50)
    
    try:
        # 导入函数
        from modules.core.shanghai_jobs import signing_and_sales_incentive_sep_shanghai_v2
        print("✅ 函数导入成功")
        
        # 检查函数是否可调用
        if not callable(signing_and_sales_incentive_sep_shanghai_v2):
            print("❌ 函数不可调用")
            return False
        
        print("🚀 开始执行上海9月新架构函数...")
        print("注意：这将尝试实际执行函数，可能需要网络连接和数据库")
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 执行函数
        try:
            result = signing_and_sales_incentive_sep_shanghai_v2()
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f"✅ 执行成功！")
            print(f"   - 执行时间: {execution_time:.2f} 秒")
            print(f"   - 返回结果类型: {type(result)}")
            
            if hasattr(result, '__len__'):
                print(f"   - 结果数量: {len(result)} 条记录")
            
            if result and hasattr(result[0], '__dict__'):
                print(f"   - 第一条记录类型: {type(result[0])}")
                
            return True
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ 执行失败 (耗时 {execution_time:.2f} 秒)")
            print(f"   错误: {e}")
            
            # 分析错误类型
            error_type = type(e).__name__
            if "ModuleNotFoundError" in error_type:
                print("   🔍 分析: 缺少依赖模块")
            elif "ConnectionError" in error_type or "requests" in str(e).lower():
                print("   🔍 分析: 网络连接问题")
            elif "database" in str(e).lower() or "sqlite" in str(e).lower():
                print("   🔍 分析: 数据库相关问题")
            elif "config" in str(e).lower():
                print("   🔍 分析: 配置相关问题")
            else:
                print("   🔍 分析: 其他执行错误")
            
            return False
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_configuration_loading():
    """测试配置加载"""
    print("\n⚙️ 测试配置加载")
    print("=" * 50)
    
    try:
        from modules.core.config_adapter import ConfigAdapter
        
        # 测试北京配置
        bj_config = ConfigAdapter.get_reward_config("BJ-2025-09")
        print(f"✅ 北京9月配置加载成功")
        print(f"   - 配置字段数: {len(bj_config)}")
        print(f"   - 幸运数字: {bj_config.get('lucky_number')}")
        print(f"   - 奖励类型数: {len(bj_config.get('awards_mapping', {}))}")
        
        # 测试上海配置
        sh_config = ConfigAdapter.get_reward_config("SH-2025-09")
        print(f"✅ 上海9月配置加载成功")
        print(f"   - 配置字段数: {len(sh_config)}")
        print(f"   - 幸运数字: {sh_config.get('lucky_number', '未设置')}")
        print(f"   - 奖励类型数: {len(sh_config.get('awards_mapping', {}))}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='新架构执行测试工具')
    parser.add_argument('--city', choices=['beijing', 'shanghai'], help='测试指定城市')
    parser.add_argument('--all', action='store_true', help='测试所有城市')
    parser.add_argument('--config-only', action='store_true', help='只测试配置加载')
    
    args = parser.parse_args()
    
    print("🔍 新架构执行测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 配置测试
    if args.config_only or not args.city:
        config_result = test_configuration_loading()
        results.append(("配置加载", config_result))
        
        if args.config_only:
            print(f"\n{'='*60}")
            print(f"配置测试结果: {'通过' if config_result else '失败'}")
            return 0 if config_result else 1
    
    # 执行测试
    if args.all:
        bj_result = test_beijing_execution()
        sh_result = test_shanghai_execution()
        results.extend([("北京9月执行", bj_result), ("上海9月执行", sh_result)])
    elif args.city == 'beijing':
        bj_result = test_beijing_execution()
        results.append(("北京9月执行", bj_result))
    elif args.city == 'shanghai':
        sh_result = test_shanghai_execution()
        results.append(("上海9月执行", sh_result))
    else:
        # 默认测试配置和北京
        config_result = test_configuration_loading()
        bj_result = test_beijing_execution()
        results.extend([("配置加载", config_result), ("北京9月执行", bj_result)])
    
    # 总结结果
    print(f"\n{'='*60}")
    print("📊 测试结果总结")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！新架构功能正常")
        return 0
    else:
        print("⚠️ 部分测试失败，需要检查问题")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
