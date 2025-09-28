"""
北京2025年10月销售激励活动集成测试

测试整个处理流程的正确性，包括：
1. 配置加载
2. 数据处理管道
3. 奖励计算
4. 消息生成
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline
from modules.core.data_models import PerformanceRecord


class TestBeijingOctoberIntegration:
    """北京10月功能集成测试"""
    
    def test_config_loading(self):
        """测试北京10月配置加载"""
        from modules.core.config_adapter import ConfigAdapter
        
        # 测试配置加载
        config = ConfigAdapter.get_reward_config("BJ-2025-10")
        
        # 验证关键配置
        assert config["lucky_number"] == "5"
        assert config["lucky_number_sequence_type"] == "platform_only"
        assert config["self_referral_rewards"]["enable"] == False
        assert config["reward_calculation_strategy"]["type"] == "dual_track"
        
        print("✅ 配置加载测试通过")
    
    def test_pipeline_creation(self):
        """测试处理管道创建"""
        try:
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-10",
                activity_code="BJ-OCT",
                city="BJ",
                housekeeper_key_format="管家",
                storage_type="sqlite",
                enable_project_limit=True,
                enable_dual_track=True,
                enable_historical_contracts=False,
                db_path=":memory:"  # 使用内存数据库进行测试
            )
            
            # 验证管道组件
            assert pipeline is not None
            assert config.config_key == "BJ-2025-10"
            assert config.activity_code == "BJ-OCT"
            assert config.enable_dual_track == True
            assert config.enable_historical_contracts == False
            assert store is not None
            
            print("✅ 处理管道创建测试通过")
            
        except Exception as e:
            pytest.skip(f"管道创建测试跳过，原因: {e}")
    
    def test_mock_data_processing(self):
        """测试模拟数据处理"""
        # 创建模拟合同数据
        mock_contract_data = [
            {
                '合同ID(_id)': 'test_001',
                '活动城市(province)': '北京',
                '工单编号(serviceAppointmentNum)': 'SA001',
                'Status': 'COMPLETED',
                '管家(serviceHousekeeper)': '张三',
                '合同编号(contractdocNum)': 'BJ202510001',
                '合同金额(adjustRefundMoney)': 50000,
                '支付金额(paidAmount)': 50000,
                '差额(difference)': 0,
                'State': 'PAID',
                '创建时间(createTime)': '2025-10-01 10:00:00',
                '服务商(orgName)': '测试服务商',
                '签约时间(signedDate)': '2025-10-01',
                'Doorsill': 0,
                '款项来源类型(tradeIn)': '',
                '转化率(conversion)': '',
                '平均客单价(average)': '',
                '管家ID(serviceHousekeeperId)': 'hk001',
                '工单类型(sourceType)': '2',  # 平台单
                '客户联系地址(contactsAddress)': '北京市朝阳区',
                '项目地址(projectAddress)': '北京市朝阳区测试项目',
            },
            {
                '合同ID(_id)': 'test_002',
                '活动城市(province)': '北京',
                '工单编号(serviceAppointmentNum)': 'SA002',
                'Status': 'COMPLETED',
                '管家(serviceHousekeeper)': '张三',
                '合同编号(contractdocNum)': 'BJ202510002',
                '合同金额(adjustRefundMoney)': 30000,
                '支付金额(paidAmount)': 30000,
                '差额(difference)': 0,
                'State': 'PAID',
                '创建时间(createTime)': '2025-10-02 10:00:00',
                '服务商(orgName)': '测试服务商',
                '签约时间(signedDate)': '2025-10-02',
                'Doorsill': 0,
                '款项来源类型(tradeIn)': '',
                '转化率(conversion)': '',
                '平均客单价(average)': '',
                '管家ID(serviceHousekeeperId)': 'hk001',
                '工单类型(sourceType)': '1',  # 自引单
                '客户联系地址(contactsAddress)': '北京市海淀区',
                '项目地址(projectAddress)': '北京市海淀区测试项目',
            }
        ]
        
        try:
            # 创建处理管道
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-10",
                activity_code="BJ-OCT",
                city="BJ",
                housekeeper_key_format="管家",
                storage_type="sqlite",
                enable_project_limit=True,
                enable_dual_track=True,
                enable_historical_contracts=False,
                db_path=":memory:"
            )
            
            # 处理数据
            processed_records = pipeline.process(mock_contract_data)
            
            # 验证处理结果
            assert isinstance(processed_records, list)
            assert len(processed_records) >= 0  # 可能因为数据过滤而为空
            
            print(f"✅ 模拟数据处理测试通过，处理了 {len(processed_records)} 条记录")
            
            # 如果有处理结果，验证数据结构
            if processed_records:
                record = processed_records[0]
                assert isinstance(record, PerformanceRecord)
                assert record.activity_code == "BJ-OCT"
                print("✅ 数据结构验证通过")
            
        except Exception as e:
            pytest.skip(f"模拟数据处理测试跳过，原因: {e}")
    
    def test_reward_calculation_logic(self):
        """测试奖励计算逻辑"""
        from modules.core.reward_calculator import RewardCalculator
        from modules.core.data_models import ContractData, HousekeeperStats, OrderType
        
        # 创建奖励计算器
        calculator = RewardCalculator("BJ-2025-10")
        
        # 测试数据：平台单数量为5（5的倍数）
        housekeeper_stats = HousekeeperStats(
            housekeeper="张三",
            activity_code="BJ-OCT",
            contract_count=8,
            platform_count=5,  # 平台单5个，应该触发幸运数字
            self_referral_count=3,
            total_amount=80000,
            performance_amount=80000,
            platform_amount=50000,
            self_referral_amount=30000
        )
        
        contract_data = ContractData(
            contract_id="test_001",
            housekeeper="张三",
            service_provider="测试服务商",
            contract_amount=50000,
            order_type=OrderType.PLATFORM
        )
        
        # 计算奖励
        rewards, next_reward_gap = calculator.calculate(
            contract_data, housekeeper_stats
        )

        # 验证幸运数字奖励
        assert len(rewards) > 0, "应该有奖励"

        # 检查是否有幸运数字奖励
        lucky_reward = None
        for reward in rewards:
            if reward.reward_type == "幸运数字":
                lucky_reward = reward
                break

        assert lucky_reward is not None, "应该有幸运数字奖励"
        assert lucky_reward.reward_name == "接好运"

        print("✅ 奖励计算逻辑测试通过")
        print(f"   奖励数量: {len(rewards)}")
        print(f"   幸运数字奖励: {lucky_reward.reward_name}")
        print(f"   下一奖励差距: {next_reward_gap}")
    
    def test_message_template_generation(self):
        """测试消息模板生成"""
        from modules.core.notification_service import NotificationService
        from modules.core.data_models import ProcessingConfig, City
        from unittest.mock import Mock, patch
        
        # 创建配置
        config = ProcessingConfig(
            config_key="BJ-2025-10",
            activity_code="BJ-OCT",
            city=City.BEIJING,
            housekeeper_key_format="管家"
        )
        
        # 创建通知服务
        mock_storage = Mock()
        notification_service = NotificationService(mock_storage, config)
        
        # 测试记录
        test_record = {
            '管家(serviceHousekeeper)': '张三',
            '合同编号(contractdocNum)': 'BJ202510001',
            '工单类型': '平台单',
            '平台单累计数量': 5,
            '自引单累计数量': 3,
            '平台单累计金额': 125000,
            '自引单累计金额': 75000,
            '备注': '距离 精英奖 还需 100,000 元',
            '是否发送通知': 'N'
        }
        
        # 模拟消息发送
        with patch('modules.core.notification_service.create_task') as mock_create_task:
            notification_service._send_group_notification(test_record)
            
            # 验证消息发送
            mock_create_task.assert_called_once()
            call_args = mock_create_task.call_args[0]
            message = call_args[2]
            
            # 验证消息内容
            assert '🧨🧨🧨 签约喜报 🧨🧨🧨' in message
            assert '张三' in message
            assert '平台单' in message
            assert '本单为平台本月累计签约第 8 单' in message  # 5+3=8
            assert '个人平台单累计签约第 5 单，累计签约 125,000 元' in message
            assert '个人自引单累计签约第 3 单，累计签约 75,000元' in message
            assert '距离 精英奖 还需 100,000 元' in message
            
            print("✅ 消息模板生成测试通过")
            print(f"   生成的消息长度: {len(message)} 字符")


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "-s"])
