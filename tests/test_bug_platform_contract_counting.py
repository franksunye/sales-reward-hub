#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试：平台单计数BUG验证
验证节节高奖励计算时，合同计数应该只包含平台单，不应包含自引单
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPlatformContractCountingBug(unittest.TestCase):
    """测试平台单计数BUG"""
    
    def setUp(self):
        """测试前准备"""
        # 模拟混合订单数据：平台单和自引单交替
        self.mixed_contract_data = [
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
                '工单类型(sourceType)': 2,  # 平台单
                '项目地址(projectAddress)': '上海市浦东新区科技园456号',
                '管家ID(serviceHousekeeperId)': 'HK001',
                '客户联系地址(contactsAddress)': '上海市浦东新区张江路123号'
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
                '转化率(conversion)': '80%',
                '平均客单价(average)': '15000',
                '工单类型(sourceType)': 1,  # 自引单
                '项目地址(projectAddress)': '上海市浦东新区自引项目789号',
                '管家ID(serviceHousekeeperId)': 'HK001',
                '客户联系地址(contactsAddress)': '上海市浦东新区自引地址789号'
            },
            {
                '合同ID(_id)': 'SH003',
                '活动城市(province)': '上海',
                '工单编号(serviceAppointmentNum)': 'WO003',
                'Status': 'active',
                '管家(serviceHousekeeper)': '张三',
                '合同编号(contractdocNum)': 'CT003',
                '合同金额(adjustRefundMoney)': '30000',
                '支付金额(paidAmount)': '30000',
                '差额(difference)': '0',
                'State': 'valid',
                '创建时间(createTime)': '2025-09-03',
                '服务商(orgName)': '上海英森防水工程有限公司',
                '签约时间(signedDate)': '2025-09-03',
                'Doorsill': '10000',
                '款项来源类型(tradeIn)': 'type1',
                '转化率(conversion)': '90%',
                '平均客单价(average)': '30000',
                '工单类型(sourceType)': 2,  # 平台单
                '项目地址(projectAddress)': '上海市浦东新区科技园999号',
                '管家ID(serviceHousekeeperId)': 'HK001',
                '客户联系地址(contactsAddress)': '上海市浦东新区张江路999号'
            }
        ]
        
        self.existing_contract_ids = set()
        self.housekeeper_award_lists = {}
    
    def test_platform_contract_sequence_bug(self):
        """
        测试BUG：平台单奖励计算错误

        场景：处理顺序为 平台单1 -> 自引单1 -> 平台单2
        期望：第2个平台单的奖励计算应该基于2个平台单，不是3个总合同
        """
        from modules.data_processing_module import process_data_shanghai_sep
        
        result = process_data_shanghai_sep(
            self.mixed_contract_data,
            self.existing_contract_ids,
            self.housekeeper_award_lists
        )
        
        # 验证处理了3个合同
        self.assertEqual(len(result), 3, "应该处理3个合同")
        
        # 找到平台单记录
        platform_records = [r for r in result if r['工单类型'] == '平台单']
        self_referral_records = [r for r in result if r['工单类型'] == '自引单']
        
        self.assertEqual(len(platform_records), 2, "应该有2个平台单")
        self.assertEqual(len(self_referral_records), 1, "应该有1个自引单")
        
        # === 关键BUG验证 ===
        # 第1个平台单：活动期内第几个合同应该是1
        first_platform = platform_records[0]
        self.assertEqual(first_platform['合同ID(_id)'], 'SH001')
        
        # 第2个平台单：活动期内第几个合同应该是2（不是3！）
        second_platform = platform_records[1]
        self.assertEqual(second_platform['合同ID(_id)'], 'SH003')
        
        # 关键验证：检查奖励计算是否基于正确的平台单数量
        # 第2个平台单的奖励计算应该基于2个平台单，不是3个总合同

        # 验证奖励计算结果
        # 根据配置，节节高需要5个平台单，现在有2个平台单，应该显示"还需3单"
        print(f"第2个平台单备注: {second_platform['备注']}")

        # 验证奖励计算基于正确的平台单数量
        self.assertIn("还需 3 单", second_platform['备注'],
                     "第2个平台单的奖励计算应该基于2个平台单（5-2=3），不是3个总合同（5-3=2）")
    
    def test_platform_contract_reward_calculation_bug(self):
        """
        测试BUG：节节高奖励计算基于错误的合同计数
        
        验证节节高奖励计算时使用的合同数量是否正确
        """
        from modules.data_processing_module import process_data_shanghai_sep
        
        result = process_data_shanghai_sep(
            self.mixed_contract_data,
            self.existing_contract_ids,
            self.housekeeper_award_lists
        )
        
        # 找到第2个平台单
        platform_records = [r for r in result if r['工单类型'] == '平台单']
        second_platform = platform_records[1]
        
        # 检查备注信息（包含奖励计算逻辑）
        print(f"第2个平台单备注: {second_platform['备注']}")
        
        # 根据设计文档，节节高奖励需要5个平台单才能开始
        # 当前只有2个平台单，应该提示"还需3单"
        # 但如果计数包含自引单，可能会显示"还需2单"（错误）
        
        # 验证当前可能的错误行为
        if "还需 2 单" in second_platform['备注']:
            self.fail("BUG：节节高奖励计算包含了自引单计数，应该是'还需3单'而不是'还需2单'")

if __name__ == '__main__':
    unittest.main()
