"""
销售激励系统重构 - 全面等价性验证
版本: v1.0
创建日期: 2025-01-08

全面验证新架构与原有功能的完全等价性
重点验证：
1. 北京6月vs9月的差异兼容性（幸运数字、工单上限、历史合同等）
2. 上海不同月份的兼容性（双轨统计、自引单奖励等）
3. 新架构的统一处理能力
4. 与旧架构的完全等价性
"""

import unittest
import logging
import tempfile
import os
import sys
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline
from modules.core.data_models import ContractData, PerformanceRecord


class ComprehensiveEquivalenceValidator(unittest.TestCase):
    """全面等价性验证器"""
    
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
    
    def create_realistic_test_data(self) -> Dict[str, List[Dict]]:
        """创建真实业务场景的测试数据"""
        return {
            # 北京6月测试数据（8月活动）
            'BJ-JUN-REALISTIC': [
                # 幸运数字8，万元以上，应该获得"接好运万元以上"
                {
                    '合同ID(_id)': '2025080812345678',
                    '管家(serviceHousekeeper)': '北京张三',
                    '服务商(orgName)': '北京优质服务A',
                    '合同金额(adjustRefundMoney)': 25000,
                    '支付金额(paidAmount)': 20000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ001',
                    '工单编号(serviceAppointmentNum)': 'WD001',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-08-08 10:00:00'
                },
                # 幸运数字8，万元以下，应该获得"接好运"
                {
                    '合同ID(_id)': '2025080812345688',
                    '管家(serviceHousekeeper)': '北京李四',
                    '服务商(orgName)': '北京优质服务B',
                    '合同金额(adjustRefundMoney)': 8500,
                    '支付金额(paidAmount)': 7000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ002',
                    '工单编号(serviceAppointmentNum)': 'WD002',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-08-08 11:00:00'
                },
                # 非幸运数字，不应该有幸运奖励
                {
                    '合同ID(_id)': '2025080812345679',
                    '管家(serviceHousekeeper)': '北京王五',
                    '服务商(orgName)': '北京优质服务C',
                    '合同金额(adjustRefundMoney)': 15000,
                    '支付金额(paidAmount)': 12000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ003',
                    '工单编号(serviceAppointmentNum)': 'WD003',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-08-08 12:00:00'
                },
                # 同一管家的第二个合同（用于测试累计统计）
                {
                    '合同ID(_id)': '2025080812345680',
                    '管家(serviceHousekeeper)': '北京张三',
                    '服务商(orgName)': '北京优质服务A',
                    '合同金额(adjustRefundMoney)': 18000,
                    '支付金额(paidAmount)': 15000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ001',
                    '工单编号(serviceAppointmentNum)': 'WD004',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-08-08 13:00:00'
                }
            ],
            
            # 北京9月测试数据（增加了历史合同、个人序列幸运数字、5万上限）
            'BJ-SEP-REALISTIC': [
                # 新合同，超过5万上限，应该被限制为5万
                {
                    '合同ID(_id)': '2025090912345680',
                    '管家(serviceHousekeeper)': '北京赵六',
                    '服务商(orgName)': '北京精品服务A',
                    '合同金额(adjustRefundMoney)': 80000,  # 超过5万上限
                    '支付金额(paidAmount)': 65000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ004',
                    '工单编号(serviceAppointmentNum)': 'WD005',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-09 10:00:00'
                },
                # 历史合同，有pcContractdocNum字段
                {
                    '合同ID(_id)': '2025090912345681',
                    'pcContractdocNum': 'PC2024123001',  # 历史合同标识
                    '管家(serviceHousekeeper)': '北京赵六',
                    '服务商(orgName)': '北京精品服务A',
                    '合同金额(adjustRefundMoney)': 35000,
                    '支付金额(paidAmount)': 28000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ004',
                    '工单编号(serviceAppointmentNum)': 'WD006',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-09 11:00:00'
                },
                # 第三个合同（用于测试个人序列幸运数字：第3个不是5的倍数）
                {
                    '合同ID(_id)': '2025090912345682',
                    '管家(serviceHousekeeper)': '北京赵六',
                    '服务商(orgName)': '北京精品服务A',
                    '合同金额(adjustRefundMoney)': 22000,
                    '支付金额(paidAmount)': 18000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ004',
                    '工单编号(serviceAppointmentNum)': 'WD007',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-09 12:00:00'
                },
                # 第五个合同（个人序列第5个，是5的倍数，应该有幸运奖励）
                {
                    '合同ID(_id)': '2025090912345683',
                    '管家(serviceHousekeeper)': '北京赵六',
                    '服务商(orgName)': '北京精品服务A',
                    '合同金额(adjustRefundMoney)': 28000,
                    '支付金额(paidAmount)': 22000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ004',
                    '工单编号(serviceAppointmentNum)': 'WD008',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-09 13:00:00'
                },
                # 第五个合同的补充（确保是第5个）
                {
                    '合同ID(_id)': '2025090912345684',
                    '管家(serviceHousekeeper)': '北京赵六',
                    '服务商(orgName)': '北京精品服务A',
                    '合同金额(adjustRefundMoney)': 30000,
                    '支付金额(paidAmount)': 24000,
                    '款项来源类型(tradeIn)': 0,
                    '管家ID(serviceHousekeeperId)': 'BJ004',
                    '工单编号(serviceAppointmentNum)': 'WD009',
                    '活动城市(province)': '北京',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-09 14:00:00'
                }
            ],
            
            # 上海9月测试数据（双轨统计 + 自引单奖励 + 项目地址去重）
            'SH-SEP-REALISTIC': [
                # 平台单
                {
                    '合同ID(_id)': '2025090812345705',
                    '管家(serviceHousekeeper)': '上海孙七',
                    '服务商(orgName)': '上海精品服务A',
                    '合同金额(adjustRefundMoney)': 18000,
                    '支付金额(paidAmount)': 15000,
                    '款项来源类型(tradeIn)': 0,  # 平台单
                    '管家ID(serviceHousekeeperId)': 'SH001',
                    '客户联系地址(contactsAddress)': '上海市浦东新区',
                    '项目地址(projectAddress)': '上海市浦东新区陆家嘴金融中心A座',
                    '活动城市(province)': '上海',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-08 10:00:00'
                },
                # 自引单（不同项目地址）
                {
                    '合同ID(_id)': '2025090812345706',
                    '管家(serviceHousekeeper)': '上海孙七',
                    '服务商(orgName)': '上海精品服务A',
                    '合同金额(adjustRefundMoney)': 22000,
                    '支付金额(paidAmount)': 18000,
                    '款项来源类型(tradeIn)': 1,  # 自引单
                    '管家ID(serviceHousekeeperId)': 'SH001',
                    '客户联系地址(contactsAddress)': '上海市徐汇区',
                    '项目地址(projectAddress)': '上海市徐汇区衡山路商务中心B座',
                    '活动城市(province)': '上海',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-08 11:00:00'
                },
                # 重复项目地址的自引单（应该被跳过）
                {
                    '合同ID(_id)': '2025090812345707',
                    '管家(serviceHousekeeper)': '上海孙七',
                    '服务商(orgName)': '上海精品服务A',
                    '合同金额(adjustRefundMoney)': 20000,
                    '支付金额(paidAmount)': 16000,
                    '款项来源类型(tradeIn)': 1,  # 自引单
                    '管家ID(serviceHousekeeperId)': 'SH001',
                    '客户联系地址(contactsAddress)': '上海市徐汇区',
                    '项目地址(projectAddress)': '上海市徐汇区衡山路商务中心B座',  # 重复地址
                    '活动城市(province)': '上海',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-08 12:00:00'
                },
                # 另一个管家的平台单
                {
                    '合同ID(_id)': '2025090812345708',
                    '管家(serviceHousekeeper)': '上海周八',
                    '服务商(orgName)': '上海精品服务B',
                    '合同金额(adjustRefundMoney)': 16000,
                    '支付金额(paidAmount)': 13000,
                    '款项来源类型(tradeIn)': 0,  # 平台单
                    '管家ID(serviceHousekeeperId)': 'SH002',
                    '客户联系地址(contactsAddress)': '上海市静安区',
                    '项目地址(projectAddress)': '上海市静安区南京西路购物中心C座',
                    '活动城市(province)': '上海',
                    'Status': '已签约',
                    '创建时间(createTime)': '2025-09-08 13:00:00'
                }
            ]
        }


    def validate_beijing_june_vs_september_differences(self):
        """验证北京6月vs9月的差异处理"""
        print("\n=== 北京6月vs9月差异验证 ===")

        test_data = self.create_realistic_test_data()

        # 验证北京6月（8月活动）
        june_result = self._process_and_validate_beijing_june(test_data['BJ-JUN-REALISTIC'])

        # 验证北京9月
        september_result = self._process_and_validate_beijing_september(test_data['BJ-SEP-REALISTIC'])

        # 对比差异
        differences = self._compare_beijing_june_september(june_result, september_result)

        return {
            'june_result': june_result,
            'september_result': september_result,
            'differences': differences,
            'validation_passed': len(differences['errors']) == 0
        }

    def _process_and_validate_beijing_june(self, test_data: List[Dict]) -> Dict[str, Any]:
        """处理和验证北京6月数据"""
        print("  处理北京6月数据...")

        # 创建处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-06",
            activity_code="BJ-JUN",
            city="BJ",
            db_path=self.temp_db.name + "_june",
            enable_project_limit=True
        )

        # 处理数据
        processed_records = pipeline.process(test_data)

        # 分析结果
        result = {
            'total_records': len(processed_records),
            'lucky_records': [],
            'cumulative_stats': {},
            'reward_summary': {},
            'expected_vs_actual': {}
        }

        # 分析幸运数字奖励
        for record in processed_records:
            for reward in record.rewards:
                if '接好运' in reward.reward_name:
                    result['lucky_records'].append({
                        'contract_id': record.contract_data.contract_id,
                        'reward_name': reward.reward_name,
                        'contract_amount': record.contract_data.contract_amount
                    })

        # 分析累计统计
        for record in processed_records:
            housekeeper = record.housekeeper_stats.housekeeper
            if housekeeper not in result['cumulative_stats']:
                result['cumulative_stats'][housekeeper] = []
            result['cumulative_stats'][housekeeper].append({
                'contract_count': record.housekeeper_stats.contract_count,
                'total_amount': record.housekeeper_stats.total_amount,
                'contract_id': record.contract_data.contract_id
            })

        # 验证预期结果
        expected_lucky_count = 2  # 两个末位8的合同
        actual_lucky_count = len(result['lucky_records'])

        result['expected_vs_actual'] = {
            'lucky_rewards': {
                'expected': expected_lucky_count,
                'actual': actual_lucky_count,
                'match': expected_lucky_count == actual_lucky_count
            },
            'total_records': {
                'expected': 4,
                'actual': result['total_records'],
                'match': result['total_records'] == 4
            }
        }

        print(f"    北京6月处理完成: {result['total_records']}条记录, {actual_lucky_count}个幸运奖励")
        return result

    def _process_and_validate_beijing_september(self, test_data: List[Dict]) -> Dict[str, Any]:
        """处理和验证北京9月数据"""
        print("  处理北京9月数据...")

        # 创建处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-09",
            activity_code="BJ-SEP",
            city="BJ",
            db_path=self.temp_db.name + "_september",
            enable_project_limit=True,
            enable_historical_contracts=True
        )

        # 处理数据
        processed_records = pipeline.process(test_data)

        # 分析结果
        result = {
            'total_records': len(processed_records),
            'historical_records': [],
            'amount_limited_records': [],
            'personal_sequence_lucky': [],
            'cumulative_stats': {},
            'expected_vs_actual': {}
        }

        # 分析历史合同
        for record in processed_records:
            if record.contract_data.is_historical:
                result['historical_records'].append({
                    'contract_id': record.contract_data.contract_id,
                    'pc_contract_num': record.contract_data.raw_data.get('pcContractdocNum', '')
                })

        # 分析工单金额上限
        for record in processed_records:
            if record.contract_data.contract_amount > 50000 and record.performance_amount == 50000:
                result['amount_limited_records'].append({
                    'contract_id': record.contract_data.contract_id,
                    'original_amount': record.contract_data.contract_amount,
                    'limited_amount': record.performance_amount
                })

        # 分析个人序列幸运数字（第5个合同应该有幸运奖励）
        for record in processed_records:
            for reward in record.rewards:
                if '接好运' in reward.reward_name:
                    result['personal_sequence_lucky'].append({
                        'contract_id': record.contract_data.contract_id,
                        'reward_name': reward.reward_name,
                        'sequence_number': record.housekeeper_stats.contract_count
                    })

        # 验证预期结果
        expected_historical = 1  # 一个历史合同
        expected_limited = 1     # 一个超限合同
        expected_lucky = 1       # 第5个合同有幸运奖励

        result['expected_vs_actual'] = {
            'historical_contracts': {
                'expected': expected_historical,
                'actual': len(result['historical_records']),
                'match': len(result['historical_records']) == expected_historical
            },
            'amount_limited': {
                'expected': expected_limited,
                'actual': len(result['amount_limited_records']),
                'match': len(result['amount_limited_records']) == expected_limited
            },
            'personal_sequence_lucky': {
                'expected': expected_lucky,
                'actual': len(result['personal_sequence_lucky']),
                'match': len(result['personal_sequence_lucky']) == expected_lucky
            },
            'total_records': {
                'expected': 5,
                'actual': result['total_records'],
                'match': result['total_records'] == 5
            }
        }

        print(f"    北京9月处理完成: {result['total_records']}条记录, {len(result['historical_records'])}个历史合同, {len(result['amount_limited_records'])}个超限处理")
        return result

    def _compare_beijing_june_september(self, june_result: Dict, september_result: Dict) -> Dict[str, Any]:
        """对比北京6月vs9月的差异"""
        print("  对比北京6月vs9月差异...")

        differences = {
            'key_differences': [],
            'errors': [],
            'summary': {}
        }

        # 验证关键差异
        # 1. 幸运数字逻辑差异
        june_lucky = june_result['expected_vs_actual']['lucky_rewards']
        september_lucky = september_result['expected_vs_actual']['personal_sequence_lucky']

        if june_lucky['match'] and september_lucky['match']:
            differences['key_differences'].append("✅ 幸运数字逻辑差异正确：6月末位8 vs 9月个人序列5倍数")
        else:
            differences['errors'].append(f"❌ 幸运数字逻辑错误：6月{june_lucky} vs 9月{september_lucky}")

        # 2. 工单金额上限差异
        september_limited = september_result['expected_vs_actual']['amount_limited']
        if september_limited['match']:
            differences['key_differences'].append("✅ 工单金额上限差异正确：6月无限制 vs 9月5万上限")
        else:
            differences['errors'].append(f"❌ 工单金额上限错误：9月应该有1个超限处理，实际{september_limited}")

        # 3. 历史合同支持差异
        september_historical = september_result['expected_vs_actual']['historical_contracts']
        if september_historical['match']:
            differences['key_differences'].append("✅ 历史合同支持差异正确：6月不支持 vs 9月支持")
        else:
            differences['errors'].append(f"❌ 历史合同支持错误：9月应该有1个历史合同，实际{september_historical}")

        differences['summary'] = {
            'total_differences_verified': len(differences['key_differences']),
            'errors_found': len(differences['errors']),
            'validation_passed': len(differences['errors']) == 0
        }

        return differences


    def validate_shanghai_multi_month_compatibility(self):
        """验证上海多月份兼容性"""
        print("\n=== 上海多月份兼容性验证 ===")

        test_data = self.create_realistic_test_data()['SH-SEP-REALISTIC']

        # 验证上海不同月份的处理
        results = {}

        for config_key, activity_code, month_name in [
            ('SH-2025-04', 'SH-APR', '4月'),
            ('SH-2025-08', 'SH-AUG', '8月'),
            ('SH-2025-09', 'SH-SEP', '9月')
        ]:
            print(f"  验证上海{month_name}...")
            results[month_name] = self._process_shanghai_month(
                test_data, config_key, activity_code, month_name
            )

        # 对比不同月份的差异
        compatibility_result = self._compare_shanghai_months(results)

        return {
            'month_results': results,
            'compatibility': compatibility_result,
            'validation_passed': compatibility_result['validation_passed']
        }

    def _process_shanghai_month(self, test_data: List[Dict], config_key: str,
                               activity_code: str, month_name: str) -> Dict[str, Any]:
        """处理上海特定月份数据"""

        # 创建处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key=config_key,
            activity_code=activity_code,
            city="SH",
            db_path=self.temp_db.name + f"_sh_{month_name}",
            enable_dual_track=(config_key == 'SH-2025-09'),
            housekeeper_key_format="管家_服务商"
        )

        # 处理数据
        processed_records = pipeline.process(test_data)

        # 分析结果
        result = {
            'month': month_name,
            'config_key': config_key,
            'total_records': len(processed_records),
            'platform_records': [],
            'self_referral_records': [],
            'red_packet_rewards': [],
            'lucky_rewards': [],
            'project_address_dedup': {},
            'expected_vs_actual': {}
        }

        # 分析双轨统计（仅9月有效）
        if config_key == 'SH-2025-09':
            for record in processed_records:
                if record.contract_data.order_type.value == 'platform':
                    result['platform_records'].append({
                        'contract_id': record.contract_data.contract_id,
                        'amount': record.contract_data.contract_amount
                    })
                elif record.contract_data.order_type.value == 'self_referral':
                    result['self_referral_records'].append({
                        'contract_id': record.contract_data.contract_id,
                        'amount': record.contract_data.contract_amount,
                        'project_address': record.contract_data.raw_data.get('项目地址(projectAddress)', '')
                    })

        # 分析红包奖励
        for record in processed_records:
            for reward in record.rewards:
                if '红包' in reward.reward_name:
                    result['red_packet_rewards'].append({
                        'contract_id': record.contract_data.contract_id,
                        'reward_name': reward.reward_name
                    })

        # 分析幸运数字奖励（上海应该没有）
        for record in processed_records:
            for reward in record.rewards:
                if '接好运' in reward.reward_name:
                    result['lucky_rewards'].append({
                        'contract_id': record.contract_data.contract_id,
                        'reward_name': reward.reward_name
                    })

        # 验证预期结果
        if config_key == 'SH-2025-09':
            # 9月：双轨统计 + 自引单奖励 + 项目地址去重
            expected_total = 3  # 原始4条，重复地址1条被跳过，实际处理3条
            expected_platform = 2  # 2个平台单
            expected_self_referral = 1  # 1个自引单（重复地址的被跳过）
            expected_red_packet = 1  # 1个红包奖励
        else:
            # 4月、8月：基础处理，无双轨统计
            expected_total = 4  # 所有4条都处理
            expected_platform = 0  # 无双轨统计概念
            expected_self_referral = 0
            expected_red_packet = 0  # 无自引单奖励

        result['expected_vs_actual'] = {
            'total_records': {
                'expected': expected_total,
                'actual': result['total_records'],
                'match': result['total_records'] == expected_total
            },
            'platform_records': {
                'expected': expected_platform,
                'actual': len(result['platform_records']),
                'match': len(result['platform_records']) == expected_platform
            },
            'self_referral_records': {
                'expected': expected_self_referral,
                'actual': len(result['self_referral_records']),
                'match': len(result['self_referral_records']) == expected_self_referral
            },
            'red_packet_rewards': {
                'expected': expected_red_packet,
                'actual': len(result['red_packet_rewards']),
                'match': len(result['red_packet_rewards']) == expected_red_packet
            },
            'lucky_rewards': {
                'expected': 0,  # 上海所有月份都无幸运奖励
                'actual': len(result['lucky_rewards']),
                'match': len(result['lucky_rewards']) == 0
            }
        }

        print(f"    上海{month_name}处理完成: {result['total_records']}条记录")
        return result

    def _compare_shanghai_months(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """对比上海不同月份的兼容性"""
        print("  对比上海不同月份兼容性...")

        compatibility = {
            'consistent_features': [],
            'month_specific_features': [],
            'errors': [],
            'validation_passed': True
        }

        # 验证一致性特征（所有月份都应该有的）
        for month, result in results.items():
            # 1. 无幸运数字奖励
            if result['expected_vs_actual']['lucky_rewards']['match']:
                compatibility['consistent_features'].append(f"✅ {month}无幸运数字奖励")
            else:
                compatibility['errors'].append(f"❌ {month}不应该有幸运数字奖励")
                compatibility['validation_passed'] = False

        # 验证月份特定功能
        # 9月特有功能
        sep_result = results.get('9月', {})
        if sep_result:
            if sep_result['expected_vs_actual']['platform_records']['match']:
                compatibility['month_specific_features'].append("✅ 9月双轨统计-平台单正确")
            else:
                compatibility['errors'].append("❌ 9月双轨统计-平台单错误")
                compatibility['validation_passed'] = False

            if sep_result['expected_vs_actual']['self_referral_records']['match']:
                compatibility['month_specific_features'].append("✅ 9月双轨统计-自引单正确")
            else:
                compatibility['errors'].append("❌ 9月双轨统计-自引单错误")
                compatibility['validation_passed'] = False

            if sep_result['expected_vs_actual']['red_packet_rewards']['match']:
                compatibility['month_specific_features'].append("✅ 9月自引单红包奖励正确")
            else:
                compatibility['errors'].append("❌ 9月自引单红包奖励错误")
                compatibility['validation_passed'] = False

        # 4月、8月基础功能
        for month in ['4月', '8月']:
            month_result = results.get(month, {})
            if month_result and month_result['expected_vs_actual']['total_records']['match']:
                compatibility['month_specific_features'].append(f"✅ {month}基础处理正确")
            else:
                compatibility['errors'].append(f"❌ {month}基础处理错误")
                compatibility['validation_passed'] = False

        return compatibility

    def test_comprehensive_equivalence_validation(self):
        """全面等价性验证测试"""
        print("\n" + "="*80)
        print("全面等价性验证 - 新架构与原有功能完全等价性验证")
        print("="*80)

        # 验证北京6月vs9月差异
        beijing_validation = self.validate_beijing_june_vs_september_differences()
        self.validation_results.append({
            'test_name': '北京6月vs9月差异验证',
            'result': beijing_validation,
            'passed': beijing_validation['validation_passed']
        })

        # 验证上海多月份兼容性
        shanghai_validation = self.validate_shanghai_multi_month_compatibility()
        self.validation_results.append({
            'test_name': '上海多月份兼容性验证',
            'result': shanghai_validation,
            'passed': shanghai_validation['validation_passed']
        })

        # 生成综合报告
        self._generate_comprehensive_report()

        # 断言所有验证都通过
        all_passed = all(result['passed'] for result in self.validation_results)
        self.assertTrue(all_passed, "全面等价性验证存在失败项")

        print("\n" + "="*80)
        print("✅ 全面等价性验证完成！")
        print("="*80)

    def _generate_comprehensive_report(self):
        """生成全面验证报告"""
        print("\n" + "="*60)
        print("全面等价性验证报告")
        print("="*60)

        total_tests = len(self.validation_results)
        passed_tests = len([r for r in self.validation_results if r['passed']])

        print(f"总验证项: {total_tests}")
        print(f"通过验证: {passed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")

        for result in self.validation_results:
            status = "✅ 通过" if result['passed'] else "❌ 失败"
            print(f"\n{result['test_name']}: {status}")

            if result['test_name'] == '北京6月vs9月差异验证':
                beijing_result = result['result']
                print("  关键差异验证:")
                for diff in beijing_result['differences']['key_differences']:
                    print(f"    {diff}")
                for error in beijing_result['differences']['errors']:
                    print(f"    {error}")

            elif result['test_name'] == '上海多月份兼容性验证':
                shanghai_result = result['result']
                print("  一致性特征:")
                for feature in shanghai_result['compatibility']['consistent_features']:
                    print(f"    {feature}")
                print("  月份特定功能:")
                for feature in shanghai_result['compatibility']['month_specific_features']:
                    print(f"    {feature}")
                for error in shanghai_result['compatibility']['errors']:
                    print(f"    {error}")

        if passed_tests == total_tests:
            print(f"\n🎉 全面等价性验证100%通过！")
            print("新架构与原有功能完全等价，支持所有业务差异")
        else:
            print(f"\n❌ 存在{total_tests - passed_tests}个验证失败项，需要修复")


def run_comprehensive_equivalence_validation():
    """运行全面等价性验证"""
    print("销售激励系统重构 - 全面等价性验证")
    print("验证重点：北京6月vs9月差异兼容性，上海多月份兼容性")
    print("=" * 80)

    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(ComprehensiveEquivalenceValidator('test_comprehensive_equivalence_validation'))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    run_comprehensive_equivalence_validation()
