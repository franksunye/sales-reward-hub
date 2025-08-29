#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
兼容性测试模块
测试新的上海9月功能不会影响现有的北京8月和上海8月job功能
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jobs import signing_and_sales_incentive_aug_beijing, signing_and_sales_incentive_aug_shanghai
from modules.config import REWARD_CONFIGS


class TestCompatibility(unittest.TestCase):
    """兼容性测试类"""

    def setUp(self):
        """测试前准备"""
        self.original_configs = REWARD_CONFIGS.copy()

    def tearDown(self):
        """测试后清理"""
        # 恢复原始配置
        REWARD_CONFIGS.clear()
        REWARD_CONFIGS.update(self.original_configs)

    def test_existing_configs_unchanged(self):
        """测试现有配置未被修改"""
        # 检查北京8月配置
        self.assertIn("BJ-2025-08", REWARD_CONFIGS)
        bj_config = REWARD_CONFIGS["BJ-2025-08"]
        
        # 验证关键配置项存在且未被修改
        self.assertIn("lucky_number", bj_config)
        self.assertIn("performance_limits", bj_config)
        self.assertIn("tiered_rewards", bj_config)
        self.assertIn("awards_mapping", bj_config)
        
        # 检查上海4月配置（当前生产使用的配置）
        self.assertIn("SH-2025-04", REWARD_CONFIGS)
        sh_config = REWARD_CONFIGS["SH-2025-04"]
        
        # 验证关键配置项存在且未被修改
        self.assertIn("lucky_number", sh_config)
        self.assertIn("performance_limits", sh_config)
        self.assertIn("tiered_rewards", sh_config)
        self.assertIn("awards_mapping", sh_config)

    def test_new_config_added_correctly(self):
        """测试新配置正确添加"""
        # 检查上海9月配置
        self.assertIn("SH-2025-09", REWARD_CONFIGS)
        sh_sep_config = REWARD_CONFIGS["SH-2025-09"]
        
        # 验证新配置的关键项
        self.assertIn("self_referral_rewards", sh_sep_config)
        self.assertIn("awards_mapping", sh_sep_config)
        
        # 验证自引单配置
        self_referral = sh_sep_config["self_referral_rewards"]
        self.assertIn("enable", self_referral)
        self.assertIn("reward_type", self_referral)
        self.assertIn("reward_name", self_referral)
        
        # 验证奖励映射包含自引单奖励
        awards_mapping = sh_sep_config["awards_mapping"]
        self.assertIn("红包", awards_mapping)

    @patch('jobs.send_request_with_managed_session')
    @patch('jobs.save_to_csv_with_headers')
    @patch('jobs.archive_file')
    @patch('jobs.notify_awards_jun_beijing')
    @patch('jobs.read_contract_data')
    @patch('jobs.process_data_jun_beijing')
    @patch('jobs.write_performance_data')
    @patch('jobs.collect_unique_contract_ids_from_file')
    @patch('jobs.get_housekeeper_award_list')
    def test_beijing_aug_job_still_works(self, mock_get_award_list, mock_collect_ids, mock_write_perf, mock_process, mock_read, mock_notify, mock_archive, mock_save, mock_request):
        """测试北京8月job仍然正常工作"""
        # 模拟API响应
        mock_request.return_value = {
            'data': {
                'rows': [
                    ['BJ001', '北京', 'APP001', '已完成', '张三', 'CONTRACT001', 50000, 50000, 0, 
                     '已支付', '2025-08-15', '北京测试公司', '2025-08-15', 40000, '线上支付', 0.8, 50000]
                ]
            }
        }
        
        # 模拟文件保存成功
        mock_save.return_value = None
        mock_archive.return_value = None
        mock_notify.return_value = None
        mock_read.return_value = []  # 模拟空的现有合同数据
        mock_process.return_value = []  # 模拟处理后的数据
        mock_write_perf.return_value = None
        mock_collect_ids.return_value = set()  # 模拟空的现有合同ID集合
        mock_get_award_list.return_value = {}  # 模拟空的奖励列表
        
        try:
            # 执行北京8月job
            signing_and_sales_incentive_aug_beijing()
            
            # 验证关键函数被调用
            mock_request.assert_called_once()
            mock_save.assert_called_once()
            mock_notify.assert_called_once()
            
        except Exception as e:
            self.fail(f"北京8月job执行失败: {e}")

    @patch('jobs.send_request_with_managed_session')
    @patch('jobs.save_to_csv_with_headers')
    @patch('jobs.archive_file')
    @patch('jobs.notify_awards_shanghai_generate_message_march')
    @patch('jobs.read_contract_data')
    @patch('jobs.process_data_shanghai_apr')
    @patch('jobs.write_performance_data')
    @patch('jobs.collect_unique_contract_ids_from_file')
    @patch('jobs.get_unique_housekeeper_award_list')
    def test_shanghai_aug_job_still_works(self, mock_get_award_list, mock_collect_ids, mock_write_perf, mock_process, mock_read, mock_notify, mock_archive, mock_save, mock_request):
        """测试上海8月job仍然正常工作"""
        # 模拟API响应
        mock_request.return_value = {
            'data': {
                'rows': [
                    ['SH001', '上海', 'APP001', '已完成', '李四', 'CONTRACT001', 60000, 60000, 0, 
                     '已支付', '2025-08-15', '上海测试公司', '2025-08-15', 40000, '线上支付', 0.9, 60000]
                ]
            }
        }
        
        # 模拟文件保存成功
        mock_save.return_value = None
        mock_archive.return_value = None
        mock_notify.return_value = None
        mock_read.return_value = []  # 模拟空的现有合同数据
        mock_process.return_value = []  # 模拟处理后的数据
        mock_write_perf.return_value = None
        mock_collect_ids.return_value = set()  # 模拟空的现有合同ID集合
        mock_get_award_list.return_value = {}  # 模拟空的奖励列表
        
        try:
            # 执行上海8月job（实际使用4月配置）
            signing_and_sales_incentive_aug_shanghai()
            
            # 验证关键函数被调用
            mock_request.assert_called_once()
            mock_save.assert_called_once()
            mock_notify.assert_called_once()
            
        except Exception as e:
            self.fail(f"上海8月job执行失败: {e}")

    def test_function_imports_still_work(self):
        """测试现有函数导入仍然正常"""
        try:
            from jobs import (
                signing_and_sales_incentive_aug_beijing,
                signing_and_sales_incentive_aug_shanghai,
                signing_and_sales_incentive_sep_shanghai  # 新函数
            )
            
            # 验证函数可调用
            self.assertTrue(callable(signing_and_sales_incentive_aug_beijing))
            self.assertTrue(callable(signing_and_sales_incentive_aug_shanghai))
            self.assertTrue(callable(signing_and_sales_incentive_sep_shanghai))
            
        except ImportError as e:
            self.fail(f"函数导入失败: {e}")

    def test_config_isolation(self):
        """测试配置隔离性"""
        # 获取不同月份的配置
        bj_config = REWARD_CONFIGS.get("BJ-2025-08", {})
        sh_apr_config = REWARD_CONFIGS.get("SH-2025-04", {})  # 上海4月配置
        sh_sep_config = REWARD_CONFIGS.get("SH-2025-09", {})

        # 验证配置独立性
        # 北京8月应该有幸运奖，上海没有
        self.assertNotEqual(bj_config.get("lucky_number", ""), "")
        self.assertEqual(sh_apr_config.get("lucky_number", ""), "")
        self.assertEqual(sh_sep_config.get("lucky_number", ""), "")

        # 只有上海9月有自引单配置
        self.assertNotIn("self_referral_rewards", bj_config)
        self.assertNotIn("self_referral_rewards", sh_apr_config)
        self.assertIn("self_referral_rewards", sh_sep_config)

    def test_no_cross_contamination(self):
        """测试配置间无交叉污染"""
        # 修改上海9月配置
        if "SH-2025-09" in REWARD_CONFIGS:
            original_value = REWARD_CONFIGS["SH-2025-09"]["self_referral_rewards"]["enable"]
            REWARD_CONFIGS["SH-2025-09"]["self_referral_rewards"]["enable"] = not original_value
            
            # 验证其他配置未受影响
            bj_config = REWARD_CONFIGS.get("BJ-2025-08", {})
            sh_apr_config = REWARD_CONFIGS.get("SH-2025-04", {})

            # 北京和上海4月配置应该保持不变
            self.assertNotIn("self_referral_rewards", bj_config)
            self.assertNotIn("self_referral_rewards", sh_apr_config)
            
            # 恢复原值
            REWARD_CONFIGS["SH-2025-09"]["self_referral_rewards"]["enable"] = original_value


if __name__ == '__main__':
    unittest.main()
