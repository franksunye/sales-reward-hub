"""
上海2025年10月销售激励活动功能测试

测试重点：
1. 消息模板不显示自引单信息
2. 自引单奖励禁用逻辑
3. 平台单奖励计算正确
4. 配置隔离有效
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from typing import List, Dict

# 设置测试环境
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai_v2
from modules.core.notification_service import NotificationService
from modules.core.data_models import ProcessingConfig, City
from modules.core.storage import create_data_store


class TestShanghaiOctoberMessageTemplate:
    """测试上海10月专用消息模板"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = ProcessingConfig(
            config_key="SH-2025-10",
            activity_code="SH-OCT",
            city=City.SHANGHAI,
            housekeeper_key_format="管家_服务商"
        )
        
        # 创建存储实例
        self.storage = create_data_store(storage_type="sqlite", db_path=":memory:")
        
        # 创建通知服务
        self.notification_service = NotificationService(self.storage, self.config)
    
    def test_shanghai_october_platform_order_message(self):
        """测试上海10月平台单消息模板 - 不显示自引单信息"""
        # 准备测试数据
        record = {
            '管家(serviceHousekeeper)': '张三',
            '工单类型': '平台单',
            '合同编号(contractdocNum)': 'SH-OCT-001',
            '活动期内第几个合同': 5,
            '平台单累计数量': 3,
            '自引单累计数量': 2,  # 这个字段应该被忽略
            '平台单累计金额': 150000,
            '自引单累计金额': 80000,  # 这个字段应该被忽略
            '转化率(conversion)': '15.5%',
            '是否发送通知': 'N'
        }
        
        # 模拟备注信息
        with patch.object(self.notification_service, '_should_send_group_notification', return_value=True):
            with patch('task_manager.create_task') as mock_create_task:
                self.notification_service._send_group_notification(record)
                
                # 验证任务创建被调用
                assert mock_create_task.called
                
                # 获取消息内容
                call_args = mock_create_task.call_args
                message = call_args[0][2]  # 第三个参数是消息内容
                
                # 验证消息包含平台单信息
                assert '个人平台单累计签约第 3 单' in message
                assert '个人平台单金额累计签约 15.0万 元' in message
                assert '个人平台单转化率 15.5%' in message
                
                # 验证消息不包含自引单信息
                assert '自引单累计签约第' not in message
                assert '自引单金额累计签约' not in message
                assert '累计计入业绩' not in message
    
    def test_shanghai_october_self_referral_order_message(self):
        """测试上海10月自引单消息模板 - 同样不显示自引单信息"""
        # 准备测试数据
        record = {
            '管家(serviceHousekeeper)': '李四',
            '工单类型': '自引单',  # 即使是自引单，也使用相同的模板
            '合同编号(contractdocNum)': 'SH-OCT-002',
            '活动期内第几个合同': 8,
            '平台单累计数量': 5,
            '自引单累计数量': 3,
            '平台单累计金额': 200000,
            '自引单累计金额': 120000,
            '转化率(conversion)': '18.2%',
            '是否发送通知': 'N'
        }
        
        with patch.object(self.notification_service, '_should_send_group_notification', return_value=True):
            with patch('task_manager.create_task') as mock_create_task:
                self.notification_service._send_group_notification(record)
                
                # 验证任务创建被调用
                assert mock_create_task.called
                
                # 获取消息内容
                call_args = mock_create_task.call_args
                message = call_args[0][2]
                
                # 验证消息仍然只显示平台单信息，即使当前合同是自引单
                assert '个人平台单累计签约第 5 单' in message
                assert '个人平台单金额累计签约 20.0万 元' in message
                assert '个人平台单转化率 18.2%' in message
                
                # 验证消息不包含自引单信息
                assert '自引单累计签约第' not in message
                assert '自引单金额累计签约' not in message


class TestShanghaiOctoberSelfReferralRewards:
    """测试上海10月自引单奖励禁用逻辑"""
    
    def test_self_referral_rewards_disabled_in_config(self):
        """测试配置中自引单奖励被正确禁用"""
        from modules.config import REWARD_CONFIGS
        
        config = REWARD_CONFIGS.get("SH-2025-10")
        assert config is not None, "SH-2025-10配置不存在"
        
        # 验证自引单奖励被禁用
        self_referral_config = config.get("self_referral_rewards", {})
        assert self_referral_config.get("enable") is False, "自引单奖励应该被禁用"
        
        # 验证奖励计算策略为单轨
        strategy_config = config.get("reward_calculation_strategy", {})
        assert strategy_config.get("type") == "single_track", "应该使用单轨激励策略"


class TestShanghaiOctoberPlatformRewards:
    """测试上海10月平台单奖励计算"""
    
    def test_platform_rewards_configuration(self):
        """测试平台单奖励配置正确"""
        from modules.config import REWARD_CONFIGS
        
        config = REWARD_CONFIGS.get("SH-2025-10")
        assert config is not None
        
        # 验证节节高奖励配置
        tiered_rewards = config.get("tiered_rewards", {})
        assert tiered_rewards.get("min_contracts") == 5, "平台单需要5个合同"
        
        # 验证奖励阶梯
        tiers = tiered_rewards.get("tiers", [])
        expected_tiers = [
            {"name": "基础奖", "threshold": 40000},
            {"name": "达标奖", "threshold": 60000},
            {"name": "优秀奖", "threshold": 80000},
            {"name": "精英奖", "threshold": 120000},
            {"name": "卓越奖", "threshold": 160000}
        ]
        
        assert len(tiers) == len(expected_tiers), "奖励阶梯数量不正确"
        for expected, actual in zip(expected_tiers, tiers):
            assert actual["name"] == expected["name"], f"奖励名称不匹配: {actual['name']} vs {expected['name']}"
            assert actual["threshold"] == expected["threshold"], f"奖励阈值不匹配: {actual['threshold']} vs {expected['threshold']}"
        
        # 验证奖励金额映射
        awards_mapping = config.get("awards_mapping", {})
        expected_awards = {
            "基础奖": "200",
            "达标奖": "300",
            "优秀奖": "400",
            "精英奖": "800",
            "卓越奖": "1200"
        }
        
        for award_name, expected_amount in expected_awards.items():
            assert awards_mapping.get(award_name) == expected_amount, f"{award_name}奖励金额不正确"


class TestShanghaiOctoberJobFunction:
    """测试上海10月Job函数"""
    
    @patch('modules.core.shanghai_jobs._get_shanghai_contract_data')
    @patch('modules.core.shanghai_jobs._send_notifications')
    def test_shanghai_october_job_function_exists(self, mock_send_notifications, mock_get_data):
        """测试上海10月Job函数存在且可调用"""
        # 模拟合同数据
        mock_get_data.return_value = [
            {
                '合同ID(_id)': 'SH-OCT-001',
                '管家(serviceHousekeeper)': '张三',
                '服务商(orgName)': '测试服务商',
                '工单类型(sourceType)': '2',  # 平台单
                '合同金额(adjustRefundMoney)': 50000,
                '支付金额(paidAmount)': 50000,
                '项目地址(projectAddress)': '上海市测试地址1'
            }
        ]
        
        # 模拟通知发送
        mock_send_notifications.return_value = None
        
        try:
            # 调用上海10月Job函数
            records = signing_and_sales_incentive_oct_shanghai_v2()
            
            # 验证函数正常执行
            assert isinstance(records, list), "返回结果应该是列表"
            
            # 验证使用了正确的API
            mock_get_data.assert_called_once()
            call_args = mock_get_data.call_args[0]
            
            # 验证使用了10月的API端点
            from modules.config import API_URL_SH_OCT
            assert call_args[0] == API_URL_SH_OCT, "应该使用上海10月的API端点"
            
        except Exception as e:
            pytest.fail(f"上海10月Job函数执行失败: {e}")


class TestShanghaiOctoberConfigIsolation:
    """测试上海10月配置隔离"""
    
    def test_config_isolation_from_september(self):
        """测试10月配置与9月配置隔离"""
        from modules.config import REWARD_CONFIGS
        
        oct_config = REWARD_CONFIGS.get("SH-2025-10")
        sep_config = REWARD_CONFIGS.get("SH-2025-09")
        
        assert oct_config is not None, "10月配置不存在"
        assert sep_config is not None, "9月配置不存在"
        
        # 验证关键差异
        # 10月：自引单奖励禁用，单轨
        oct_self_referral = oct_config.get("self_referral_rewards", {})
        oct_strategy = oct_config.get("reward_calculation_strategy", {})
        
        assert oct_self_referral.get("enable") is False, "10月应该禁用自引单奖励"
        assert oct_strategy.get("type") == "single_track", "10月应该使用单轨策略"
        
        # 9月：自引单奖励启用，双轨
        sep_self_referral = sep_config.get("self_referral_rewards", {})
        sep_strategy = sep_config.get("reward_calculation_strategy", {})
        
        assert sep_self_referral.get("enable") is True, "9月应该启用自引单奖励"
        assert sep_strategy.get("type") == "dual_track", "9月应该使用双轨策略"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
