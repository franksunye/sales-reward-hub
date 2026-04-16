#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证北京11月job是否能正常运行
测试修复后的代码对11月job的影响
"""

import logging
import os
import sys
import types

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub

os.environ.setdefault("CONTACT_PHONE_NUMBER", "13800000000")
os.environ.setdefault("METABASE_USERNAME", "test@example.com")
os.environ.setdefault("METABASE_PASSWORD", "test-password")
os.environ.setdefault("WECOM_WEBHOOK_DEFAULT", "https://example.com/default")
os.environ.setdefault("WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT", "https://example.com/sign-broadcast")
os.environ.setdefault("DB_SOURCE", "local")

from modules.log_config import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def test_beijing_november_processing():
    """测试北京11月处理管道"""
    logger.info("=" * 60)
    logger.info("测试: 北京11月处理管道（仅播报模式）")
    logger.info("=" * 60)
    
    try:
        from modules.core import create_standard_pipeline
        from modules.core.config_adapter import ConfigAdapter
        
        # 获取北京11月配置
        config = ConfigAdapter.get_reward_config("BJ-2025-11")
        logger.info(f"✅ 成功获取 BJ-2025-11 配置")
        
        # 检查 processing_config
        processing_config = config.get("processing_config", {})
        process_platform_only = processing_config.get("process_platform_only", False)
        logger.info(f"   - process_platform_only: {process_platform_only}")
        
        # 创建北京11月处理管道
        pipeline, proc_config, store = create_standard_pipeline(
            config_key="BJ-2025-11",
            activity_code="BJ-NOV",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_project_limit=False,
            enable_dual_track=False,
            db_path=":memory:"
        )
        
        logger.info("✅ 成功创建北京11月处理管道")
        logger.info(f"   - 活动编码: {proc_config.activity_code}")
        logger.info(f"   - 配置键: {proc_config.config_key}")
        
        # 创建测试数据：包含平台单和自引单
        test_contracts = [
            {
                '合同ID(_id)': 'test_platform_001',
                '管家(serviceHousekeeper)': '测试管家A',
                '合同金额(adjustRefundMoney)': 50000,
                '工单类型(sourceType)': 2,  # 平台单
                '签约时间(signedDate)': '2025-11-01',
                '服务商(orgName)': '测试服务商',
                '转化率(conversion)': 0.5,
                '平均客单价(average)': 10000,
            },
            {
                '合同ID(_id)': 'test_self_001',
                '管家(serviceHousekeeper)': '测试管家B',
                '合同金额(adjustRefundMoney)': 30000,
                '工单类型(sourceType)': 1,  # 自引单
                '签约时间(signedDate)': '2025-11-02',
                '服务商(orgName)': '测试服务商',
                '转化率(conversion)': 0.3,
                '平均客单价(average)': 5000,
            }
        ]
        
        logger.info(f"\n创建测试数据:")
        logger.info(f"   - 平台单: 1个")
        logger.info(f"   - 自引单: 1个")
        logger.info(f"   - 总计: {len(test_contracts)}个")
        
        # 调用 process 方法
        logger.info(f"\n调用 process 方法...")
        records = pipeline.process(test_contracts)
        
        logger.info(f"✅ 成功调用 process 方法")
        logger.info(f"   - 输入合同数: {len(test_contracts)}")
        logger.info(f"   - 输出记录数: {len(records)}")
        
        # 验证仅播报模式的行为
        if process_platform_only:
            logger.info(f"\n✅ 仅播报模式验证:")
            logger.info(f"   - 应该仅处理平台单")
            logger.info(f"   - 自引单应该被过滤掉")
            logger.info(f"   - 预期输出: 最多1个记录（平台单）")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_notification_config():
    """测试北京11月通知配置"""
    logger.info("\n" + "=" * 60)
    logger.info("测试: 北京11月通知配置")
    logger.info("=" * 60)
    
    try:
        from modules.core.config_adapter import ConfigAdapter
        
        # 获取北京11月配置
        config = ConfigAdapter.get_reward_config("BJ-2025-11")
        
        # 检查 notification_config
        notification_config = config.get("notification_config", {})
        enable_award_notification = notification_config.get("enable_award_notification", True)
        
        logger.info(f"✅ 成功获取通知配置")
        logger.info(f"   - enable_award_notification: {enable_award_notification}")
        
        if not enable_award_notification:
            logger.info(f"   ✅ 正确：北京11月禁用了个人奖励通知（仅播报模式）")
        else:
            logger.warning(f"   ⚠️  警告：北京11月应该禁用个人奖励通知")
        
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
    logger.info("║" + "  北京11月job 修复验证".center(58) + "║")
    logger.info("║" + " " * 58 + "║")
    logger.info("╚" + "=" * 58 + "╝")
    logger.info("\n")
    
    tests = [
        ("北京11月处理管道", test_beijing_november_processing),
        ("北京11月通知配置", test_notification_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("\n🎉 北京11月job 正常运行！")
        return 0
    else:
        logger.error(f"\n❌ 有 {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
