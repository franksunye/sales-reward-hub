"""
TDD测试：上海9月数据处理功能
测试 process_data_shanghai_sep() 函数的核心逻辑
"""

import unittest
import sys
import os
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestShanghaiSepDataProcessing(unittest.TestCase):
    """测试上海9月数据处理功能"""
    
    def setUp(self):
        """每个测试用例前的初始化"""
        self.config_key = "SH-2025-09"
        
        # 模拟合同数据（包含新字段）
        self.sample_contract_data = [
            {
                '合同ID(_id)': 'SH001',
                '活动城市(province)': '上海',
                '工单编号(serviceAppointmentNum)': 'WO001',
                'Status': 'active',
                '管家(serviceHousekeeper)': '张三',
                '合同编号(contractdocNum)': 'CT001',
                '合同金额(adjustRefundMoney)': '25000',
                '支付金额(paidAmount)': '25000',
                '差额(difference)': '0',
                'State': 'valid',
                '创建时间(createTime)': '2025-09-01',
                '服务商(orgName)': '上海英森防水工程有限公司',
                '签约时间(signedDate)': '2025-09-01',
                'Doorsill': '10000',
                '款项来源类型(tradeIn)': 'type1',
                '转化率(conversion)': '85%',
                '平均客单价(average)': '25000',
                # 新增字段
                '管家ID(serviceHousekeeperId)': 'HK001',
                '工单类型(sourceType)': 2,  # 平台单
                '客户联系地址(contactsAddress)': '上海市浦东新区张江路123号',
                '项目地址(projectAddress)': '上海市浦东新区科技园456号'
            },
            {
                '合同ID(_id)': 'SH002',
                '活动城市(province)': '上海',
                '工单编号(serviceAppointmentNum)': 'WO002',
                'Status': 'active',
                '管家(serviceHousekeeper)': '张三',
                '合同编号(contractdocNum)': 'CT002',
                '合同金额(adjustRefundMoney)': '15000',
                '支付金额(paidAmount)': '15000',
                '差额(difference)': '0',
                'State': 'valid',
                '创建时间(createTime)': '2025-09-02',
                '服务商(orgName)': '上海英森防水工程有限公司',
                '签约时间(signedDate)': '2025-09-02',
                'Doorsill': '10000',
                '款项来源类型(tradeIn)': 'type1',
                '转化率(conversion)': '90%',
                '平均客单价(average)': '15000',
                # 新增字段
                '管家ID(serviceHousekeeperId)': 'HK001',
                '工单类型(sourceType)': 1,  # 自引单
                '客户联系地址(contactsAddress)': '上海市徐汇区漕河泾开发区789号',
                '项目地址(projectAddress)': '上海市徐汇区漕河泾开发区789号'
            }
        ]
        
        self.existing_contract_ids = set()
        self.housekeeper_award_lists = {}
    
    def test_process_data_shanghai_sep_function_exists(self):
        """测试：process_data_shanghai_sep函数是否存在"""
        # 这个测试会失败，因为函数还不存在
        from modules.data_processing_module import process_data_shanghai_sep
        
        # 测试函数签名
        result = process_data_shanghai_sep(
            self.sample_contract_data, 
            self.existing_contract_ids, 
            self.housekeeper_award_lists
        )
        self.assertIsInstance(result, list)

    def test_platform_order_processing(self):
        """测试：平台单处理逻辑"""
        from modules.data_processing_module import process_data_shanghai_sep

        # 只包含平台单的数据
        platform_data = [self.sample_contract_data[0]]  # sourceType = 2

        result = process_data_shanghai_sep(
            platform_data,
            self.existing_contract_ids,
            self.housekeeper_award_lists
        )

        self.assertEqual(len(result), 1)
        record = result[0]

        # 验证基本字段
        self.assertEqual(record['合同ID(_id)'], 'SH001')
        self.assertEqual(record['工单类型'], '平台单')

        # 验证新增统计字段
        self.assertEqual(record['平台单累计数量'], 1)
        self.assertEqual(record['平台单累计金额'], 25000.0)
        self.assertEqual(record['自引单累计数量'], 0)
        self.assertEqual(record['自引单累计金额'], 0.0)

        # 验证管家累计数据
        self.assertEqual(record['管家累计单数'], 1)
        self.assertEqual(record['管家累计金额'], 25000)

    def test_self_referral_order_processing(self):
        """测试：自引单处理逻辑"""
        from modules.data_processing_module import process_data_shanghai_sep

        # 只包含自引单的数据
        self_referral_data = [self.sample_contract_data[1]]  # sourceType = 1

        result = process_data_shanghai_sep(
            self_referral_data,
            self.existing_contract_ids,
            self.housekeeper_award_lists
        )

        self.assertEqual(len(result), 1)
        record = result[0]

        # 验证基本字段
        self.assertEqual(record['合同ID(_id)'], 'SH002')
        self.assertEqual(record['工单类型'], '自引单')

        # 验证新增统计字段
        self.assertEqual(record['平台单累计数量'], 0)
        self.assertEqual(record['平台单累计金额'], 0.0)
        self.assertEqual(record['自引单累计数量'], 1)
        self.assertEqual(record['自引单累计金额'], 15000.0)

        # 验证自引单奖励
        self.assertEqual(record['奖励类型'], '自引单')
        self.assertEqual(record['奖励名称'], '红包')
        self.assertEqual(record['激活奖励状态'], 1)

        # 验证管家累计数据
        self.assertEqual(record['管家累计单数'], 1)
        self.assertEqual(record['管家累计金额'], 15000)

    def test_mixed_orders_processing(self):
        """测试：混合订单处理逻辑"""
        from modules.data_processing_module import process_data_shanghai_sep

        # 包含平台单和自引单的混合数据
        result = process_data_shanghai_sep(
            self.sample_contract_data,
            self.existing_contract_ids,
            self.housekeeper_award_lists
        )

        self.assertEqual(len(result), 2)

        # 验证第一条记录（平台单）
        platform_record = result[0]
        self.assertEqual(platform_record['工单类型'], '平台单')
        self.assertEqual(platform_record['平台单累计数量'], 1)
        self.assertEqual(platform_record['自引单累计数量'], 0)

        # 验证第二条记录（自引单）
        self_referral_record = result[1]
        self.assertEqual(self_referral_record['工单类型'], '自引单')
        self.assertEqual(self_referral_record['平台单累计数量'], 1)  # 累计包含之前的平台单
        self.assertEqual(self_referral_record['自引单累计数量'], 1)

        # 验证管家累计数据（应该是两种订单的总和）
        final_record = result[-1]
        self.assertEqual(final_record['管家累计单数'], 2)
        self.assertEqual(final_record['管家累计金额'], 40000)  # 25000 + 15000

    def test_new_fields_mapping(self):
        """测试：新增字段的正确映射"""
        from modules.data_processing_module import process_data_shanghai_sep

        result = process_data_shanghai_sep(
            [self.sample_contract_data[0]],
            self.existing_contract_ids,
            self.housekeeper_award_lists
        )

        record = result[0]

        # 验证新增字段的映射
        self.assertEqual(record['管家ID(serviceHousekeeperId)'], 'HK001')
        self.assertEqual(record['客户联系地址(contactsAddress)'], '上海市浦东新区张江路123号')
        self.assertEqual(record['项目地址(projectAddress)'], '上海市浦东新区科技园456号')

        # 验证活动编号
        self.assertEqual(record['活动编号'], 'SH-2025-09')

        # 验证通知状态
        self.assertEqual(record['是否发送通知'], 'N')

    def test_duplicate_contract_handling(self):
        """测试：重复合同处理"""
        from modules.data_processing_module import process_data_shanghai_sep

        # 设置已存在的合同ID
        existing_ids = {'SH001'}

        result = process_data_shanghai_sep(
            self.sample_contract_data,
            existing_ids,
            self.housekeeper_award_lists
        )

        # 应该只处理一条记录（SH002），跳过已存在的SH001
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['合同ID(_id)'], 'SH002')
        self.assertEqual(result[0]['工单类型'], '自引单')

if __name__ == '__main__':
    unittest.main()
