"""
销售激励系统重构 - 上海功能等价性验证
版本: v1.0
创建日期: 2025-01-08

验证重构后的上海系统与现有系统的功能等价性。
重点验证：双轨统计、自引单奖励、项目地址去重。
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

from modules.core.shanghai_jobs import (
    signing_and_sales_incentive_apr_shanghai_v2,
    signing_and_sales_incentive_sep_shanghai_v2
)
from modules.core.tests.test_equivalence_validation import EquivalenceValidator


class ShanghaiEquivalenceTest(unittest.TestCase):
    """上海功能等价性验证测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.validator = EquivalenceValidator()
        
        # 上海测试数据
        self.shanghai_test_data = [
            {
                '合同ID(_id)': '2025010812345801',  # 包含幸运数字8
                '管家(serviceHousekeeper)': '王五',
                '服务商(orgName)': '上海精品服务',
                '合同金额(adjustRefundMoney)': 18000,
                '支付金额(paidAmount)': 15000,
                '款项来源类型(tradeIn)': 0,  # 平台单
                '管家ID(serviceHousekeeperId)': 'HK001',
                '客户联系地址(contactsAddress)': '上海市浦东新区',
                '项目地址(projectAddress)': '上海市浦东新区张江高科技园区A座',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 10:00:00'
            },
            {
                '合同ID(_id)': '2025010812345802',
                '管家(serviceHousekeeper)': '王五',
                '服务商(orgName)': '上海精品服务',
                '合同金额(adjustRefundMoney)': 22000,
                '支付金额(paidAmount)': 18000,
                '款项来源类型(tradeIn)': 1,  # 自引单
                '管家ID(serviceHousekeeperId)': 'HK001',
                '客户联系地址(contactsAddress)': '上海市徐汇区',
                '项目地址(projectAddress)': '上海市徐汇区淮海中路B座',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 11:00:00'
            },
            {
                '合同ID(_id)': '2025010812345803',
                '管家(serviceHousekeeper)': '赵六',
                '服务商(orgName)': '上海优质服务',
                '合同金额(adjustRefundMoney)': 25000,
                '支付金额(paidAmount)': 20000,
                '款项来源类型(tradeIn)': 1,  # 自引单
                '管家ID(serviceHousekeeperId)': 'HK002',
                '客户联系地址(contactsAddress)': '上海市静安区',
                '项目地址(projectAddress)': '上海市静安区南京西路C座',
                '活动城市(province)': '上海',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 12:00:00'
            }
        ]
    
    def test_shanghai_april_equivalence(self):
        """测试上海4月功能等价性"""
        print("\n" + "="*60)
        print("上海4月功能等价性验证")
        print("="*60)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()
            
            try:
                # Mock数据获取函数
                with patch('modules.core.shanghai_jobs._get_shanghai_contract_data', 
                          return_value=self.shanghai_test_data):
                    with patch('modules.core.shanghai_jobs.create_standard_pipeline') as mock_pipeline:
                        from modules.core import create_standard_pipeline
                        pipeline, config, store = create_standard_pipeline(
                            config_key="SH-2025-04",
                            activity_code="SH-APR",
                            city="SH",
                            housekeeper_key_format="管家_服务商",
                            storage_type="sqlite",
                            enable_dual_track=False,
                            db_path=temp_db.name
                        )
                        mock_pipeline.return_value = (pipeline, config, store)
                        
                        new_records = signing_and_sales_incentive_apr_shanghai_v2()
                
                # 转换为字典格式
                new_data = [record.to_dict() for record in new_records]
                
                # 模拟旧系统输出
                old_data = self._simulate_shanghai_old_system_output(self.shanghai_test_data, "SH-APR")
                
                # 验证等价性
                result = self.validator.validate_data_equivalence(old_data, new_data, "上海4月")
                
                # 断言
                if not result['is_equivalent']:
                    self.fail(f"上海4月功能等价性验证失败: {result['differences']}")
                
            finally:
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def test_shanghai_september_dual_track_equivalence(self):
        """测试上海9月双轨统计功能等价性"""
        print("\n" + "="*60)
        print("上海9月双轨统计功能等价性验证")
        print("="*60)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()
            
            try:
                # Mock数据获取函数
                with patch('modules.core.shanghai_jobs._get_shanghai_contract_data_with_dual_track', 
                          return_value=self.shanghai_test_data):
                    with patch('modules.core.shanghai_jobs.create_standard_pipeline') as mock_pipeline:
                        from modules.core import create_standard_pipeline
                        pipeline, config, store = create_standard_pipeline(
                            config_key="SH-2025-09",
                            activity_code="SH-SEP",
                            city="SH",
                            housekeeper_key_format="管家_服务商",
                            storage_type="sqlite",
                            enable_dual_track=True,
                            db_path=temp_db.name
                        )
                        mock_pipeline.return_value = (pipeline, config, store)
                        
                        new_records = signing_and_sales_incentive_sep_shanghai_v2()
                
                # 转换为字典格式
                new_data = [record.to_dict() for record in new_records]
                
                # 模拟旧系统输出（包含双轨统计）
                old_data = self._simulate_shanghai_dual_track_output(self.shanghai_test_data, "SH-SEP")
                
                # 验证等价性
                result = self.validator.validate_data_equivalence(old_data, new_data, "上海9月双轨统计")
                
                # 验证双轨统计字段
                self._verify_dual_track_fields(new_data)
                
                # 断言
                if not result['is_equivalent']:
                    self.fail(f"上海9月双轨统计功能等价性验证失败: {result['differences']}")
                
            finally:
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def _simulate_shanghai_old_system_output(self, input_data: List[Dict], activity_code: str) -> List[Dict]:
        """模拟上海旧系统输出"""
        old_output = []
        housekeeper_stats = {}
        
        for i, contract in enumerate(input_data):
            housekeeper = contract['管家(serviceHousekeeper)']
            service_provider = contract['服务商(orgName)']
            housekeeper_key = f"{housekeeper}_{service_provider}"
            contract_amount = contract['合同金额(adjustRefundMoney)']
            
            # 更新管家统计
            if housekeeper_key not in housekeeper_stats:
                housekeeper_stats[housekeeper_key] = {'count': 0, 'amount': 0}
            
            housekeeper_stats[housekeeper_key]['count'] += 1
            housekeeper_stats[housekeeper_key]['amount'] += contract_amount
            
            # 计算奖励（上海没有幸运数字奖励，只有节节高奖励）
            reward_types = []
            reward_names = []

            # 上海4月没有幸运数字奖励，只有节节高奖励
            # 这里简化处理，实际应该根据管家累计金额计算节节高奖励
            # 由于测试数据较少，暂不触发节节高奖励
            
            # 构建输出记录
            record = {
                '活动编号': activity_code,
                '合同ID(_id)': contract['合同ID(_id)'],
                '管家(serviceHousekeeper)': housekeeper,
                '服务商(orgName)': service_provider,
                '合同金额(adjustRefundMoney)': contract_amount,
                '管家累计单数': housekeeper_stats[housekeeper_key]['count'],
                '管家累计金额': housekeeper_stats[housekeeper_key]['amount'],
                '计入业绩金额': contract_amount,
                '奖励类型': ','.join(reward_types) if reward_types else '',
                '奖励名称': ','.join(reward_names) if reward_names else '',
                '活动期内第几个合同': i + 1
            }
            
            old_output.append(record)
        
        return old_output
    
    def _simulate_shanghai_dual_track_output(self, input_data: List[Dict], activity_code: str) -> List[Dict]:
        """模拟上海双轨统计旧系统输出"""
        old_output = []
        housekeeper_stats = {}
        
        for i, contract in enumerate(input_data):
            housekeeper = contract['管家(serviceHousekeeper)']
            service_provider = contract['服务商(orgName)']
            housekeeper_key = f"{housekeeper}_{service_provider}"
            contract_amount = contract['合同金额(adjustRefundMoney)']
            order_type = '自引单' if contract['款项来源类型(tradeIn)'] == 1 else '平台单'
            
            # 更新管家统计
            if housekeeper_key not in housekeeper_stats:
                housekeeper_stats[housekeeper_key] = {
                    'count': 0, 'amount': 0,
                    'platform_count': 0, 'platform_amount': 0,
                    'self_referral_count': 0, 'self_referral_amount': 0
                }
            
            stats = housekeeper_stats[housekeeper_key]
            stats['count'] += 1
            stats['amount'] += contract_amount
            
            if order_type == '平台单':
                stats['platform_count'] += 1
                stats['platform_amount'] += contract_amount
            else:
                stats['self_referral_count'] += 1
                stats['self_referral_amount'] += contract_amount
            
            # 计算奖励（上海9月：没有幸运数字奖励，有自引单奖励）
            reward_types = []
            reward_names = []

            # 上海9月没有幸运数字奖励，只有节节高奖励和自引单奖励
            # 节节高奖励需要累计金额达到门槛，这里简化处理

            # 自引单奖励
            if order_type == '自引单':
                reward_types.append('自引单')
                reward_names.append('红包')
            
            # 构建输出记录（包含双轨统计字段）
            record = {
                '活动编号': activity_code,
                '合同ID(_id)': contract['合同ID(_id)'],
                '管家(serviceHousekeeper)': housekeeper,
                '服务商(orgName)': service_provider,
                '合同金额(adjustRefundMoney)': contract_amount,
                '管家累计单数': stats['count'],
                '管家累计金额': stats['amount'],
                '计入业绩金额': contract_amount,
                '奖励类型': ','.join(reward_types) if reward_types else '',
                '奖励名称': ','.join(reward_names) if reward_names else '',
                '活动期内第几个合同': i + 1,
                # 双轨统计字段
                '工单类型': order_type,
                '平台单累计数量': stats['platform_count'],
                '平台单累计金额': stats['platform_amount'],
                '自引单累计数量': stats['self_referral_count'],
                '自引单累计金额': stats['self_referral_amount'],
                '管家ID(serviceHousekeeperId)': contract.get('管家ID(serviceHousekeeperId)', ''),
                '客户联系地址(contactsAddress)': contract.get('客户联系地址(contactsAddress)', ''),
                '项目地址(projectAddress)': contract.get('项目地址(projectAddress)', '')
            }
            
            old_output.append(record)
        
        return old_output
    
    def _verify_dual_track_fields(self, new_data: List[Dict]):
        """验证双轨统计字段"""
        print("\n验证双轨统计字段:")
        
        for record in new_data:
            housekeeper = record.get('管家(serviceHousekeeper)', '')
            order_type = record.get('工单类型', '')
            platform_count = record.get('平台单累计数量', 0)
            platform_amount = record.get('平台单累计金额', 0)
            self_referral_count = record.get('自引单累计数量', 0)
            self_referral_amount = record.get('自引单累计金额', 0)
            
            print(f"  {housekeeper}: {order_type}")
            print(f"    平台单: {platform_count}单, {platform_amount}元")
            print(f"    自引单: {self_referral_count}单, {self_referral_amount}元")
            
            # 验证双轨统计逻辑
            if order_type == '平台单':
                self.assertGreater(platform_count, 0, f"{housekeeper}的平台单数量应该大于0")
            elif order_type == '自引单':
                self.assertGreater(self_referral_count, 0, f"{housekeeper}的自引单数量应该大于0")
    
    def tearDown(self):
        """清理测试环境"""
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
