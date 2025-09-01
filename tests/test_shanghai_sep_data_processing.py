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

    def test_complete_field_calculation_first_time(self):
        """测试：完整字段计算验证 - 首次计算场景"""
        from modules.data_processing_module import process_data_shanghai_sep

        # 场景：首次处理，没有已存在合同
        result = process_data_shanghai_sep(
            [self.sample_contract_data[0]],  # 平台单
            set(),  # 没有已存在合同
            {}
        )

        self.assertEqual(len(result), 1, "应该处理1个合同")
        record = result[0]

        # === 基础字段验证 ===
        self.assertEqual(record['合同ID(_id)'], 'SH001')
        self.assertEqual(record['管家(serviceHousekeeper)'], '张三')
        self.assertEqual(record['服务商(orgName)'], '上海英森防水工程有限公司')
        self.assertEqual(record['合同金额(adjustRefundMoney)'], '25000')

        # === 新增字段验证 ===
        self.assertEqual(record['管家ID(serviceHousekeeperId)'], 'HK001')
        self.assertEqual(record['客户联系地址(contactsAddress)'], '上海市浦东新区张江路123号')
        self.assertEqual(record['项目地址(projectAddress)'], '上海市浦东新区科技园456号')
        self.assertEqual(record['活动编号'], 'SH-2025-09')
        self.assertEqual(record['工单类型'], '平台单')

        # === 累计计算字段验证（首次计算）===
        self.assertEqual(record['管家累计单数'], 1, "首次计算：累计单数应该是1")
        self.assertEqual(record['管家累计金额'], 25000, "首次计算：累计金额应该是25000")

        # === 分类统计字段验证 ===
        self.assertEqual(record['平台单累计数量'], 1, "平台单累计数量应该是1")
        self.assertEqual(record['平台单累计金额'], 25000.0, "平台单累计金额应该是25000")
        self.assertEqual(record['自引单累计数量'], 0, "自引单累计数量应该是0")
        self.assertEqual(record['自引单累计金额'], 0.0, "自引单累计金额应该是0")

        # === 奖励计算字段验证 ===
        # 平台单第1单，没有奖励
        self.assertEqual(record['奖励类型'], '', "第1个平台单没有奖励")
        self.assertEqual(record['奖励名称'], '', "第1个平台单没有奖励名称")
        self.assertEqual(record['激活奖励状态'], 0, "第1个平台单激活状态为0")

        # === 备注字段验证 ===
        self.assertIn("还需", record['备注'], "备注应该包含还需多少单的信息")

        # === 通知状态字段验证 ===
        self.assertEqual(record['是否发送通知'], 'N', "通知状态应该是N")

    def test_complete_field_calculation_incremental(self):
        """测试：完整字段计算验证 - 增量计算场景"""
        from modules.data_processing_module import process_data_shanghai_sep

        # 场景：增量处理，第1个合同已存在，处理第2个合同
        existing_contract_ids = {'SH001'}

        result = process_data_shanghai_sep(
            self.sample_contract_data,  # 包含SH001和SH002
            existing_contract_ids,
            {}
        )

        # 应该只返回1条新记录（SH002）
        self.assertEqual(len(result), 1, "增量计算：应该只为新合同创建记录")
        record = result[0]

        # === 基础字段验证 ===
        self.assertEqual(record['合同ID(_id)'], 'SH002', "应该是第2个合同")
        self.assertEqual(record['工单类型'], '自引单', "第2个合同是自引单")

        # === 累计计算字段验证（增量计算）===
        # 关键：累计数据应该包含已存在的第1个合同
        self.assertEqual(record['管家累计单数'], 2, "增量计算：累计单数应该是2（包含已存在合同）")
        self.assertEqual(record['管家累计金额'], 40000, "增量计算：累计金额应该是40000（25000+15000）")

        # === 分类统计字段验证（增量计算）===
        self.assertEqual(record['平台单累计数量'], 1, "平台单累计数量应该是1（来自已存在合同）")
        self.assertEqual(record['平台单累计金额'], 25000.0, "平台单累计金额应该是25000")
        self.assertEqual(record['自引单累计数量'], 1, "自引单累计数量应该是1（当前合同）")
        self.assertEqual(record['自引单累计金额'], 15000.0, "自引单累计金额应该是15000")

        # === 奖励计算字段验证（基于累计数据）===
        self.assertEqual(record['奖励类型'], '自引单', "自引单应该有奖励")
        self.assertEqual(record['奖励名称'], '红包', "自引单奖励名称应该是红包")
        self.assertEqual(record['激活奖励状态'], 1, "有奖励时激活状态为1")

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

    def test_real_data_complete_field_validation(self):
        """测试：真实数据完整字段验证 - 使用丁长勇的真实合同数据"""
        from modules.data_processing_module import process_data_shanghai_sep

        # 使用真实的丁长勇合同数据
        real_contracts = [
            {
                '合同ID(_id)': '1558405240220697121',  # 第1个合同
                '管家(serviceHousekeeper)': '丁长勇',
                '服务商(orgName)': '上海国坦装潢设计工程有限公司',
                '合同金额(adjustRefundMoney)': '9900',
                '支付金额(paidAmount)': '9900',
                '差额(difference)': '0',
                'Status': '1',
                'State': '1',
                '创建时间(createTime)': '2025-09-01T08:22:18.889+08:00',
                '签约时间(signedDate)': '2025-09-01T08:28:00.012+08:00',
                '工单编号(serviceAppointmentNum)': 'GD20250810446',
                '合同编号(contractdocNum)': 'YHWX-SH-GTZH-2025090001',
                '活动城市(province)': '310000',
                'Doorsill': '9900',
                '款项来源类型(tradeIn)': '1',
                '转化率(conversion)': '2.0',
                '平均客单价(average)': '7450.0',
                '管家ID(serviceHousekeeperId)': '7409250475944264684',
                '工单类型(sourceType)': 2,  # 平台单
                '客户联系地址(contactsAddress)': '上海市市辖区闵行区罗锦路888弄 上海阳城2支弄20号501',
                '项目地址(projectAddress)': '上海市市辖区闵行区罗锦路888弄 上海阳城2支弄20号501'
            },
            {
                '合同ID(_id)': '4323227372965152055',  # 第2个合同
                '管家(serviceHousekeeper)': '丁长勇',
                '服务商(orgName)': '上海国坦装潢设计工程有限公司',
                '合同金额(adjustRefundMoney)': '5000',
                '支付金额(paidAmount)': '5000',
                '差额(difference)': '0',
                'Status': '1',
                'State': '1',
                '创建时间(createTime)': '2025-09-01T09:31:31.127+08:00',
                '签约时间(signedDate)': '2025-09-01T09:38:15.544+08:00',
                '工单编号(serviceAppointmentNum)': 'GD20250900003',
                '合同编号(contractdocNum)': 'YHWX-SH-GTZH-2025090002',
                '活动城市(province)': '310000',
                'Doorsill': '5000',
                '款项来源类型(tradeIn)': '1',
                '转化率(conversion)': '2.0',
                '平均客单价(average)': '7450.0',
                '管家ID(serviceHousekeeperId)': '7409250475944264684',
                '工单类型(sourceType)': 2,  # 平台单
                '客户联系地址(contactsAddress)': '上海市市辖区浦东新区浦明路233弄3号1103',
                '项目地址(projectAddress)': '上海市市辖区浦东新区浦明路233弄3号1103'
            }
        ]

        # 测试增量计算：第1个合同已存在，处理第2个合同
        existing_contract_ids = {'1558405240220697121'}

        result = process_data_shanghai_sep(
            real_contracts,
            existing_contract_ids,
            {}
        )

        # 验证只返回1条新记录
        self.assertEqual(len(result), 1, "应该只为新合同创建记录")
        record = result[0]

        # === 验证所有关键计算字段 ===

        # 基础字段
        self.assertEqual(record['合同ID(_id)'], '4323227372965152055', "应该是第2个合同")
        self.assertEqual(record['管家(serviceHousekeeper)'], '丁长勇')
        self.assertEqual(record['合同金额(adjustRefundMoney)'], '5000')
        self.assertEqual(record['工单类型'], '平台单')
        self.assertEqual(record['活动编号'], 'SH-2025-09')

        # 累计计算字段（这是我们发现BUG的核心字段）
        self.assertEqual(record['管家累计单数'], 2, "累计单数：包含已存在的第1个合同")
        self.assertEqual(record['管家累计金额'], 14900, "累计金额：9900+5000=14900")

        # 分类统计字段
        self.assertEqual(record['平台单累计数量'], 2, "平台单累计数量：两个都是平台单")
        self.assertEqual(record['平台单累计金额'], 14900.0, "平台单累计金额：9900+5000")
        self.assertEqual(record['自引单累计数量'], 0, "自引单累计数量：都不是自引单")
        self.assertEqual(record['自引单累计金额'], 0.0, "自引单累计金额：都不是自引单")

        # 奖励计算字段（基于累计数据）
        # 2个合同，距离5个合同的节节高奖励还需3个
        self.assertIn("还需 3 单", record['备注'], "备注应该基于累计2个合同计算")

        # 通知状态
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

        # 应该只为新合同创建记录（SH002），但累计数据包含已存在的SH001
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['合同ID(_id)'], 'SH002')
        self.assertEqual(result[0]['工单类型'], '自引单')

        # 验证累计数据包含了已存在的合同
        self.assertEqual(result[0]['管家累计单数'], 2)  # 包含SH001和SH002
        self.assertEqual(result[0]['管家累计金额'], 40000)  # 25000 + 15000

if __name__ == '__main__':
    unittest.main()
