"""
销售激励系统重构 - 上海Job函数迁移
版本: v1.0
创建日期: 2025-01-08

重构后的上海Job函数，使用新的核心架构。
支持双轨统计（平台单 vs 自引单）和项目地址去重逻辑。
"""

import logging
import os
import sys
from typing import List, Dict, Optional

# 确保能导入现有模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core import create_standard_pipeline
from modules.core.data_models import PerformanceRecord


def signing_and_sales_incentive_apr_shanghai_v2() -> List[PerformanceRecord]:
    """
    重构后的上海4月Job函数
    
    替代原有的signing_and_sales_incentive_apr_shanghai函数
    使用新的核心架构，支持基础的节节高奖励
    """
    logging.info("开始执行上海4月销售激励任务（重构版）")
    
    try:
        # 1. 创建标准处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="SH-2025-04",
            activity_code="SH-APR",
            city="SH",
            housekeeper_key_format="管家_服务商",  # 上海使用管家_服务商格式
            storage_type="sqlite",
            enable_dual_track=False,  # 4月还没有双轨统计
            db_path="performance_data.db"
        )
        
        logging.info(f"创建处理管道成功: {config.activity_code}")
        
        # 2. 获取合同数据
        contract_data = _get_shanghai_contract_data()
        logging.info(f"获取到 {len(contract_data)} 个合同数据")
        
        # 3. 处理数据
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")
        
        # 4. 生成CSV文件和发送通知
        csv_file = _generate_csv_output(processed_records, config)
        _send_notifications(processed_records, config)
        
        # 5. 获取处理摘要
        summary = pipeline.get_processing_summary()
        logging.info(f"处理摘要: {summary}")
        
        return processed_records
        
    except Exception as e:
        logging.error(f"上海4月任务执行失败: {e}")
        import traceback
        logging.error(f"详细错误: {traceback.format_exc()}")
        raise


def signing_and_sales_incentive_aug_shanghai_v2() -> List[PerformanceRecord]:
    """
    重构后的上海8月Job函数
    
    替代原有的signing_and_sales_incentive_aug_shanghai函数
    使用正确的配置，不再复用4月函数
    """
    logging.info("开始执行上海8月销售激励任务（重构版）")
    
    try:
        # 使用正确的8月配置
        pipeline, config, store = create_standard_pipeline(
            config_key="SH-2025-08",  # 使用正确的8月配置
            activity_code="SH-AUG",
            city="SH",
            housekeeper_key_format="管家_服务商",
            storage_type="sqlite",
            enable_dual_track=False,  # 8月还没有双轨统计
            db_path="performance_data.db"
        )
        
        logging.info(f"创建处理管道成功: {config.activity_code}")
        
        # 获取合同数据
        contract_data = _get_shanghai_contract_data()
        logging.info(f"获取到 {len(contract_data)} 个合同数据")
        
        # 处理数据
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")
        
        # 生成输出和发送通知
        csv_file = _generate_csv_output(processed_records, config)
        _send_notifications(processed_records, config)
        
        return processed_records
        
    except Exception as e:
        logging.error(f"上海8月任务执行失败: {e}")
        raise


def signing_and_sales_incentive_sep_shanghai_v2() -> List[PerformanceRecord]:
    """
    重构后的上海9月Job函数
    
    替代原有的signing_and_sales_incentive_sep_shanghai函数
    支持双轨统计（平台单 vs 自引单）和项目地址去重
    """
    logging.info("开始执行上海9月销售激励任务（重构版）")
    
    try:
        # 使用9月配置，启用双轨统计
        pipeline, config, store = create_standard_pipeline(
            config_key="SH-2025-09",
            activity_code="SH-SEP",
            city="SH",
            housekeeper_key_format="管家_服务商",
            storage_type="sqlite",
            enable_dual_track=True,  # 启用双轨统计
            db_path="performance_data.db"
        )
        
        logging.info(f"创建处理管道成功: {config.activity_code}")
        
        # 获取合同数据（包含双轨统计字段）
        contract_data = _get_shanghai_contract_data_with_dual_track()
        logging.info(f"获取到 {len(contract_data)} 个合同数据（支持双轨统计）")
        
        # 处理数据
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")
        
        # 生成输出和发送通知
        csv_file = _generate_csv_output_with_dual_track(processed_records, config)
        _send_notifications(processed_records, config)
        
        return processed_records
        
    except Exception as e:
        logging.error(f"上海9月任务执行失败: {e}")
        raise


# 辅助函数 - 保持与现有系统的兼容性

def _get_shanghai_contract_data() -> List[Dict]:
    """获取上海合同数据（模拟现有API调用）"""
    logging.info("从Metabase获取上海合同数据...")
    
    # TODO: 替换为实际的API调用
    # from modules.request_module import get_data_from_metabase
    # return get_data_from_metabase(api_url, headers)
    
    # 示例数据
    return [
        {
            '合同ID(_id)': '2025010812345701',
            '管家(serviceHousekeeper)': '王五',
            '服务商(orgName)': '上海精品服务',
            '合同金额(adjustRefundMoney)': 18000,
            '支付金额(paidAmount)': 15000,
            '款项来源类型(tradeIn)': 0,  # 平台单
            '活动城市(province)': '上海',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 10:00:00'
        }
    ]


def _get_shanghai_contract_data_with_dual_track() -> List[Dict]:
    """获取上海合同数据（支持双轨统计）"""
    logging.info("从Metabase获取上海合同数据（支持双轨统计）...")
    
    # 示例数据，包含平台单和自引单
    return [
        {
            '合同ID(_id)': '2025010812345701',
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
            '合同ID(_id)': '2025010812345702',
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
            '合同ID(_id)': '2025010812345703',
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


def _generate_csv_output(records: List[PerformanceRecord], config) -> str:
    """生成CSV输出文件"""
    import csv
    from datetime import datetime
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"performance_data_{config.activity_code}_{timestamp}.csv"
    
    if not records:
        logging.warning("没有记录需要输出")
        return csv_file
    
    # 转换记录为字典格式
    record_dicts = [record.to_dict() for record in records]
    
    # 写入CSV文件
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if record_dicts:
            writer = csv.DictWriter(f, fieldnames=record_dicts[0].keys())
            writer.writeheader()
            writer.writerows(record_dicts)
    
    logging.info(f"CSV文件生成完成: {csv_file}, {len(records)} 条记录")
    return csv_file


def _generate_csv_output_with_dual_track(records: List[PerformanceRecord], config) -> str:
    """生成包含双轨统计的CSV输出文件"""
    import csv
    from datetime import datetime
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = f"performance_data_{config.activity_code}_dual_track_{timestamp}.csv"
    
    if not records:
        logging.warning("没有记录需要输出")
        return csv_file
    
    # 转换记录为字典格式，包含双轨统计字段
    record_dicts = []
    for record in records:
        record_dict = record.to_dict()
        
        # 添加双轨统计特有字段
        record_dict.update({
            '管家ID(serviceHousekeeperId)': record.contract_data.raw_data.get('管家ID(serviceHousekeeperId)', ''),
            '客户联系地址(contactsAddress)': record.contract_data.raw_data.get('客户联系地址(contactsAddress)', ''),
            '项目地址(projectAddress)': record.contract_data.raw_data.get('项目地址(projectAddress)', '')
        })
        
        record_dicts.append(record_dict)
    
    # 写入CSV文件
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if record_dicts:
            writer = csv.DictWriter(f, fieldnames=record_dicts[0].keys())
            writer.writeheader()
            writer.writerows(record_dicts)
    
    logging.info(f"双轨统计CSV文件生成完成: {csv_file}, {len(records)} 条记录")
    return csv_file


def _send_notifications(records: List[PerformanceRecord], config):
    """发送通知"""
    # TODO: 集成现有的上海通知模块
    # from modules.notification_module import notify_awards_shanghai_generic
    # notify_awards_shanghai_generic(records, config)
    
    # 统计需要发送通知的记录
    notification_records = [r for r in records if r.rewards]
    logging.info(f"需要发送通知的记录: {len(notification_records)} 条")
    
    # 模拟通知发送
    for record in notification_records:
        reward_names = [r.reward_name for r in record.rewards]
        housekeeper_key = f"{record.contract_data.housekeeper}_{record.contract_data.service_provider}"
        logging.info(f"发送通知: {housekeeper_key} 获得奖励 {reward_names}")


# 兼容性函数 - 保持与现有调用方式的兼容

def signing_and_sales_incentive_apr_shanghai():
    """兼容性包装函数 - 上海4月"""
    return signing_and_sales_incentive_apr_shanghai_v2()


def signing_and_sales_incentive_aug_shanghai():
    """兼容性包装函数 - 上海8月"""
    return signing_and_sales_incentive_aug_shanghai_v2()


def signing_and_sales_incentive_sep_shanghai():
    """兼容性包装函数 - 上海9月"""
    return signing_and_sales_incentive_sep_shanghai_v2()


if __name__ == "__main__":
    # 测试上海Job函数
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("测试上海4月Job函数...")
    records_apr = signing_and_sales_incentive_apr_shanghai_v2()
    print(f"上海4月处理完成: {len(records_apr)} 条记录")
    
    print("\n测试上海9月Job函数（双轨统计）...")
    records_sep = signing_and_sales_incentive_sep_shanghai_v2()
    print(f"上海9月处理完成: {len(records_sep)} 条记录")
