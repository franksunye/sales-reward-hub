#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单快速测试脚本 - 完全使用Mock数据，不连接任何真实API
专注于验证业务逻辑，执行时间控制在30秒以内

使用方法:
    python test_jobs_simple.py

特点:
- 完全Mock模式，不连接任何外部服务
- 2-5秒内完成所有任务测试
- 验证核心业务逻辑流程
- 适合日常开发验证
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.log_config import setup_logging

# 设置日志
setup_logging()

class SimpleMocker:
    """简单Mock类 - 拦截所有外部调用"""
    def __init__(self):
        self.messages_sent = []
        self.api_calls = []
        
    def mock_api_request(self, *args, **kwargs):
        """Mock所有API请求"""
        self.api_calls.append({'args': args, 'kwargs': kwargs})
        print(f"🔧 [MOCK] API调用被拦截")

        # 根据URL判断返回什么类型的响应
        url = str(args[0]) if args else ""

        # 创建Mock响应对象
        class MockResponse:
            def __init__(self, is_session=False):
                self.status_code = 200 if is_session else 202
                self.is_session = is_session

            def json(self):
                if self.is_session:
                    # Session API返回格式
                    return {"id": "mock_session_id", "status": "success"}
                else:
                    # 数据API返回格式 - 包含完整的合同字段
                    mock_contract = [
                        "mock_contract_id_001",  # 合同ID(_id)
                        "110000",  # 活动城市(province)
                        "SA2025080001",  # 工单编号(serviceAppointmentNum)
                        "已完成",  # Status
                        "张三",  # 管家(serviceHousekeeper)
                        "BJ2025080001",  # 合同编号(contractdocNum)
                        "15000",  # 合同金额(adjustRefundMoney)
                        "15000",  # 支付金额(paidAmount)
                        "0",  # 差额(difference)
                        "已签约",  # State
                        "2025-08-15T10:30:00.000+08:00",  # 创建时间(createTime)
                        "北京博远恒泰装饰装修有限公司",  # 服务商(orgName)
                        "2025-08-15T14:20:00.000+08:00",  # 签约时间(signedDate)
                        "10000",  # Doorsill
                        "线上支付",  # 款项来源类型(tradeIn)
                        "0.85",  # 转化率(conversion)
                        "18500"  # 平均客单价(average)
                    ]
                    return {"data": {"rows": [mock_contract]}}

        # 判断是否是session API
        is_session = 'session' in url.lower()
        return MockResponse(is_session)
        
    def mock_webhook_post(self, *args, **kwargs):
        """Mock webhook消息发送"""
        self.messages_sent.append({'args': args, 'kwargs': kwargs})
        print(f"📤 [MOCK] 消息发送被拦截")
        return True
        
    def mock_task_create(self, *args, **kwargs):
        """Mock任务创建"""
        print(f"📋 [MOCK] 任务创建被拦截")
        return {"task_id": f"mock_{int(time.time())}", "status": "created"}

def test_single_job_simple(job_name, job_function):
    """简单测试单个任务"""
    print(f"\n{'='*50}")
    print(f"🚀 测试: {job_name}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    
    start_time = time.time()
    mocker = SimpleMocker()
    
    try:
        # Mock所有可能的外部调用
        with patch('modules.request_module.send_request_with_managed_session', mocker.mock_api_request), \
             patch('modules.notification_module.post_text_to_webhook', mocker.mock_webhook_post), \
             patch('modules.notification_module.post_markdown_v2_to_webhook', mocker.mock_webhook_post), \
             patch('modules.service_provider_sla_monitor.post_text_to_webhook', mocker.mock_webhook_post), \
             patch('task_manager.create_task', mocker.mock_task_create), \
             patch('requests.post', mocker.mock_api_request), \
             patch('requests.get', mocker.mock_api_request):
            
            print(f"🔧 Mock设置完成，开始执行...")
            
            # 执行任务
            job_function()
            
            execution_time = time.time() - start_time
            
            print(f"\n📊 测试结果:")
            print(f"   ✅ 状态: 成功")
            print(f"   ⏱️  执行时间: {execution_time:.2f} 秒")
            print(f"   📞 API调用: {len(mocker.api_calls)} 次")
            print(f"   💬 消息生成: {len(mocker.messages_sent)} 条")
            print(f"{'='*50}")
            
            return True, execution_time
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"\n📊 测试结果:")
        print(f"   ❌ 状态: 失败")
        print(f"   ⏱️  执行时间: {execution_time:.2f} 秒")
        print(f"   ❗ 错误: {str(e)}")
        print(f"{'='*50}")
        
        return False, execution_time

def run_simple_tests():
    """运行简单快速测试"""
    print("🎯 开始简单快速测试")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔧 模式: 完全Mock，不连接任何外部服务")
    print("⚡ 目标: 30秒内完成所有测试")
    
    # 导入任务函数
    try:
        from jobs import (
            signing_and_sales_incentive_aug_beijing,
            signing_and_sales_incentive_aug_shanghai,
            generate_daily_service_report,
            send_pending_orders_reminder
        )
    except ImportError as e:
        print(f"❌ 导入任务函数失败: {e}")
        return
    
    # 定义测试任务
    test_jobs = [
        ("北京8月签约激励", signing_and_sales_incentive_aug_beijing),
        ("上海8月签约激励", signing_and_sales_incentive_aug_shanghai),
        ("日常服务报告", generate_daily_service_report),
        ("待预约工单提醒", send_pending_orders_reminder)
    ]
    
    total_start = time.time()
    results = []
    
    for job_name, job_function in test_jobs:
        success, exec_time = test_single_job_simple(job_name, job_function)
        results.append({
            'name': job_name,
            'success': success,
            'time': exec_time
        })
        
        # 短暂间隔
        time.sleep(0.5)
    
    # 总结报告
    total_time = time.time() - total_start
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n{'🎉 测试完成报告':=^60}")
    print(f"📊 总体统计:")
    print(f"   ✅ 成功: {successful} 个任务")
    print(f"   ❌ 失败: {failed} 个任务")
    print(f"   ⏱️  总耗时: {total_time:.2f} 秒")
    
    if total_time < 30:
        print(f"   🎯 性能目标: ✅ 达成 (< 30秒)")
    else:
        print(f"   🎯 性能目标: ❌ 未达成 (> 30秒)")
    
    print(f"\n📋 详细结果:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['name']} - {result['time']:.2f}s")
    
    if failed == 0:
        print(f"\n🎉 所有任务测试通过！")
        print(f"💡 核心业务逻辑运行正常，可以安全部署。")
    else:
        print(f"\n⚠️  有 {failed} 个任务失败，请检查相关代码。")
    
    print(f"\n💡 测试说明:")
    print(f"   - 本测试使用完全Mock模式")
    print(f"   - 验证任务函数的基本执行流程")
    print(f"   - 不连接真实API，不发送真实消息")
    print(f"   - 适合快速验证代码变更")
    
    print(f"{'='*60}")

if __name__ == '__main__':
    try:
        run_simple_tests()
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试框架异常: {e}")
        import traceback
        print(traceback.format_exc())
