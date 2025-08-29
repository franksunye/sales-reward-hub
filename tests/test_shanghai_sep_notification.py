"""
TDD测试：上海9月通知功能
测试 notify_awards_shanghai_generic() 函数的核心逻辑
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestShanghaiSepNotification(unittest.TestCase):
    """测试上海9月通知功能"""
    
    def setUp(self):
        """每个测试用例前的初始化"""
        self.config_key = "SH-2025-09"
        self.performance_data_filename = "test_performance_data.csv"
        self.status_filename = "test_status.json"
        
        # 模拟业绩数据记录
        self.sample_performance_records = [
            {
                '合同ID(_id)': 'SH001',
                '管家(serviceHousekeeper)': '张三',
                '合同编号(contractdocNum)': 'CT001',
                '工单类型': '平台单',
                '激活奖励状态': '1',
                '奖励类型': '节节高',
                '奖励名称': '基础奖',
                '是否发送通知': 'N',
                '管家累计单数': 5,
                '管家累计金额': 45000,
                '转化率(conversion)': '85%',
                '活动期内第几个合同': 1,
                '备注': '距离 达标奖 还需 15,000 元'
            },
            {
                '合同ID(_id)': 'SH002',
                '管家(serviceHousekeeper)': '李四',
                '合同编号(contractdocNum)': 'CT002',
                '工单类型': '自引单',
                '激活奖励状态': '1',
                '奖励类型': '自引单',
                '奖励名称': '红包',
                '是否发送通知': 'N',
                '管家累计单数': 1,
                '管家累计金额': 15000,
                '转化率(conversion)': '90%',
                '活动期内第几个合同': 2,
                '备注': '恭喜已经达成所有奖励，祝愿再接再厉，再创佳绩'
            }
        ]
    
    def test_notify_awards_shanghai_generic_function_exists(self):
        """测试：notify_awards_shanghai_generic函数是否存在"""
        # 这个测试会失败，因为函数还不存在
        from modules.notification_module import notify_awards_shanghai_generic
        
        # 测试函数签名
        with patch('modules.notification_module.get_all_records_from_csv') as mock_get_records, \
             patch('modules.notification_module.load_send_status') as mock_load_status, \
             patch('modules.notification_module.create_task') as mock_create_task:
            
            mock_get_records.return_value = []
            mock_load_status.return_value = {}
            
            # 函数应该能够被调用而不抛出异常
            notify_awards_shanghai_generic(
                self.performance_data_filename,
                self.status_filename,
                self.config_key
            )
    
    def test_group_notification_creation(self):
        """测试：群通知任务创建"""
        from modules.notification_module import notify_awards_shanghai_generic
        
        with patch('modules.notification_module.get_all_records_from_csv') as mock_get_records, \
             patch('modules.notification_module.load_send_status') as mock_load_status, \
             patch('modules.notification_module.create_task') as mock_create_task, \
             patch('modules.notification_module.update_send_status') as mock_update_status, \
             patch('modules.notification_module.write_performance_data_to_csv') as mock_write_csv, \
             patch('modules.notification_module.preprocess_amount') as mock_preprocess_amount, \
             patch('modules.notification_module.preprocess_rate') as mock_preprocess_rate:
            
            # 设置模拟返回值
            mock_get_records.return_value = [self.sample_performance_records[0]]
            mock_load_status.return_value = {}
            mock_preprocess_amount.return_value = "45,000"
            mock_preprocess_rate.return_value = "85%"
            
            # 调用函数
            notify_awards_shanghai_generic(
                self.performance_data_filename,
                self.status_filename,
                self.config_key
            )
            
            # 验证群通知任务被创建
            mock_create_task.assert_any_call(
                'send_wecom_message',
                '（上海）运营群',
                unittest.mock.ANY  # 消息内容我们稍后验证
            )
            
            # 验证状态更新
            mock_update_status.assert_called()
    
    def test_award_notification_creation(self):
        """测试：个人奖励通知任务创建"""
        from modules.notification_module import notify_awards_shanghai_generic
        
        with patch('modules.notification_module.get_all_records_from_csv') as mock_get_records, \
             patch('modules.notification_module.load_send_status') as mock_load_status, \
             patch('modules.notification_module.create_task') as mock_create_task, \
             patch('modules.notification_module.generate_award_message') as mock_generate_award, \
             patch('modules.notification_module.update_send_status') as mock_update_status, \
             patch('modules.notification_module.write_performance_data_to_csv') as mock_write_csv, \
             patch('modules.notification_module.preprocess_amount') as mock_preprocess_amount, \
             patch('modules.notification_module.preprocess_rate') as mock_preprocess_rate:
            
            # 设置模拟返回值
            mock_get_records.return_value = [self.sample_performance_records[0]]
            mock_load_status.return_value = {}
            mock_generate_award.return_value = "张三签约合同CT001\n\n达成基础奖奖励条件，获得签约奖励200元 🧧🧧🧧"
            mock_preprocess_amount.return_value = "45,000"
            mock_preprocess_rate.return_value = "85%"
            
            # 调用函数
            notify_awards_shanghai_generic(
                self.performance_data_filename,
                self.status_filename,
                self.config_key
            )
            
            # 验证个人奖励通知任务被创建
            mock_create_task.assert_any_call(
                'send_wechat_message',
                '满浩浩',
                "张三签约合同CT001\n\n达成基础奖奖励条件，获得签约奖励200元 🧧🧧🧧"
            )
    
    def test_self_referral_notification(self):
        """测试：自引单通知处理"""
        from modules.notification_module import notify_awards_shanghai_generic
        
        with patch('modules.notification_module.get_all_records_from_csv') as mock_get_records, \
             patch('modules.notification_module.load_send_status') as mock_load_status, \
             patch('modules.notification_module.create_task') as mock_create_task, \
             patch('modules.notification_module.generate_award_message') as mock_generate_award, \
             patch('modules.notification_module.update_send_status') as mock_update_status, \
             patch('modules.notification_module.write_performance_data_to_csv') as mock_write_csv, \
             patch('modules.notification_module.preprocess_amount') as mock_preprocess_amount, \
             patch('modules.notification_module.preprocess_rate') as mock_preprocess_rate:
            
            # 设置模拟返回值 - 自引单记录
            mock_get_records.return_value = [self.sample_performance_records[1]]
            mock_load_status.return_value = {}
            mock_generate_award.return_value = "李四签约合同CT002\n\n达成红包奖励条件，获得签约奖励50元 🧧🧧🧧"
            mock_preprocess_amount.return_value = "15,000"
            mock_preprocess_rate.return_value = "90%"
            
            # 调用函数
            notify_awards_shanghai_generic(
                self.performance_data_filename,
                self.status_filename,
                self.config_key
            )
            
            # 验证群通知包含自引单标识
            group_call_args = None
            for call in mock_create_task.call_args_list:
                if call[0][0] == 'send_wecom_message':
                    group_call_args = call[0][2]  # 消息内容
                    break
            
            self.assertIsNotNone(group_call_args)
            self.assertIn('自引单', group_call_args)
            self.assertIn('李四', group_call_args)
    
    def test_no_notification_for_sent_records(self):
        """测试：已发送通知的记录不重复处理"""
        from modules.notification_module import notify_awards_shanghai_generic
        
        with patch('modules.notification_module.get_all_records_from_csv') as mock_get_records, \
             patch('modules.notification_module.load_send_status') as mock_load_status, \
             patch('modules.notification_module.create_task') as mock_create_task:
            
            # 设置已发送状态
            record_with_sent_status = self.sample_performance_records[0].copy()
            record_with_sent_status['是否发送通知'] = 'Y'
            
            mock_get_records.return_value = [record_with_sent_status]
            mock_load_status.return_value = {'SH001': '发送成功'}
            
            # 调用函数
            notify_awards_shanghai_generic(
                self.performance_data_filename,
                self.status_filename,
                self.config_key
            )
            
            # 验证没有创建任务
            mock_create_task.assert_not_called()

if __name__ == '__main__':
    unittest.main()
