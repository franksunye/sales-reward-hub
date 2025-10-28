#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证 ProcessingConfig.config 属性错误的修复
测试北京10月job是否能正常运行
"""

import logging
import sys
from modules.log_config import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def test_processing_pipeline_fix():
    """测试 processing_pipeline.py 的修复"""
    logger.info("=" * 60)
    logger.info("测试1: 验证 ProcessingConfig 不会访问 .config 属性")
    logger.info("=" * 60)
    
    try:
        from modules.core.data_models import ProcessingConfig, City
        
        # 创建一个 ProcessingConfig 对象
        config = ProcessingConfig(
            config_key="BJ-2025-10",
            activity_code="BJ-OCT",
            city=City("BJ"),
            housekeeper_key_format="管家"
        )
        
        # 验证 ProcessingConfig 没有 config 属性
        if hasattr(config, 'config'):
            logger.error("❌ ProcessingConfig 不应该有 config 属性")
            return False
        
        logger.info("✅ ProcessingConfig 正确地没有 config 属性")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_config_adapter():
    """测试 ConfigAdapter 能否正确获取配置"""
    logger.info("=" * 60)
    logger.info("测试2: 验证 ConfigAdapter 能正确获取配置")
    logger.info("=" * 60)
    
    try:
        from modules.core.config_adapter import ConfigAdapter
        
        # 测试获取北京10月配置
        config = ConfigAdapter.get_reward_config("BJ-2025-10")
        
        if not config:
            logger.error("❌ 无法获取 BJ-2025-10 配置")
            return False
        
        logger.info(f"✅ 成功获取 BJ-2025-10 配置")
        logger.info(f"   - 配置键: BJ-2025-10")
        logger.info(f"   - 包含字段: {list(config.keys())}")
        
        # 验证北京11月配置有 processing_config
        config_nov = ConfigAdapter.get_reward_config("BJ-2025-11")
        if "processing_config" in config_nov:
            logger.info(f"✅ BJ-2025-11 配置包含 processing_config")
            logger.info(f"   - process_platform_only: {config_nov['processing_config'].get('process_platform_only')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_processing_pipeline_creation():
    """测试处理管道创建是否正常"""
    logger.info("=" * 60)
    logger.info("测试3: 验证处理管道创建")
    logger.info("=" * 60)
    
    try:
        from modules.core import create_standard_pipeline
        
        # 创建北京10月处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-10",
            activity_code="BJ-OCT",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_project_limit=True,
            enable_dual_track=True,
            db_path=":memory:"  # 使用内存数据库
        )
        
        logger.info("✅ 成功创建北京10月处理管道")
        logger.info(f"   - 活动编码: {config.activity_code}")
        logger.info(f"   - 配置键: {config.config_key}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_processing_pipeline_process():
    """测试处理管道的 process 方法"""
    logger.info("=" * 60)
    logger.info("测试4: 验证处理管道的 process 方法")
    logger.info("=" * 60)
    
    try:
        from modules.core import create_standard_pipeline
        
        # 创建北京10月处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-10",
            activity_code="BJ-OCT",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_project_limit=True,
            enable_dual_track=True,
            db_path=":memory:"
        )
        
        # 创建测试数据
        test_contracts = [
            {
                '合同ID(_id)': 'test_001',
                '管家(serviceHousekeeper)': '测试管家',
                '合同金额(adjustRefundMoney)': 50000,
                '工单类型(sourceType)': 2,  # 平台单
                '签约时间(signedDate)': '2025-10-01',
                '服务商(orgName)': '测试服务商',
                '转化率(conversion)': 0.5,
                '平均客单价(average)': 10000,
            }
        ]
        
        # 调用 process 方法
        records = pipeline.process(test_contracts)
        
        logger.info(f"✅ 成功调用 process 方法")
        logger.info(f"   - 输入合同数: {len(test_contracts)}")
        logger.info(f"   - 输出记录数: {len(records)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """运行所有测试"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " " * 58 + "║")
    logger.info("║" + "  ProcessingConfig.config 属性错误修复验证".center(58) + "║")
    logger.info("║" + " " * 58 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("\n")
    
    tests = [
        ("ProcessingConfig 属性检查", test_processing_pipeline_fix),
        ("ConfigAdapter 配置获取", test_config_adapter),
        ("处理管道创建", test_processing_pipeline_creation),
        ("处理管道 process 方法", test_processing_pipeline_process),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ 测试异常: {e}")
            results.append((test_name, False))
        logger.info("\n")
    
    # 总结
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("\n🎉 所有测试通过！修复成功！")
        return 0
    else:
        logger.error(f"\n❌ 有 {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())

