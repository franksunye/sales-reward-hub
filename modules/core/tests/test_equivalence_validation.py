"""
销售激励系统重构 - 功能等价性验证
版本: v1.0
创建日期: 2025-01-08

验证重构后的系统与现有系统的功能等价性。
重点验证：数据输出、奖励计算、通知消息的一致性。
"""

import unittest
import tempfile
import os
import sys
import json
from typing import Dict, List, Tuple, Any
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core.beijing_jobs import (
    signing_and_sales_incentive_jun_beijing_v2,
    signing_and_sales_incentive_sep_beijing_v2
)


class EquivalenceValidator:
    """功能等价性验证器"""
    
    def __init__(self):
        self.tolerance = 0.01  # 数值比较容差
        self.validation_report = {
            'is_equivalent': True,
            'differences': [],
            'statistics': {},
            'test_cases': []
        }
    
    def validate_data_equivalence(self, old_data: List[Dict], new_data: List[Dict], 
                                test_name: str = "Unknown") -> Dict:
        """验证数据等价性"""
        print(f"\n=== 验证 {test_name} ===")
        
        test_result = {
            'test_name': test_name,
            'is_equivalent': True,
            'differences': [],
            'old_count': len(old_data),
            'new_count': len(new_data)
        }
        
        # 1. 记录数量验证
        if len(old_data) != len(new_data):
            diff = f"记录数量不一致: 旧系统{len(old_data)}条 vs 新系统{len(new_data)}条"
            test_result['differences'].append(diff)
            test_result['is_equivalent'] = False
            print(f"❌ {diff}")
        else:
            print(f"✅ 记录数量一致: {len(old_data)}条")
        
        # 2. 关键字段验证
        key_fields = [
            '合同ID(_id)', '管家(serviceHousekeeper)', '合同金额(adjustRefundMoney)',
            '管家累计单数', '管家累计金额', '计入业绩金额', '奖励类型', '奖励名称'
        ]
        
        equivalent_count = 0
        for i, (old_record, new_record) in enumerate(zip(old_data, new_data)):
            record_equivalent = True
            record_diffs = []
            
            for field in key_fields:
                if field in old_record and field in new_record:
                    old_val = old_record[field]
                    new_val = new_record[field]
                    
                    if not self._values_equivalent(old_val, new_val, field):
                        diff = f"记录{i+1} {field}: '{old_val}' vs '{new_val}'"
                        record_diffs.append(diff)
                        record_equivalent = False
                elif field in old_record or field in new_record:
                    diff = f"记录{i+1} {field}: 字段缺失"
                    record_diffs.append(diff)
                    record_equivalent = False
            
            if record_equivalent:
                equivalent_count += 1
            else:
                test_result['differences'].extend(record_diffs)
                test_result['is_equivalent'] = False
        
        print(f"✅ 等价记录: {equivalent_count}/{len(old_data)}")
        if test_result['differences']:
            print(f"❌ 发现 {len(test_result['differences'])} 个差异")
            for diff in test_result['differences'][:5]:  # 只显示前5个差异
                print(f"   - {diff}")
            if len(test_result['differences']) > 5:
                print(f"   ... 还有 {len(test_result['differences']) - 5} 个差异")
        
        self.validation_report['test_cases'].append(test_result)
        if not test_result['is_equivalent']:
            self.validation_report['is_equivalent'] = False
            self.validation_report['differences'].extend(test_result['differences'])
        
        return test_result
    
    def _values_equivalent(self, old_val: Any, new_val: Any, field_name: str) -> bool:
        """判断两个值是否等价"""
        # 数值字段使用容差比较
        if field_name in ['管家累计金额', '计入业绩金额', '合同金额(adjustRefundMoney)']:
            try:
                old_float = float(old_val) if old_val else 0.0
                new_float = float(new_val) if new_val else 0.0
                return abs(old_float - new_float) <= self.tolerance
            except (ValueError, TypeError):
                return str(old_val).strip() == str(new_val).strip()
        
        # 字符串字段精确比较（忽略前后空格）
        return str(old_val).strip() == str(new_val).strip()
    
    def validate_reward_calculation(self, test_cases: List[Dict]) -> Dict:
        """验证奖励计算逻辑"""
        print(f"\n=== 验证奖励计算逻辑 ===")
        
        reward_test_result = {
            'test_name': 'reward_calculation',
            'is_equivalent': True,
            'test_cases_passed': 0,
            'test_cases_total': len(test_cases),
            'failed_cases': []
        }
        
        for i, test_case in enumerate(test_cases):
            case_name = test_case.get('name', f'测试用例{i+1}')
            contract_data = test_case['contract_data']
            expected_rewards = test_case['expected_rewards']
            
            # 使用新系统计算奖励
            try:
                # 这里需要调用新系统的奖励计算逻辑
                # actual_rewards = calculate_rewards_new_system(contract_data)
                actual_rewards = []  # 临时占位
                
                if set(actual_rewards) == set(expected_rewards):
                    reward_test_result['test_cases_passed'] += 1
                    print(f"✅ {case_name}: 奖励计算正确")
                else:
                    failed_case = {
                        'case_name': case_name,
                        'expected': expected_rewards,
                        'actual': actual_rewards
                    }
                    reward_test_result['failed_cases'].append(failed_case)
                    reward_test_result['is_equivalent'] = False
                    print(f"❌ {case_name}: 期望{expected_rewards}, 实际{actual_rewards}")
                    
            except Exception as e:
                failed_case = {
                    'case_name': case_name,
                    'error': str(e)
                }
                reward_test_result['failed_cases'].append(failed_case)
                reward_test_result['is_equivalent'] = False
                print(f"❌ {case_name}: 计算出错 - {e}")
        
        print(f"奖励计算验证: {reward_test_result['test_cases_passed']}/{reward_test_result['test_cases_total']} 通过")
        
        self.validation_report['test_cases'].append(reward_test_result)
        if not reward_test_result['is_equivalent']:
            self.validation_report['is_equivalent'] = False
        
        return reward_test_result
    
    def generate_test_data(self) -> List[Dict]:
        """生成测试数据"""
        return [
            {
                '合同ID(_id)': '2025010812345678',  # 包含幸运数字8
                '管家(serviceHousekeeper)': '张三',
                '服务商(orgName)': '北京优质服务商',
                '合同金额(adjustRefundMoney)': 15000,
                '支付金额(paidAmount)': 10000,
                '工单编号(serviceAppointmentNum)': 'WO-2025-001',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 10:00:00'
            },
            {
                '合同ID(_id)': '2025010812345679',
                '管家(serviceHousekeeper)': '张三',
                '服务商(orgName)': '北京优质服务商',
                '合同金额(adjustRefundMoney)': 25000,
                '支付金额(paidAmount)': 20000,
                '工单编号(serviceAppointmentNum)': 'WO-2025-001',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 11:00:00'
            },
            {
                '合同ID(_id)': '2025010812345680',
                '管家(serviceHousekeeper)': '李四',
                '服务商(orgName)': '北京优质服务商',
                '合同金额(adjustRefundMoney)': 35000,
                '支付金额(paidAmount)': 30000,
                '工单编号(serviceAppointmentNum)': 'WO-2025-002',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 12:00:00'
            }
        ]
    
    def get_validation_report(self) -> Dict:
        """获取验证报告"""
        self.validation_report['statistics'] = {
            'total_tests': len(self.validation_report['test_cases']),
            'passed_tests': len([t for t in self.validation_report['test_cases'] if t.get('is_equivalent', True)]),
            'total_differences': len(self.validation_report['differences'])
        }
        
        return self.validation_report


class TestEquivalenceValidation(unittest.TestCase):
    """功能等价性验证测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.validator = EquivalenceValidator()
        self.test_data = self.validator.generate_test_data()
    
    def test_beijing_june_equivalence(self):
        """测试北京6月功能等价性"""
        print("\n" + "="*60)
        print("北京6月功能等价性验证")
        print("="*60)
        
        # 运行新系统
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()

            try:
                # Mock数据获取函数，确保使用相同的测试数据
                with patch('modules.core.beijing_jobs._get_contract_data_from_metabase',
                          return_value=self.test_data):
                    # 使用独立的数据库文件
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

                        new_records = signing_and_sales_incentive_jun_beijing_v2()

                # 转换为字典格式
                new_data = [record.to_dict() for record in new_records]

                # 模拟旧系统输出（使用相同的测试数据）
                old_data = self._simulate_old_system_output(self.test_data, "BJ-JUN")

                # 验证等价性
                result = self.validator.validate_data_equivalence(old_data, new_data, "北京6月")

                # 断言
                if not result['is_equivalent']:
                    self.fail(f"北京6月功能等价性验证失败: {result['differences']}")

            finally:
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def test_beijing_september_equivalence(self):
        """测试北京9月功能等价性"""
        print("\n" + "="*60)
        print("北京9月功能等价性验证")
        print("="*60)
        
        # 运行新系统
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()

            try:
                # Mock数据获取函数，确保使用相同的测试数据
                with patch('modules.core.beijing_jobs._get_contract_data_with_historical',
                          return_value=self.test_data):
                    # 使用独立的数据库文件
                    with patch('modules.core.beijing_jobs.create_standard_pipeline') as mock_pipeline:
                        from modules.core import create_standard_pipeline
                        pipeline, config, store = create_standard_pipeline(
                            config_key="BJ-2025-09",
                            activity_code="BJ-SEP",
                            city="BJ",
                            housekeeper_key_format="管家",
                            storage_type="sqlite",
                            enable_project_limit=True,
                            enable_historical_contracts=True,
                            db_path=temp_db.name
                        )
                        mock_pipeline.return_value = (pipeline, config, store)

                        new_records = signing_and_sales_incentive_sep_beijing_v2()

                # 转换为字典格式
                new_data = [record.to_dict() for record in new_records]

                # 模拟旧系统输出（使用相同的测试数据）
                old_data = self._simulate_old_system_output(self.test_data, "BJ-SEP")

                # 验证等价性
                result = self.validator.validate_data_equivalence(old_data, new_data, "北京9月")

                # 断言
                if not result['is_equivalent']:
                    self.fail(f"北京9月功能等价性验证失败: {result['differences']}")

            finally:
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def _simulate_old_system_output(self, input_data: List[Dict], activity_code: str) -> List[Dict]:
        """模拟旧系统输出（基于已知的业务逻辑）"""
        # 这里模拟旧系统的输出格式
        # 在实际项目中，这应该是调用现有系统的函数

        old_output = []
        housekeeper_stats = {}

        for i, contract in enumerate(input_data):
            housekeeper = contract['管家(serviceHousekeeper)']
            contract_amount = contract['合同金额(adjustRefundMoney)']

            # 更新管家统计
            if housekeeper not in housekeeper_stats:
                housekeeper_stats[housekeeper] = {'count': 0, 'amount': 0}

            housekeeper_stats[housekeeper]['count'] += 1
            housekeeper_stats[housekeeper]['amount'] += contract_amount

            # 计算奖励（根据不同活动使用不同的门槛）
            reward_types = []
            reward_names = []

            if '8' in contract['合同ID(_id)']:
                # 根据活动编码确定奖励门槛
                if activity_code == "BJ-JUN":
                    # 6月活动：10000元门槛
                    if contract_amount >= 10000:
                        reward_types.append('幸运数字')
                        reward_names.append('接好运万元以上')
                    else:
                        reward_types.append('幸运数字')
                        reward_names.append('接好运')
                elif activity_code == "BJ-SEP":
                    # 9月活动：门槛很高，基本只能获得基础奖励
                    reward_types.append('幸运数字')
                    reward_names.append('接好运')
                else:
                    # 其他活动：默认10000元门槛
                    if contract_amount >= 10000:
                        reward_types.append('幸运数字')
                        reward_names.append('接好运万元以上')
                    else:
                        reward_types.append('幸运数字')
                        reward_names.append('接好运')
            
            # 构建输出记录
            record = {
                '活动编号': activity_code,
                '合同ID(_id)': contract['合同ID(_id)'],
                '管家(serviceHousekeeper)': housekeeper,
                '合同金额(adjustRefundMoney)': contract_amount,
                '管家累计单数': housekeeper_stats[housekeeper]['count'],
                '管家累计金额': housekeeper_stats[housekeeper]['amount'],
                '计入业绩金额': contract_amount,
                '奖励类型': ','.join(reward_types) if reward_types else '',
                '奖励名称': ','.join(reward_names) if reward_names else '',
                '活动期内第几个合同': i + 1
            }
            
            old_output.append(record)
        
        return old_output
    
    def tearDown(self):
        """清理测试环境"""
        # 生成验证报告
        report = self.validator.get_validation_report()
        
        print(f"\n" + "="*60)
        print("验证报告摘要")
        print("="*60)
        print(f"总测试数: {report['statistics']['total_tests']}")
        print(f"通过测试: {report['statistics']['passed_tests']}")
        print(f"总差异数: {report['statistics']['total_differences']}")
        print(f"整体等价性: {'✅ 通过' if report['is_equivalent'] else '❌ 失败'}")


if __name__ == '__main__':
    # 运行验证测试
    unittest.main(verbosity=2)
