"""
销售激励系统重构 - 全面验证测试
版本: v1.0
创建日期: 2025-01-08

全面验证重构后系统的各种业务场景。
"""

import unittest
import tempfile
import os
import sys
from typing import Dict, List
from unittest.mock import patch

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core.beijing_jobs import (
    signing_and_sales_incentive_jun_beijing_v2,
    signing_and_sales_incentive_sep_beijing_v2
)
from modules.core.tests.test_equivalence_validation import EquivalenceValidator


class ComprehensiveValidationTest(unittest.TestCase):
    """全面验证测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.validator = EquivalenceValidator()
    
    def test_edge_cases(self):
        """测试边界情况"""
        print("\n" + "="*60)
        print("边界情况测试")
        print("="*60)
        
        # 边界测试数据
        edge_cases = [
            # 刚好达到门槛
            {
                '合同ID(_id)': '2025010812345681',
                '管家(serviceHousekeeper)': '边界测试1',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 10000,  # 刚好10000
                '支付金额(paidAmount)': 8000,
                '工单编号(serviceAppointmentNum)': 'WO-EDGE-001',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 10:00:00'
            },
            # 刚好不达门槛
            {
                '合同ID(_id)': '2025010812345682',
                '管家(serviceHousekeeper)': '边界测试2',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 9999,  # 刚好不到10000
                '支付金额(paidAmount)': 8000,
                '工单编号(serviceAppointmentNum)': 'WO-EDGE-002',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 11:00:00'
            },
            # 没有幸运数字
            {
                '合同ID(_id)': '2025010912345679',  # 没有8
                '管家(serviceHousekeeper)': '边界测试3',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 15000,
                '支付金额(paidAmount)': 12000,
                '工单编号(serviceAppointmentNum)': 'WO-EDGE-003',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 12:00:00'
            }
        ]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()
            
            try:
                # 测试北京6月
                with patch('modules.core.beijing_jobs._get_contract_data_from_metabase', 
                          return_value=edge_cases):
                    with patch('modules.core.beijing_jobs.create_standard_pipeline') as mock_pipeline:
                        from modules.core import create_standard_pipeline
                        pipeline, config, store = create_standard_pipeline(
                            config_key="BJ-2025-06",
                            activity_code="BJ-JUN",
                            city="BJ",
                            housekeeper_key_format="管家",
                            storage_type="sqlite",
                            enable_project_limit=True,
                            db_path=temp_db.name
                        )
                        mock_pipeline.return_value = (pipeline, config, store)
                        
                        records = signing_and_sales_incentive_jun_beijing_v2()
                
                print(f"边界情况处理结果: {len(records)} 条记录")
                
                # 验证边界情况
                for record in records:
                    contract_id = record.contract_data.contract_id
                    rewards = [r.reward_name for r in record.rewards]
                    amount = record.contract_data.contract_amount
                    
                    if contract_id == '2025010812345681':  # 刚好10000
                        self.assertIn('接好运万元以上', rewards, "刚好达到门槛应该获得高额奖励")
                        print(f"✅ {contract_id} (10000元): {rewards}")
                    elif contract_id == '2025010812345682':  # 9999
                        self.assertIn('接好运', rewards, "刚好不达门槛应该获得基础奖励")
                        self.assertNotIn('接好运万元以上', rewards, "不应该获得高额奖励")
                        print(f"✅ {contract_id} (9999元): {rewards}")
                    elif contract_id == '2025010912345679':  # 没有8
                        self.assertEqual(len(rewards), 0, "没有幸运数字不应该获得奖励")
                        print(f"✅ {contract_id} (无幸运数字): {rewards}")
                
            finally:
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def test_duplicate_handling(self):
        """测试去重处理"""
        print("\n" + "="*60)
        print("去重处理测试")
        print("="*60)
        
        # 包含重复合同ID的测试数据
        duplicate_data = [
            {
                '合同ID(_id)': '2025010812345688',
                '管家(serviceHousekeeper)': '去重测试',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 15000,
                '支付金额(paidAmount)': 12000,
                '工单编号(serviceAppointmentNum)': 'WO-DUP-001',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 10:00:00'
            },
            {
                '合同ID(_id)': '2025010812345688',  # 重复的合同ID
                '管家(serviceHousekeeper)': '去重测试',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 20000,  # 不同的金额
                '支付金额(paidAmount)': 16000,
                '工单编号(serviceAppointmentNum)': 'WO-DUP-002',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 11:00:00'
            }
        ]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()
            
            try:
                with patch('modules.core.beijing_jobs._get_contract_data_from_metabase', 
                          return_value=duplicate_data):
                    with patch('modules.core.beijing_jobs.create_standard_pipeline') as mock_pipeline:
                        from modules.core import create_standard_pipeline
                        pipeline, config, store = create_standard_pipeline(
                            config_key="BJ-2025-06",
                            activity_code="BJ-JUN",
                            city="BJ",
                            housekeeper_key_format="管家",
                            storage_type="sqlite",
                            enable_project_limit=True,
                            db_path=temp_db.name
                        )
                        mock_pipeline.return_value = (pipeline, config, store)
                        
                        records = signing_and_sales_incentive_jun_beijing_v2()
                
                # 应该只处理1条记录（去重）
                self.assertEqual(len(records), 1, "重复的合同ID应该被去重")
                print(f"✅ 去重测试通过: 输入2条重复记录，处理1条")
                
                # 验证处理的是第一条记录
                record = records[0]
                self.assertEqual(record.contract_data.contract_amount, 15000, "应该处理第一条记录")
                print(f"✅ 处理的记录金额: {record.contract_data.contract_amount}元")
                
            finally:
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def test_housekeeper_accumulation(self):
        """测试管家累计统计"""
        print("\n" + "="*60)
        print("管家累计统计测试")
        print("="*60)
        
        # 同一管家的多个合同
        accumulation_data = [
            {
                '合同ID(_id)': '2025010812345691',
                '管家(serviceHousekeeper)': '累计测试管家',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 8000,
                '支付金额(paidAmount)': 6000,
                '工单编号(serviceAppointmentNum)': 'WO-ACC-001',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 10:00:00'
            },
            {
                '合同ID(_id)': '2025010812345692',
                '管家(serviceHousekeeper)': '累计测试管家',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 12000,
                '支付金额(paidAmount)': 10000,
                '工单编号(serviceAppointmentNum)': 'WO-ACC-002',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 11:00:00'
            },
            {
                '合同ID(_id)': '2025010812345693',
                '管家(serviceHousekeeper)': '累计测试管家',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 15000,
                '支付金额(paidAmount)': 12000,
                '工单编号(serviceAppointmentNum)': 'WO-ACC-003',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 12:00:00'
            }
        ]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()
            
            try:
                with patch('modules.core.beijing_jobs._get_contract_data_from_metabase', 
                          return_value=accumulation_data):
                    with patch('modules.core.beijing_jobs.create_standard_pipeline') as mock_pipeline:
                        from modules.core import create_standard_pipeline
                        pipeline, config, store = create_standard_pipeline(
                            config_key="BJ-2025-06",
                            activity_code="BJ-JUN",
                            city="BJ",
                            housekeeper_key_format="管家",
                            storage_type="sqlite",
                            enable_project_limit=True,
                            db_path=temp_db.name
                        )
                        mock_pipeline.return_value = (pipeline, config, store)
                        
                        records = signing_and_sales_incentive_jun_beijing_v2()
                
                # 验证累计统计
                self.assertEqual(len(records), 3, "应该处理3条记录")
                
                expected_cumulative = [
                    (1, 8000.0),   # 第1个合同
                    (2, 20000.0),  # 第2个合同：8000 + 12000
                    (3, 35000.0)   # 第3个合同：8000 + 12000 + 15000
                ]
                
                for i, record in enumerate(records):
                    expected_count, expected_amount = expected_cumulative[i]
                    actual_count = record.housekeeper_stats.contract_count
                    actual_amount = record.housekeeper_stats.total_amount
                    
                    self.assertEqual(actual_count, expected_count, 
                                   f"第{i+1}个合同的累计单数应该是{expected_count}")
                    self.assertEqual(actual_amount, expected_amount, 
                                   f"第{i+1}个合同的累计金额应该是{expected_amount}")
                    
                    print(f"✅ 第{i+1}个合同: {actual_count}单, {actual_amount}元")
                
            finally:
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def tearDown(self):
        """清理测试环境"""
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
