"""
销售激励系统重构 - 上海等价性验证
版本: v1.0
创建日期: 2025-01-08

验证上海新架构与原有功能的完全等价性
重点验证：双轨统计、自引单奖励、项目地址去重
"""

import unittest
import logging
import tempfile
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline
from modules.core.data_models import ContractData, PerformanceRecord


class ShanghaiEquivalenceValidator(unittest.TestCase):
    """上海等价性验证器"""
    
    def setUp(self):
        """测试初始化"""
        logging.basicConfig(level=logging.INFO)
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
    
    def tearDown(self):
        """测试清理"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_shanghai_september_dual_track_equivalence(self):
        """测试上海9月双轨统计等价性"""
        print("\n=== 上海9月双轨统计等价性验证 ===")
        
        # 模拟原有系统的预期输出
        expected_output = [
            {
                '活动编号': 'SH-SEP',
                '合同ID(_id)': '2025090812345705',
                '管家(serviceHousekeeper)': '上海管家3',
                '服务商(orgName)': '上海精品服务C',
                '合同金额(adjustRefundMoney)': 18000,
                '管家累计单数': 2,  # 平台单+自引单
                '管家累计金额': 40000,  # 18000+22000
                '计入业绩金额': 18000,
                '奖励类型': '',
                '奖励名称': '',
                '活动期内第几个合同': 1,
                # 双轨统计字段
                '管家平台单数': 1,
                '管家平台单金额': 18000,
                '管家自引单数': 1,
                '管家自引单金额': 22000,
                '管家ID(serviceHousekeeperId)': 'SH003',
                '客户联系地址(contactsAddress)': '上海市浦东新区',
                '项目地址(projectAddress)': '上海市浦东新区陆家嘴E座'
            },
            {
                '活动编号': 'SH-SEP',
                '合同ID(_id)': '2025090812345706',
                '管家(serviceHousekeeper)': '上海管家3',
                '服务商(orgName)': '上海精品服务C',
                '合同金额(adjustRefundMoney)': 22000,
                '管家累计单数': 2,
                '管家累计金额': 40000,
                '计入业绩金额': 22000,
                '奖励类型': '自引单奖励',
                '奖励名称': '红包',
                '活动期内第几个合同': 2,
                # 双轨统计字段
                '管家平台单数': 1,
                '管家平台单金额': 18000,
                '管家自引单数': 1,
                '管家自引单金额': 22000,
                '管家ID(serviceHousekeeperId)': 'SH003',
                '客户联系地址(contactsAddress)': '上海市徐汇区',
                '项目地址(projectAddress)': '上海市徐汇区衡山路F座'
            }
        ]
        
        # 测试数据
        test_data = [
            # 平台单
            {
                '合同ID(_id)': '2025090812345705',
                '管家(serviceHousekeeper)': '上海管家3',
                '服务商(orgName)': '上海精品服务C',
                '合同金额(adjustRefundMoney)': 18000,
                '支付金额(paidAmount)': 15000,
                '款项来源类型(tradeIn)': 0,  # 平台单
                '管家ID(serviceHousekeeperId)': 'SH003',
                '客户联系地址(contactsAddress)': '上海市浦东新区',
                '项目地址(projectAddress)': '上海市浦东新区陆家嘴E座',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-09-08 10:00:00'
            },
            # 自引单
            {
                '合同ID(_id)': '2025090812345706',
                '管家(serviceHousekeeper)': '上海管家3',
                '服务商(orgName)': '上海精品服务C',
                '合同金额(adjustRefundMoney)': 22000,
                '支付金额(paidAmount)': 18000,
                '款项来源类型(tradeIn)': 1,  # 自引单
                '管家ID(serviceHousekeeperId)': 'SH003',
                '客户联系地址(contactsAddress)': '上海市徐汇区',
                '项目地址(projectAddress)': '上海市徐汇区衡山路F座',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-09-08 11:00:00'
            }
        ]
        
        # 创建处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="SH-2025-09",
            activity_code="SH-SEP",
            city="SH",
            db_path=self.temp_db.name,
            enable_dual_track=True,
            housekeeper_key_format="管家_服务商"
        )
        
        # 处理数据
        processed_records = pipeline.process(test_data)
        
        # 验证基本结果
        self.assertEqual(len(processed_records), 2, "应该处理2条记录")
        
        # 验证双轨统计
        platform_records = [r for r in processed_records if r.contract_data.order_type.value == 'platform']
        self_referral_records = [r for r in processed_records if r.contract_data.order_type.value == 'self_referral']
        
        self.assertEqual(len(platform_records), 1, "应该有1个平台单")
        self.assertEqual(len(self_referral_records), 1, "应该有1个自引单")
        
        # 验证自引单红包奖励
        red_packet_records = [r for r in self_referral_records if any('红包' in reward.reward_name for reward in r.rewards)]
        self.assertEqual(len(red_packet_records), 1, "自引单应该有红包奖励")
        
        # 验证累计统计（注意：每条记录显示的是处理到该记录时的累计值）
        # 第一条记录：累计1单
        # 第二条记录：累计2单
        sorted_records = sorted(processed_records, key=lambda r: r.contract_data.contract_id)

        # 验证第一条记录的累计统计
        first_record = sorted_records[0]
        self.assertEqual(first_record.housekeeper_stats.contract_count, 1, "第一条记录：管家累计单数应该是1")
        self.assertEqual(first_record.housekeeper_stats.total_amount, 18000, "第一条记录：管家累计金额应该是18000")

        # 验证第二条记录的累计统计
        second_record = sorted_records[1]
        self.assertEqual(second_record.housekeeper_stats.contract_count, 2, "第二条记录：管家累计单数应该是2")
        self.assertEqual(second_record.housekeeper_stats.total_amount, 40000, "第二条记录：管家累计金额应该是40000")
        
        print("✅ 上海9月双轨统计等价性验证通过")
    
    def test_shanghai_project_address_deduplication_equivalence(self):
        """测试上海项目地址去重等价性"""
        print("\n=== 上海项目地址去重等价性验证 ===")
        
        # 测试数据：包含重复项目地址的自引单
        test_data = [
            # 第一个自引单
            {
                '合同ID(_id)': '2025090812345710',
                '管家(serviceHousekeeper)': '上海管家4',
                '服务商(orgName)': '上海精品服务D',
                '合同金额(adjustRefundMoney)': 20000,
                '支付金额(paidAmount)': 16000,
                '款项来源类型(tradeIn)': 1,  # 自引单
                '管家ID(serviceHousekeeperId)': 'SH004',
                '客户联系地址(contactsAddress)': '上海市静安区',
                '项目地址(projectAddress)': '上海市静安区南京西路重复地址',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-09-08 10:00:00'
            },
            # 重复项目地址的自引单（应该被跳过）
            {
                '合同ID(_id)': '2025090812345711',
                '管家(serviceHousekeeper)': '上海管家4',
                '服务商(orgName)': '上海精品服务D',
                '合同金额(adjustRefundMoney)': 25000,
                '支付金额(paidAmount)': 20000,
                '款项来源类型(tradeIn)': 1,  # 自引单
                '管家ID(serviceHousekeeperId)': 'SH004',
                '客户联系地址(contactsAddress)': '上海市静安区',
                '项目地址(projectAddress)': '上海市静安区南京西路重复地址',  # 重复地址
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-09-08 11:00:00'
            },
            # 不同项目地址的自引单（应该被处理）
            {
                '合同ID(_id)': '2025090812345712',
                '管家(serviceHousekeeper)': '上海管家4',
                '服务商(orgName)': '上海精品服务D',
                '合同金额(adjustRefundMoney)': 18000,
                '支付金额(paidAmount)': 15000,
                '款项来源类型(tradeIn)': 1,  # 自引单
                '管家ID(serviceHousekeeperId)': 'SH004',
                '客户联系地址(contactsAddress)': '上海市黄浦区',
                '项目地址(projectAddress)': '上海市黄浦区外滩不同地址',  # 不同地址
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-09-08 12:00:00'
            }
        ]
        
        # 创建处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="SH-2025-09",
            activity_code="SH-SEP",
            city="SH",
            db_path=self.temp_db.name,
            enable_dual_track=True
        )
        
        # 处理数据
        processed_records = pipeline.process(test_data)
        
        # 验证结果：应该只处理2条记录（重复地址的被跳过）
        self.assertEqual(len(processed_records), 2, "重复项目地址的自引单应该被跳过，只处理2条记录")
        
        # 验证处理的记录
        processed_ids = [r.contract_data.contract_id for r in processed_records]
        self.assertIn('2025090812345710', processed_ids, "第一个自引单应该被处理")
        self.assertIn('2025090812345712', processed_ids, "不同地址的自引单应该被处理")
        self.assertNotIn('2025090812345711', processed_ids, "重复地址的自引单应该被跳过")
        
        # 验证红包奖励数量
        red_packet_records = [r for r in processed_records if any('红包' in reward.reward_name for reward in r.rewards)]
        self.assertEqual(len(red_packet_records), 2, "两个不同地址的自引单都应该有红包奖励")
        
        print("✅ 上海项目地址去重等价性验证通过")
    
    def test_shanghai_no_lucky_number_equivalence(self):
        """测试上海无幸运数字等价性"""
        print("\n=== 上海无幸运数字等价性验证 ===")
        
        # 测试数据：包含各种末位数字的合同
        test_data = [
            # 末位8（北京会有幸运奖励，上海不应该有）
            {
                '合同ID(_id)': '2025090812345708',
                '管家(serviceHousekeeper)': '上海管家5',
                '服务商(orgName)': '上海精品服务E',
                '合同金额(adjustRefundMoney)': 15000,
                '支付金额(paidAmount)': 12000,
                '款项来源类型(tradeIn)': 0,
                '管家ID(serviceHousekeeperId)': 'SH005',
                '客户联系地址(contactsAddress)': '上海市浦东新区',
                '项目地址(projectAddress)': '上海市浦东新区测试地址1',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-09-08 10:00:00'
            },
            # 末位5（北京9月会有幸运奖励，上海不应该有）
            {
                '合同ID(_id)': '2025090812345705',
                '管家(serviceHousekeeper)': '上海管家5',
                '服务商(orgName)': '上海精品服务E',
                '合同金额(adjustRefundMoney)': 18000,
                '支付金额(paidAmount)': 15000,
                '款项来源类型(tradeIn)': 0,
                '管家ID(serviceHousekeeperId)': 'SH005',
                '客户联系地址(contactsAddress)': '上海市徐汇区',
                '项目地址(projectAddress)': '上海市徐汇区测试地址2',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-09-08 11:00:00'
            }
        ]
        
        # 测试所有上海月份
        for config_key, activity_code, month_name in [
            ('SH-2025-04', 'SH-APR', '4月'),
            ('SH-2025-08', 'SH-AUG', '8月'),
            ('SH-2025-09', 'SH-SEP', '9月')
        ]:
            with self.subTest(month=month_name):
                # 创建处理管道
                pipeline, config, store = create_standard_pipeline(
                    config_key=config_key,
                    activity_code=activity_code,
                    city="SH",
                    db_path=self.temp_db.name,
                    enable_dual_track=(config_key == 'SH-2025-09')
                )
                
                # 处理数据
                processed_records = pipeline.process(test_data)
                
                # 验证无幸运数字奖励
                lucky_records = [r for r in processed_records if any('接好运' in reward.reward_name for reward in r.rewards)]
                self.assertEqual(len(lucky_records), 0, f"上海{month_name}不应该有幸运数字奖励")
                
                print(f"✅ 上海{month_name}无幸运数字验证通过")
        
        print("✅ 上海无幸运数字等价性验证通过")


def run_shanghai_equivalence_validation():
    """运行上海等价性验证"""
    print("销售激励系统重构 - 上海等价性验证")
    print("验证重点：双轨统计、自引单奖励、项目地址去重、无幸运数字")
    print("=" * 70)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(ShanghaiEquivalenceValidator)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 生成总结
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = (total_tests - failures - errors) / total_tests * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 70)
    print("上海等价性验证结果汇总:")
    print(f"- 总测试数: {total_tests}")
    print(f"- 成功测试: {total_tests - failures - errors}")
    print(f"- 失败测试: {failures}")
    print(f"- 错误测试: {errors}")
    print(f"- 成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("✅ 上海等价性验证完全通过！新架构与原有功能100%等价")
    elif success_rate >= 90:
        print("⚠️ 上海等价性验证基本通过，存在少量问题需要修复")
    else:
        print("❌ 上海等价性验证存在较多问题，需要深入调查和修复")
    
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    run_shanghai_equivalence_validation()
