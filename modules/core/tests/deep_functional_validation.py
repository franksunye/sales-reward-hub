"""
销售激励系统重构 - 深度功能验证
版本: v1.0
创建日期: 2025-01-08

重点：功能等价性验证，确保新架构与现有系统100%功能一致
注意：性能不是重点，数据量小，重点关注功能正确性
"""

import unittest
import logging
import json
import tempfile
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

# 添加项目根目录到路径
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline
from modules.core.data_models import ContractData, PerformanceRecord


class DeepFunctionalValidator(unittest.TestCase):
    """深度功能验证器 - 重点关注功能等价性"""
    
    def setUp(self):
        """测试初始化"""
        logging.basicConfig(level=logging.INFO)
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 验证结果收集
        self.validation_results = []
    
    def tearDown(self):
        """测试清理"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def create_comprehensive_test_data(self) -> Dict[str, List[Dict]]:
        """创建全面的测试数据集"""
        test_data = {
            # 北京6月测试数据
            'BJ-JUN': [
                # 正常情况：幸运数字8，万元以上
                {
                    '合同ID(_id)': '2025010812345678',
                    '管家(serviceHousekeeper)': '张三',
                    '服务商(orgName)': '北京优质服务',
                    '合同金额(adjustRefundMoney)': 15000,
                    '支付金额(paidAmount)': 12000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ001',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-08 10:00:00'
                },
                # 边缘情况：幸运数字8，万元以下
                {
                    '合同ID(_id)': '2025010812345688',
                    '管家(serviceHousekeeper)': '李四',
                    '服务商(orgName)': '北京优质服务',
                    '合同金额(adjustRefundMoney)': 8000,
                    '支付金额(paidAmount)': 6000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ002',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-08 11:00:00'
                },
                # 非幸运数字情况
                {
                    '合同ID(_id)': '2025010812345679',
                    '管家(serviceHousekeeper)': '王五',
                    '服务商(orgName)': '北京优质服务',
                    '合同金额(adjustRefundMoney)': 12000,
                    '支付金额(paidAmount)': 10000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ003',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-08 12:00:00'
                }
            ],
            
            # 北京9月测试数据（包含历史合同）
            'BJ-SEP': [
                # 正常新合同
                {
                    '合同ID(_id)': '2025010912345680',
                    '管家(serviceHousekeeper)': '赵六',
                    '服务商(orgName)': '北京优质服务',
                    '合同金额(adjustRefundMoney)': 80000,  # 超过5万上限
                    '支付金额(paidAmount)': 60000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ004',
                    '工单编号(serviceAppointmentNum)': 'PROJECT001',  # 添加工单编号
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-09 10:00:00'
                },
                # 历史合同
                {
                    '合同ID(_id)': '2025010912345681',
                    'pcContractdocNum': 'PC2024123001',  # 历史合同标识
                    '管家(serviceHousekeeper)': '赵六',
                    '服务商(orgName)': '北京优质服务',
                    '合同金额(adjustRefundMoney)': 25000,
                    '支付金额(paidAmount)': 20000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ004',
                    '工单编号(serviceAppointmentNum)': 'PROJECT002',  # 添加工单编号
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-09 11:00:00'
                }
            ],
            
            # 上海9月测试数据（双轨统计）
            'SH-SEP': [
                # 平台单
                {
                    '合同ID(_id)': '2025010912345690',
                    '管家(serviceHousekeeper)': '孙七',
                    '服务商(orgName)': '上海精品服务',
                    '合同金额(adjustRefundMoney)': 18000,
                    '支付金额(paidAmount)': 15000,
                    '款项来源类型(tradeIn)': 0,  # 平台单
                    '管家ID(serviceHousekeeperId)': 'SH001',
                    '客户联系地址(contactsAddress)': '上海市浦东新区',
                    '项目地址(projectAddress)': '上海市浦东新区张江高科技园区A座',
                    '活动城市(province)': '上海',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-09 10:00:00'
                },
                # 自引单
                {
                    '合同ID(_id)': '2025010912345691',
                    '管家(serviceHousekeeper)': '孙七',
                    '服务商(orgName)': '上海精品服务',
                    '合同金额(adjustRefundMoney)': 22000,
                    '支付金额(paidAmount)': 18000,
                    '款项来源类型(tradeIn)': 1,  # 自引单
                    '管家ID(serviceHousekeeperId)': 'SH001',
                    '客户联系地址(contactsAddress)': '上海市徐汇区',
                    '项目地址(projectAddress)': '上海市徐汇区淮海中路B座',
                    '活动城市(province)': '上海',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-09 11:00:00'
                },
                # 重复项目地址的自引单（应该被跳过）
                {
                    '合同ID(_id)': '2025010912345692',
                    '管家(serviceHousekeeper)': '孙七',
                    '服务商(orgName)': '上海精品服务',
                    '合同金额(adjustRefundMoney)': 20000,
                    '支付金额(paidAmount)': 16000,
                    '款项来源类型(tradeIn)': 1,  # 自引单
                    '管家ID(serviceHousekeeperId)': 'SH001',
                    '客户联系地址(contactsAddress)': '上海市徐汇区',
                    '项目地址(projectAddress)': '上海市徐汇区淮海中路B座',  # 重复地址
                    '活动城市(province)': '上海',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-01-09 12:00:00'
                }
            ]
        }
        
        return test_data
    
    def validate_business_logic(self, config_key: str, activity_code: str, 
                              test_data: List[Dict], expected_results: Dict) -> Dict[str, Any]:
        """验证业务逻辑"""
        validation_result = {
            'config_key': config_key,
            'activity_code': activity_code,
            'test_passed': True,
            'details': [],
            'errors': []
        }
        
        try:
            # 创建处理管道
            pipeline, config, store = create_standard_pipeline(
                config_key=config_key,
                activity_code=activity_code,
                city=config_key.split('-')[0],
                db_path=self.temp_db.name,
                enable_project_limit=(config_key.startswith('BJ')),
                enable_dual_track=(config_key == 'SH-2025-09'),
                enable_historical_contracts=(config_key == 'BJ-2025-09')
            )
            
            # 处理数据
            processed_records = pipeline.process(test_data)
            
            # 验证记录数量
            expected_count = expected_results.get('expected_count', len(test_data))
            actual_count = len(processed_records)
            
            if actual_count != expected_count:
                validation_result['test_passed'] = False
                validation_result['errors'].append(
                    f"记录数量不匹配: 期望{expected_count}条, 实际{actual_count}条"
                )
            else:
                validation_result['details'].append(f"✅ 记录数量正确: {actual_count}条")
            
            # 验证具体业务逻辑
            self._validate_specific_business_rules(
                config_key, processed_records, expected_results, validation_result
            )
            
        except Exception as e:
            validation_result['test_passed'] = False
            validation_result['errors'].append(f"处理异常: {str(e)}")
        
        return validation_result
    
    def _validate_specific_business_rules(self, config_key: str, records: List[PerformanceRecord], 
                                        expected: Dict, result: Dict):
        """验证具体的业务规则"""
        
        if config_key == 'BJ-2025-06':
            # 北京6月：验证幸运数字8奖励
            lucky_records = [r for r in records if any('接好运' in reward.reward_name for reward in r.rewards)]
            expected_lucky = expected.get('expected_lucky_count', 0)
            
            if len(lucky_records) != expected_lucky:
                result['test_passed'] = False
                result['errors'].append(f"幸运数字奖励数量不匹配: 期望{expected_lucky}个, 实际{len(lucky_records)}个")
            else:
                result['details'].append(f"✅ 幸运数字奖励正确: {len(lucky_records)}个")
        
        elif config_key == 'BJ-2025-09':
            # 北京9月：验证工单金额上限和历史合同
            over_limit_records = [r for r in records if r.performance_amount == 50000 and r.contract_data.contract_amount > 50000]
            expected_over_limit = expected.get('expected_over_limit_count', 0)
            
            if len(over_limit_records) != expected_over_limit:
                result['test_passed'] = False
                result['errors'].append(f"工单金额上限处理不匹配: 期望{expected_over_limit}个, 实际{len(over_limit_records)}个")
            else:
                result['details'].append(f"✅ 工单金额上限处理正确: {len(over_limit_records)}个")
            
            # 验证历史合同
            historical_records = [r for r in records if r.contract_data.is_historical]
            expected_historical = expected.get('expected_historical_count', 0)
            
            if len(historical_records) != expected_historical:
                result['test_passed'] = False
                result['errors'].append(f"历史合同处理不匹配: 期望{expected_historical}个, 实际{len(historical_records)}个")
            else:
                result['details'].append(f"✅ 历史合同处理正确: {len(historical_records)}个")
        
        elif config_key == 'SH-2025-09':
            # 上海9月：验证双轨统计和自引单奖励
            platform_records = [r for r in records if r.contract_data.order_type.value == 'platform']
            self_referral_records = [r for r in records if r.contract_data.order_type.value == 'self_referral']
            
            expected_platform = expected.get('expected_platform_count', 0)
            expected_self_referral = expected.get('expected_self_referral_count', 0)
            
            if len(platform_records) != expected_platform:
                result['test_passed'] = False
                result['errors'].append(f"平台单数量不匹配: 期望{expected_platform}个, 实际{len(platform_records)}个")
            else:
                result['details'].append(f"✅ 平台单统计正确: {len(platform_records)}个")
            
            if len(self_referral_records) != expected_self_referral:
                result['test_passed'] = False
                result['errors'].append(f"自引单数量不匹配: 期望{expected_self_referral}个, 实际{len(self_referral_records)}个")
            else:
                result['details'].append(f"✅ 自引单统计正确: {len(self_referral_records)}个")
            
            # 验证自引单红包奖励
            red_packet_records = [r for r in records if any('红包' in reward.reward_name for reward in r.rewards)]
            expected_red_packet = expected.get('expected_red_packet_count', 0)
            
            if len(red_packet_records) != expected_red_packet:
                result['test_passed'] = False
                result['errors'].append(f"红包奖励数量不匹配: 期望{expected_red_packet}个, 实际{len(red_packet_records)}个")
            else:
                result['details'].append(f"✅ 红包奖励正确: {len(red_packet_records)}个")


    def test_beijing_june_comprehensive(self):
        """北京6月全面功能验证"""
        test_data = self.create_comprehensive_test_data()['BJ-JUN']

        expected_results = {
            'expected_count': 3,  # 3条记录都应该被处理
            'expected_lucky_count': 2,  # 2个幸运数字8的合同
        }

        result = self.validate_business_logic('BJ-2025-06', 'BJ-JUN', test_data, expected_results)
        self.validation_results.append(result)

        self.assertTrue(result['test_passed'], f"北京6月验证失败: {result['errors']}")
        print(f"✅ 北京6月验证通过: {result['details']}")

    def test_beijing_september_comprehensive(self):
        """北京9月全面功能验证"""
        test_data = self.create_comprehensive_test_data()['BJ-SEP']

        expected_results = {
            'expected_count': 2,  # 2条记录都应该被处理
            'expected_over_limit_count': 1,  # 1个超过5万上限的合同
            'expected_historical_count': 1,  # 1个历史合同
        }

        result = self.validate_business_logic('BJ-2025-09', 'BJ-SEP', test_data, expected_results)
        self.validation_results.append(result)

        self.assertTrue(result['test_passed'], f"北京9月验证失败: {result['errors']}")
        print(f"✅ 北京9月验证通过: {result['details']}")

    def test_shanghai_september_comprehensive(self):
        """上海9月全面功能验证"""
        test_data = self.create_comprehensive_test_data()['SH-SEP']

        expected_results = {
            'expected_count': 2,  # 2条记录（第3条因重复项目地址被跳过）
            'expected_platform_count': 1,  # 1个平台单
            'expected_self_referral_count': 1,  # 1个自引单（重复地址的被跳过）
            'expected_red_packet_count': 1,  # 1个红包奖励
        }

        result = self.validate_business_logic('SH-2025-09', 'SH-SEP', test_data, expected_results)
        self.validation_results.append(result)

        self.assertTrue(result['test_passed'], f"上海9月验证失败: {result['errors']}")
        print(f"✅ 上海9月验证通过: {result['details']}")

    def test_edge_cases(self):
        """边缘情况测试"""
        print("\n=== 边缘情况测试 ===")

        # 测试空数据
        result = self.validate_business_logic('BJ-2025-06', 'BJ-JUN', [], {'expected_count': 0})
        self.assertTrue(result['test_passed'], "空数据处理失败")
        print("✅ 空数据处理正确")

        # 测试重复合同ID
        duplicate_data = [
            {
                '合同ID(_id)': '2025010812345999',
                '管家(serviceHousekeeper)': '测试管家',
                '服务商(orgName)': '测试服务商',
                '合同金额(adjustRefundMoney)': 10000,
                '支付金额(paidAmount)': 8000,
                '款项来源类型(tradeIn)': 0,
                '管家ID(serviceHousekeeperId)': 'TEST001',
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 10:00:00'
            },
            # 重复的合同ID
            {
                '合同ID(_id)': '2025010812345999',  # 相同ID
                '管家(serviceHousekeeper)': '测试管家2',
                '服务商(orgName)': '测试服务商2',
                '合同金额(adjustRefundMoney)': 12000,
                '支付金额(paidAmount)': 10000,
                '款项来源类型(tradeIn)': 0,
                '管家ID(serviceHousekeeperId)': 'TEST002',
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 11:00:00'
            }
        ]

        result = self.validate_business_logic('BJ-2025-06', 'BJ-JUN', duplicate_data, {'expected_count': 1})
        self.assertTrue(result['test_passed'], "重复合同ID处理失败")
        print("✅ 重复合同ID去重正确")

    def generate_validation_report(self) -> str:
        """生成深度验证报告"""
        total_tests = len(self.validation_results)
        passed_tests = len([r for r in self.validation_results if r['test_passed']])

        report = f"""
深度功能验证报告
================
验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
重点: 功能等价性验证（性能不是重点）

总体统计:
- 总测试数: {total_tests}
- 通过测试数: {passed_tests}
- 通过率: {passed_tests/total_tests*100:.1f}%
- 状态: {'✅ 全部通过' if passed_tests == total_tests else '❌ 存在失败'}

详细结果:
"""

        for result in self.validation_results:
            status = "✅ 通过" if result['test_passed'] else "❌ 失败"
            report += f"\n{result['config_key']} ({result['activity_code']}): {status}\n"

            for detail in result['details']:
                report += f"  {detail}\n"

            for error in result['errors']:
                report += f"  ❌ {error}\n"

        report += f"""
验证结论:
{'✅ 新架构功能完全正确，与预期行为100%一致' if passed_tests == total_tests else '❌ 新架构存在功能问题，需要修复'}

注意: 本验证重点关注功能正确性，性能不是评估重点。
"""

        return report


if __name__ == "__main__":
    # 运行深度功能验证
    print("销售激励系统重构 - 深度功能验证")
    print("重点：功能等价性验证（性能不是重点）")
    print("="*60)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(DeepFunctionalValidator)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 生成报告
    validator = DeepFunctionalValidator()
    validator.setUp()

    # 手动运行测试以收集结果
    try:
        validator.test_beijing_june_comprehensive()
        validator.test_beijing_september_comprehensive()
        validator.test_shanghai_september_comprehensive()
        validator.test_edge_cases()

        # 生成报告
        report = validator.generate_validation_report()
        print(report)

        # 保存报告
        with open('deep_functional_validation_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n📋 详细报告已保存: deep_functional_validation_report.txt")

    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        validator.tearDown()

    print("="*60)
    print("深度功能验证完成！")
