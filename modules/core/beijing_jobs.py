"""
销售激励系统重构 - 北京Job函数迁移
版本: v1.0
创建日期: 2025-01-08

重构后的北京Job函数，使用新的核心架构。
替代现有的重复Job函数，消除全局副作用。
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


def signing_and_sales_incentive_jun_beijing_v2() -> List[PerformanceRecord]:
    """
    重构后的北京6月Job函数
    
    替代原有的signing_and_sales_incentive_jun_beijing函数
    使用新的核心架构，消除重复代码和全局副作用
    """
    logging.info("开始执行北京6月销售激励任务（重构版）")
    
    try:
        # 1. 创建标准处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-06",
            activity_code="BJ-JUN",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_project_limit=True,  # 北京启用工单金额上限
            db_path="performance_data.db"
        )
        
        logging.info(f"创建处理管道成功: {config.activity_code}")
        
        # 2. 获取合同数据（保持现有API调用方式）
        contract_data = _get_contract_data_from_metabase()
        logging.info(f"获取到 {len(contract_data)} 个合同数据")
        
        # 3. 处理数据
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")
        
        # 4. 生成CSV文件（可配置）
        if config.enable_csv_output:
            csv_file = _generate_csv_output(processed_records, config)
            logging.info(f"生成CSV文件: {csv_file}")
        else:
            logging.info("CSV输出已禁用，数据仅保存到数据库")
        
        # 5. 发送通知（保持现有通知逻辑）
        _send_notifications(processed_records, config)
        logging.info("通知发送完成")
        
        # 6. 获取处理摘要
        summary = pipeline.get_processing_summary()
        logging.info(f"处理摘要: {summary}")
        
        return processed_records
        
    except Exception as e:
        logging.error(f"北京6月任务执行失败: {e}")
        import traceback
        logging.error(f"详细错误: {traceback.format_exc()}")
        raise


def signing_and_sales_incentive_aug_beijing_v2() -> List[PerformanceRecord]:
    """
    重构后的北京8月Job函数
    
    替代原有的signing_and_sales_incentive_aug_beijing函数
    使用正确的配置，不再复用6月函数
    """
    logging.info("开始执行北京8月销售激励任务（重构版）")
    
    try:
        # 使用正确的8月配置
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-08",  # 使用正确的8月配置
            activity_code="BJ-AUG",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_project_limit=True,
            db_path="performance_data.db"
        )
        
        logging.info(f"创建处理管道成功: {config.activity_code}")
        
        # 获取合同数据
        contract_data = _get_contract_data_from_metabase()
        logging.info(f"获取到 {len(contract_data)} 个合同数据")
        
        # 处理数据
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")
        
        # 生成输出和发送通知
        if config.enable_csv_output:
            csv_file = _generate_csv_output(processed_records, config)
            logging.info(f"生成CSV文件: {csv_file}")
        _send_notifications(processed_records, config)
        
        return processed_records
        
    except Exception as e:
        logging.error(f"北京8月任务执行失败: {e}")
        raise


def signing_and_sales_incentive_sep_beijing_v2() -> List[PerformanceRecord]:
    """
    重构后的北京9月Job函数
    
    替代原有的signing_and_sales_incentive_sep_beijing函数
    消除全局副作用，支持历史合同处理
    """
    logging.info("开始执行北京9月销售激励任务（重构版）")
    
    try:
        # 使用正确的9月配置，支持历史合同
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-09",  # 直接使用正确配置
            activity_code="BJ-SEP",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_project_limit=True,
            enable_historical_contracts=True,  # 支持历史合同处理
            db_path="performance_data.db"
        )
        
        logging.info(f"创建处理管道成功: {config.activity_code}")
        
        # 获取合同数据（包含历史合同）
        contract_data = _get_contract_data_with_historical()
        logging.info(f"获取到 {len(contract_data)} 个合同数据（包含历史合同）")
        
        # 处理数据 - 无需全局副作用
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")
        
        # 生成输出和发送通知
        if config.enable_csv_output:
            csv_file = _generate_csv_output(processed_records, config)
            logging.info(f"生成CSV文件: {csv_file}")
        _send_notifications(processed_records, config)
        
        return processed_records
        
    except Exception as e:
        logging.error(f"北京9月任务执行失败: {e}")
        raise


# 辅助函数 - 保持与现有系统的兼容性

def _parse_metabase_response(response: dict) -> List[Dict]:
    """
    通用的Metabase API响应解析函数

    将Metabase API返回的原始数据（英文字段名）转换为标准格式（中文字段名）

    Args:
        response: Metabase API返回的响应字典

    Returns:
        转换后的合同数据列表，每个元素是包含中文字段名的字典
    """
    if not response or not isinstance(response, dict) or 'data' not in response:
        logging.warning("API响应为空或格式不正确")
        return []

    data = response['data']
    if not data or 'rows' not in data or 'cols' not in data:
        logging.warning("API数据格式不正确：缺少rows或cols字段")
        return []

    rows = data['rows']
    columns = data['cols']

    if not rows:
        logging.warning("没有获取到合同数据")
        return []

    # 构建字段名映射
    column_names = [col['name'] for col in columns]

    # 转换为字典格式，并映射到标准字段名
    contract_data = []
    for row in rows:
        raw_dict = dict(zip(column_names, row))

        # 🔧 关键修复：sourceType 字段处理
        # API 返回的 sourceType 可能是字符串或数字，需要转换为数字
        # 默认值为 2（平台单）
        source_type = raw_dict.get('sourceType', 2)
        if isinstance(source_type, str):
            try:
                source_type = int(source_type)
            except (ValueError, TypeError):
                source_type = 2  # 转换失败时默认为平台单

        # 映射到标准字段名（中文）
        contract_dict = {
            '合同ID(_id)': raw_dict.get('_id', ''),
            '活动城市(province)': raw_dict.get('province', ''),
            '工单编号(serviceAppointmentNum)': raw_dict.get('serviceAppointmentNum', ''),
            'Status': raw_dict.get('status', ''),
            '管家(serviceHousekeeper)': raw_dict.get('serviceHousekeeper', ''),
            '合同编号(contractdocNum)': raw_dict.get('contractdocNum', ''),
            '合同金额(adjustRefundMoney)': raw_dict.get('adjustRefundMoney', 0),
            '支付金额(paidAmount)': raw_dict.get('paidAmount', 0),
            '差额(difference)': raw_dict.get('difference', 0),
            'State': raw_dict.get('state', ''),
            '创建时间(createTime)': raw_dict.get('createTime', ''),
            '服务商(orgName)': raw_dict.get('orgName', ''),
            '签约时间(signedDate)': raw_dict.get('signedDate', ''),
            'Doorsill': raw_dict.get('Doorsill', 0),
            '款项来源类型(tradeIn)': raw_dict.get('tradeIn', ''),
            '转化率(conversion)': raw_dict.get('conversion', 0),
            '平均客单价(average)': raw_dict.get('average', 0),
            '管家ID(serviceHousekeeperId)': raw_dict.get('serviceHousekeeperId', ''),
            '工单类型(sourceType)': source_type,  # ✅ 使用转换后的数字值
            '联系地址(contactsAddress)': raw_dict.get('contactsAddress', ''),
            '项目地址(projectAddress)': raw_dict.get('projectAddress', ''),
        }
        contract_data.append(contract_dict)

    return contract_data


def _get_contract_data_from_metabase() -> List[Dict]:
    """获取合同数据（连接真实Metabase API）- 北京9月"""
    logging.info("从Metabase获取北京9月合同数据...")

    try:
        # 导入真实的API模块
        from modules.request_module import send_request_with_managed_session
        from modules.config import API_URL_BJ_SEP

        # 调用真实的Metabase API
        response = send_request_with_managed_session(API_URL_BJ_SEP)

        if response is None:
            logging.error("Metabase API调用失败")
            return []

        # 使用通用的解析函数
        contract_data = _parse_metabase_response(response)
        if contract_data:
            logging.info(f"从Metabase获取到 {len(contract_data)} 条合同数据")
        return contract_data

    except Exception as e:
        logging.error(f"获取Metabase数据失败: {e}")
        # 在真实环境测试中，如果API失败应该抛出异常而不是返回空数据
        raise


def _get_contract_data_with_source_type() -> List[Dict]:
    """获取包含sourceType字段的合同数据（北京10月专用）"""
    logging.info("从Metabase获取北京10月合同数据（包含双轨信息）...")

    try:
        # 导入真实的API模块
        from modules.request_module import send_request_with_managed_session
        from modules.config import API_URL_BJ_OCT  # 北京10月API端点

        # 调用真实的Metabase API
        response = send_request_with_managed_session(API_URL_BJ_OCT)

        if response is None:
            logging.error("Metabase API调用失败")
            return []

        # 使用通用的解析函数
        contract_data = _parse_metabase_response(response)
        if contract_data:
            logging.info(f"成功获取 {len(contract_data)} 个合同数据，包含sourceType字段")
        return contract_data

    except Exception as e:
        logging.error(f"获取北京10月合同数据失败: {e}")
        raise


def _get_contract_data_with_historical() -> List[Dict]:
    """获取合同数据（包含历史合同）"""
    logging.info("从Metabase获取合同数据（包含历史合同）...")

    # 获取基础数据
    contract_data = _get_contract_data_from_metabase()
    
    # 添加历史合同标记
    for contract in contract_data:
        # 如果历史合同编号字段有值且不为空，则标记为历史合同
        pc_contract_doc_num = contract.get('pcContractdocNum', '')
        if pc_contract_doc_num and str(pc_contract_doc_num).strip():
            contract['is_historical'] = True
        else:
            contract['is_historical'] = False
    
    return contract_data


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
            # 收集所有可能的字段名
            all_fieldnames = set()
            for record_dict in record_dicts:
                all_fieldnames.update(record_dict.keys())

            writer = csv.DictWriter(f, fieldnames=sorted(all_fieldnames))
            writer.writeheader()
            writer.writerows(record_dicts)
    
    logging.info(f"CSV文件生成完成: {csv_file}, {len(records)} 条记录")
    return csv_file


def _send_notifications(records: List[PerformanceRecord], config):
    """发送通知 - 使用新架构的通知服务"""
    from .notification_service import create_notification_service
    from .storage import create_data_store

    # 创建存储实例
    storage = create_data_store(
        storage_type="sqlite",
        db_path="performance_data.db"
    )

    # 创建通知服务
    notification_service = create_notification_service(storage, config)

    # 发送通知
    stats = notification_service.send_notifications()

    logging.info(f"通知发送完成 - 总计: {stats['total']}, 群通知: {stats['group_notifications']}, 奖励通知: {stats['award_notifications']}")


# 兼容性函数 - 保持与现有调用方式的兼容

def signing_and_sales_incentive_jun_beijing():
    """兼容性包装函数 - 北京6月"""
    return signing_and_sales_incentive_jun_beijing_v2()


def signing_and_sales_incentive_aug_beijing():
    """兼容性包装函数 - 北京8月"""
    return signing_and_sales_incentive_aug_beijing_v2()


def signing_and_sales_incentive_sep_beijing():
    """兼容性包装函数 - 北京9月"""
    return signing_and_sales_incentive_sep_beijing_v2()


def signing_and_sales_incentive_oct_beijing_v2() -> List[PerformanceRecord]:
    """
    北京2025年10月销售激励任务

    特性：
    - 混合奖励策略：幸运数字基于平台单，节节高基于总业绩
    - 双轨统计：支持平台单和自引单分别统计
    - 专用消息模板：结合北京特色的消息格式
    - 无自引单独立奖励：简化激励逻辑
    """
    logging.info("开始执行北京10月销售激励任务（重构版）")

    try:
        # 创建北京10月专用处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-10",  # 使用北京10月配置
            activity_code="BJ-OCT",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_project_limit=True,  # 启用工单金额上限
            enable_dual_track=True,  # 启用双轨统计
            enable_historical_contracts=False,  # 不涉及历史工单
            db_path="performance_data.db"
        )

        logging.info(f"创建处理管道成功: {config.activity_code}")

        # 获取合同数据（包含sourceType字段）
        contract_data = _get_contract_data_with_source_type()
        logging.info(f"获取到 {len(contract_data)} 个合同数据（包含双轨信息）")

        # 处理数据
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")

        # 生成输出和发送通知
        if config.enable_csv_output:
            csv_file = _generate_csv_output(processed_records, config)
            logging.info(f"生成CSV文件: {csv_file}")
        _send_notifications(processed_records, config)

        return processed_records

    except Exception as e:
        logging.error(f"北京10月任务执行失败: {e}")
        import traceback
        logging.error(f"详细错误: {traceback.format_exc()}")
        raise


def signing_and_sales_incentive_oct_beijing():
    """兼容性包装函数 - 北京10月"""
    return signing_and_sales_incentive_oct_beijing_v2()


def signing_and_sales_incentive_nov_beijing_v2() -> List[PerformanceRecord]:
    """
    北京2025年11月销售激励任务（新架构）

    特点：
    - 仅播报模式：不计算任何奖励
    - 仅处理平台单
    - 不处理历史合同
    - 简化消息模板
    """
    logging.info("开始执行北京11月销售激励任务（仅播报模式）")

    try:
        # 创建处理管道
        pipeline, config, store = create_standard_pipeline(
            config_key="BJ-2025-11",
            activity_code="BJ-NOV",
            city="BJ",
            housekeeper_key_format="管家",
            storage_type="sqlite",
            enable_dual_track=False,  # 不启用双轨统计
            enable_project_limit=False,  # 不启用工单上限
            enable_historical_contracts=False,  # 不处理历史合同
            db_path="performance_data.db"
        )

        logging.info(f"创建处理管道成功: {config.activity_code}")

        # 获取合同数据
        contract_data = _get_contract_data_from_metabase_nov()
        logging.info(f"获取到 {len(contract_data)} 个合同数据")

        # 处理数据（会自动过滤平台单）
        processed_records = pipeline.process(contract_data)
        logging.info(f"处理完成: {len(processed_records)} 条记录")

        # 生成输出和发送通知
        if config.enable_csv_output:
            csv_file = _generate_csv_output(processed_records, config)
            logging.info(f"生成CSV文件: {csv_file}")
        _send_notifications(processed_records, config)

        return processed_records

    except Exception as e:
        logging.error(f"北京11月任务执行失败: {e}")
        raise


def _get_contract_data_from_metabase_nov() -> List[Dict]:
    """获取北京11月合同数据"""
    logging.info("从Metabase获取北京11月合同数据...")

    try:
        from modules.config import API_URL_BJ_NOV
        from modules.request_module import send_request_with_managed_session

        response = send_request_with_managed_session(API_URL_BJ_NOV)

        if response is None:
            logging.error("Metabase API调用失败")
            return []

        # 使用通用的解析函数
        contract_data = _parse_metabase_response(response)
        if contract_data:
            logging.info(f"从Metabase获取到 {len(contract_data)} 条合同数据")
        return contract_data

    except Exception as e:
        logging.error(f"获取北京11月合同数据失败: {e}")
        raise


def signing_and_sales_incentive_nov_beijing():
    """兼容性包装函数 - 北京11月"""
    return signing_and_sales_incentive_nov_beijing_v2()


if __name__ == "__main__":
    # 测试北京Job函数
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("测试北京6月Job函数...")
    records_jun = signing_and_sales_incentive_jun_beijing_v2()
    print(f"北京6月处理完成: {len(records_jun)} 条记录")

    print("\n测试北京9月Job函数...")
    records_sep = signing_and_sales_incentive_sep_beijing_v2()
    print(f"北京9月处理完成: {len(records_sep)} 条记录")

    print("\n测试北京10月Job函数...")
    records_oct = signing_and_sales_incentive_oct_beijing_v2()
    print(f"北京10月处理完成: {len(records_oct)} 条记录")

    print("\n测试北京11月Job函数...")
    records_nov = signing_and_sales_incentive_nov_beijing_v2()
    print(f"北京11月处理完成: {len(records_nov)} 条记录")
