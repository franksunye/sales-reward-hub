"""
TDD测试：上海9月完整Job集成测试
测试 signing_and_sales_incentive_sep_shanghai() 函数的完整流程
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestShanghaiSepJobIntegration(unittest.TestCase):
    """测试上海9月完整Job集成功能"""
    
    def setUp(self):
        """每个测试用例前的初始化"""
        # 模拟API响应数据
        self.mock_api_response = [
            {
                '_id': 'SH001',
                'province': '上海',
                'serviceAppointmentNum': 'WO001',
                'status': 'active',
                'serviceHousekeeper': '张三',
                'contractdocNum': 'CT001',
                'adjustRefundMoney': 25000,
                'paidAmount': 25000,
                'difference': 0,
                'state': 'valid',
                'createTime': '2025-09-01',
                'orgName': '上海英森防水工程有限公司',
                'signedDate': '2025-09-01',
                'doorsill': 10000,
                'tradeIn': 'type1',
                'conversion': 85,
                'average': 25000,
                # 新增字段
                'serviceHousekeeperId': 'HK001',
                'sourceType': 2,  # 平台单
                'contactsAddress': '上海市浦东新区张江路123号',
                'projectAddress': '上海市浦东新区科技园456号'
            },
            {
                '_id': 'SH002',
                'province': '上海',
                'serviceAppointmentNum': 'WO002',
                'status': 'active',
                'serviceHousekeeper': '李四',
                'contractdocNum': 'CT002',
                'adjustRefundMoney': 15000,
                'paidAmount': 15000,
                'difference': 0,
                'state': 'valid',
                'createTime': '2025-09-02',
                'orgName': '上海英森防水工程有限公司',
                'signedDate': '2025-09-02',
                'doorsill': 10000,
                'tradeIn': 'type1',
                'conversion': 90,
                'average': 15000,
                # 新增字段
                'serviceHousekeeperId': 'HK002',
                'sourceType': 1,  # 自引单
                'contactsAddress': '上海市徐汇区漕河泾开发区789号',
                'projectAddress': '上海市徐汇区漕河泾开发区789号'
            }
        ]
        
        # 模拟现有合同ID
        self.existing_contract_ids = []
        
        # 模拟文件路径
        self.raw_data_file = "RawData-SH-Sep.csv"
        self.performance_data_file = "PerformanceData-SH-Sep.csv"
        self.status_file = "send_status_shanghai_sep.json"
    
    def test_signing_and_sales_incentive_sep_shanghai_function_exists(self):
        """测试：主job函数是否存在"""
        # 这个测试会失败，因为函数还不存在
        from jobs import signing_and_sales_incentive_sep_shanghai
        
        # 测试函数签名 - 应该能够被调用而不抛出异常
        with patch('jobs.send_request_with_managed_session') as mock_fetch, \
             patch('jobs.save_to_csv_with_headers') as mock_save_csv, \
             patch('jobs.collect_unique_contract_ids_from_file') as mock_get_existing, \
             patch('jobs.get_unique_housekeeper_award_list') as mock_get_awards, \
             patch('jobs.process_data_shanghai_sep') as mock_process, \
             patch('jobs.write_performance_data_to_csv') as mock_write_csv, \
             patch('jobs.notify_awards_shanghai_generic') as mock_notify, \
             patch('jobs.archive_file') as mock_archive:
            
            mock_fetch.return_value = {'data': {'rows': []}}
            mock_get_existing.return_value = set()
            mock_get_awards.return_value = {}
            mock_process.return_value = []

            # 函数应该能够被调用
            signing_and_sales_incentive_sep_shanghai()

if __name__ == '__main__':
    unittest.main()
