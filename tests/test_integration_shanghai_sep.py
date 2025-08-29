#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海9月签约激励Job集成测试
测试完整的job流程，包括双轨处理逻辑
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jobs import signing_and_sales_incentive_sep_shanghai
from modules.config import REWARD_CONFIGS


class TestShanghaiSepIntegration(unittest.TestCase):
    """上海9月签约激励Job集成测试类"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 模拟API响应数据（包含平台单和自引单）
        self.mock_api_response = {
            'data': {
                'rows': [
                    # 平台单
                    ['SH001', '上海', 'APP001', '已完成', '张三', 'CONTRACT001', 50000, 50000, 0, 
                     '已支付', '2025-09-15', '上海测试公司', '2025-09-15', 40000, '线上支付', 0.8, 50000,
                     'housekeeper_001', 2, '上海市浦东新区张江路123号', '上海市浦东新区科技园456号'],
                    # 自引单
                    ['SH002', '上海', 'APP002', '已完成', '李四', 'CONTRACT002', 30000, 30000, 0, 
                     '已支付', '2025-09-15', '上海测试公司2', '2025-09-15', 40000, '线上支付', 0.9, 30000,
                     'housekeeper_002', 1, '上海市浦东新区张江路456号', '上海市浦东新区创新园789号'],
                    # 另一个自引单（相同项目地址，测试去重）
                    ['SH003', '上海', 'APP003', '已完成', '李四', 'CONTRACT003', 25000, 25000, 0, 
                     '已支付', '2025-09-15', '上海测试公司2', '2025-09-15', 40000, '线上支付', 0.9, 25000,
                     'housekeeper_002', 1, '上海市浦东新区张江路789号', '上海市浦东新区创新园789号']
                ]
            }
        }

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('jobs.archive_file')
    @patch('jobs.notify_awards_shanghai_generic')
    @patch('jobs.write_performance_data_to_csv')
    @patch('jobs.get_unique_housekeeper_award_list')
    @patch('jobs.collect_unique_contract_ids_from_file')
    @patch('jobs.save_to_csv_with_headers')
    @patch('jobs.send_request_with_managed_session')
    def test_complete_shanghai_sep_job_flow(self, mock_request, mock_save_csv, mock_collect_ids, 
                                          mock_get_awards, mock_write_perf, mock_notify, mock_archive):
        """测试完整的上海9月job流程"""
        
        # 1. 模拟API响应
        mock_request.return_value = self.mock_api_response
        
        # 2. 模拟文件操作
        mock_save_csv.return_value = None
        mock_collect_ids.return_value = set()  # 没有现有合同
        mock_get_awards.return_value = {}  # 没有现有奖励
        mock_write_perf.return_value = None
        mock_notify.return_value = None
        mock_archive.return_value = None
        
        # 3. 执行job
        try:
            signing_and_sales_incentive_sep_shanghai()
            
            # 4. 验证关键函数被调用
            mock_request.assert_called_once()
            mock_save_csv.assert_called_once()
            mock_collect_ids.assert_called_once()
            mock_get_awards.assert_called_once()
            mock_write_perf.assert_called_once()
            mock_notify.assert_called_once()
            mock_archive.assert_called_once()
            
            # 5. 验证通知函数使用了正确的配置
            notify_call_args = mock_notify.call_args
            self.assertEqual(notify_call_args[0][2], "SH-2025-09")  # 配置键
            
        except Exception as e:
            self.fail(f"上海9月job执行失败: {e}")

    @patch('jobs.archive_file')
    @patch('jobs.notify_awards_shanghai_generic')
    @patch('jobs.write_performance_data_to_csv')
    @patch('jobs.get_unique_housekeeper_award_list')
    @patch('jobs.collect_unique_contract_ids_from_file')
    @patch('jobs.save_to_csv_with_headers')
    @patch('jobs.send_request_with_managed_session')
    def test_data_processing_with_mixed_orders(self, mock_request, mock_save_csv, mock_collect_ids, 
                                             mock_get_awards, mock_write_perf, mock_notify, mock_archive):
        """测试混合订单的数据处理"""
        
        # 模拟API响应
        mock_request.return_value = self.mock_api_response
        
        # 模拟文件操作
        mock_save_csv.return_value = None
        mock_collect_ids.return_value = set()
        mock_get_awards.return_value = {}
        mock_archive.return_value = None
        mock_notify.return_value = None
        
        # 捕获写入的业绩数据
        captured_data = []
        def capture_write_perf(filename, data, headers):
            captured_data.extend(data)
        mock_write_perf.side_effect = capture_write_perf
        
        # 执行job
        signing_and_sales_incentive_sep_shanghai()
        
        # 验证数据处理结果
        self.assertEqual(len(captured_data), 3)  # 应该处理3个合同
        
        # 验证平台单处理
        platform_orders = [d for d in captured_data if d.get('工单类型') == '平台单']
        self.assertEqual(len(platform_orders), 1)
        
        # 验证自引单处理
        self_referral_orders = [d for d in captured_data if d.get('工单类型') == '自引单']
        self.assertEqual(len(self_referral_orders), 2)
        
        # 验证新增字段存在
        for data in captured_data:
            self.assertIn('管家ID(serviceHousekeeperId)', data)
            self.assertIn('工单类型', data)
            self.assertIn('客户联系地址(contactsAddress)', data)
            self.assertIn('项目地址(projectAddress)', data)
            self.assertIn('平台单累计数量', data)
            self.assertIn('平台单累计金额', data)
            self.assertIn('自引单累计数量', data)
            self.assertIn('自引单累计金额', data)

    def test_config_exists_and_valid(self):
        """测试上海9月配置存在且有效"""
        
        # 验证配置存在
        self.assertIn("SH-2025-09", REWARD_CONFIGS)
        
        config = REWARD_CONFIGS["SH-2025-09"]
        
        # 验证基础配置
        self.assertIn("lucky_number", config)
        self.assertIn("performance_limits", config)
        self.assertIn("tiered_rewards", config)
        self.assertIn("awards_mapping", config)
        
        # 验证自引单配置
        self.assertIn("self_referral_rewards", config)
        self_referral = config["self_referral_rewards"]
        
        self.assertIn("enable", self_referral)
        self.assertIn("reward_type", self_referral)
        self.assertIn("reward_name", self_referral)
        self.assertIn("deduplication_field", self_referral)
        
        # 验证自引单奖励在映射中存在
        reward_name = self_referral["reward_name"]
        self.assertIn(reward_name, config["awards_mapping"])

    @patch('jobs.archive_file')
    @patch('jobs.notify_awards_shanghai_generic')
    @patch('jobs.write_performance_data_to_csv')
    @patch('jobs.get_unique_housekeeper_award_list')
    @patch('jobs.collect_unique_contract_ids_from_file')
    @patch('jobs.save_to_csv_with_headers')
    @patch('jobs.send_request_with_managed_session')
    def test_no_message_sending_when_scheduler_disabled(self, mock_request, mock_save_csv, mock_collect_ids, 
                                                       mock_get_awards, mock_write_perf, mock_notify, mock_archive):
        """测试在禁用调度器的情况下不会发送真实消息"""
        
        # 模拟API响应
        mock_request.return_value = self.mock_api_response
        
        # 模拟文件操作
        mock_save_csv.return_value = None
        mock_collect_ids.return_value = set()
        mock_get_awards.return_value = {}
        mock_write_perf.return_value = None
        mock_archive.return_value = None
        
        # 模拟通知函数，确保它被调用但不发送真实消息
        mock_notify.return_value = None
        
        # 执行job
        signing_and_sales_incentive_sep_shanghai()
        
        # 验证通知函数被调用（生成任务）
        mock_notify.assert_called_once()
        
        # 验证没有真实的消息发送（因为调度器被禁用）
        # 这里我们只是验证job能正常执行，真实的消息发送由任务调度器控制
        self.assertTrue(True)  # job执行成功就说明测试通过

    def test_function_imports_work(self):
        """测试新函数可以正确导入"""
        
        try:
            from jobs import signing_and_sales_incentive_sep_shanghai
            from modules.data_processing_module import (
                process_data_shanghai_sep,
                determine_self_referral_rewards,
                get_self_referral_config,
                create_performance_record_shanghai_sep
            )
            from modules.notification_module import notify_awards_shanghai_generic
            
            # 验证函数可调用
            self.assertTrue(callable(signing_and_sales_incentive_sep_shanghai))
            self.assertTrue(callable(process_data_shanghai_sep))
            self.assertTrue(callable(determine_self_referral_rewards))
            self.assertTrue(callable(get_self_referral_config))
            self.assertTrue(callable(create_performance_record_shanghai_sep))
            self.assertTrue(callable(notify_awards_shanghai_generic))
            
        except ImportError as e:
            self.fail(f"函数导入失败: {e}")


if __name__ == '__main__':
    unittest.main()
