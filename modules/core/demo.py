#!/usr/bin/env python3
"""
销售激励系统重构 - 核心架构演示
版本: v1.0
创建日期: 2025-01-08

演示新架构的使用方法和优势。
"""

import os
import sys
import tempfile
import logging
from typing import List, Dict

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.core import (
    create_standard_pipeline,
    ContractData,
    City,
    OrderType
)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_contract_data() -> List[Dict]:
    """创建示例合同数据"""
    return [
        {
            '合同ID(_id)': '2025010812345678',  # 包含幸运数字8
            '管家(serviceHousekeeper)': '张三',
            '服务商(orgName)': '北京优质服务商',
            '合同金额(adjustRefundMoney)': 15000,
            '支付金额(paidAmount)': 10000,
            '工单编号(serviceAppointmentNum)': 'WO-2025-001',
            '款项来源类型(tradeIn)': 0,  # 平台单
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
            '服务商(orgName)': '上海精品服务',
            '合同金额(adjustRefundMoney)': 35000,
            '支付金额(paidAmount)': 30000,
            '款项来源类型(tradeIn)': 1,  # 自引单
            '项目地址(projectAddress)': '上海市浦东新区张江高科技园区',
            '活动城市(province)': '上海',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 12:00:00'
        }
    ]


def demo_beijing_processing():
    """演示北京数据处理"""
    logger.info("=== 北京数据处理演示 ===")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()
        
        try:
            # 创建北京处理管道
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-06",
                activity_code="BJ-JUN",
                city="BJ",
                db_path=temp_db.name,
                housekeeper_key_format="管家",
                enable_project_limit=True
            )
            
            logger.info(f"创建了北京处理管道: {config.activity_code}")
            
            # 准备测试数据
            contract_data = create_sample_contract_data()[:2]  # 只用北京的数据
            
            # 处理数据
            logger.info(f"开始处理 {len(contract_data)} 个合同...")
            records = pipeline.process(contract_data)
            
            logger.info(f"处理完成，生成了 {len(records)} 条记录")
            
            # 显示处理结果
            for record in records:
                logger.info(f"合同 {record.contract_data.contract_id}:")
                logger.info(f"  管家: {record.contract_data.housekeeper}")
                logger.info(f"  合同金额: {record.contract_data.contract_amount}")
                logger.info(f"  业绩金额: {record.performance_amount}")
                logger.info(f"  奖励: {[r.reward_name for r in record.rewards]}")
                logger.info(f"  管家累计: {record.housekeeper_stats.contract_count}单, {record.housekeeper_stats.total_amount}元")
            
            # 获取处理摘要
            summary = pipeline.get_processing_summary()
            logger.info(f"处理摘要: {summary}")
            
        finally:
            os.unlink(temp_db.name)


def demo_shanghai_processing():
    """演示上海数据处理（双轨统计）"""
    logger.info("\n=== 上海数据处理演示（双轨统计）===")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()
        
        try:
            # 创建上海处理管道
            pipeline, config, store = create_standard_pipeline(
                config_key="SH-2025-09",
                activity_code="SH-SEP",
                city="SH",
                db_path=temp_db.name,
                housekeeper_key_format="管家_服务商",
                enable_dual_track=True
            )
            
            logger.info(f"创建了上海处理管道: {config.activity_code}")
            
            # 准备测试数据
            contract_data = create_sample_contract_data()[2:]  # 只用上海的数据
            
            # 处理数据
            logger.info(f"开始处理 {len(contract_data)} 个合同...")
            records = pipeline.process(contract_data)
            
            logger.info(f"处理完成，生成了 {len(records)} 条记录")
            
            # 显示处理结果
            for record in records:
                logger.info(f"合同 {record.contract_data.contract_id}:")
                logger.info(f"  管家: {record.contract_data.housekeeper}")
                logger.info(f"  订单类型: {'自引单' if record.contract_data.order_type == OrderType.SELF_REFERRAL else '平台单'}")
                logger.info(f"  合同金额: {record.contract_data.contract_amount}")
                logger.info(f"  奖励: {[r.reward_name for r in record.rewards]}")
                logger.info(f"  双轨统计 - 平台单: {record.housekeeper_stats.platform_count}单/{record.housekeeper_stats.platform_amount}元")
                logger.info(f"  双轨统计 - 自引单: {record.housekeeper_stats.self_referral_count}单/{record.housekeeper_stats.self_referral_amount}元")
            
            # 获取处理摘要
            summary = pipeline.get_processing_summary()
            logger.info(f"处理摘要: {summary}")
            
        finally:
            os.unlink(temp_db.name)


def demo_performance_comparison():
    """演示性能对比"""
    logger.info("\n=== 性能对比演示 ===")
    
    import time
    
    # 创建大量测试数据
    large_contract_data = []
    for i in range(1000):
        large_contract_data.append({
            '合同ID(_id)': f'2025010800{i:06d}',
            '管家(serviceHousekeeper)': f'管家{i % 10}',  # 10个不同管家
            '服务商(orgName)': f'服务商{i % 5}',  # 5个不同服务商
            '合同金额(adjustRefundMoney)': 10000 + (i % 50000),
            '支付金额(paidAmount)': 8000 + (i % 40000),
            '款项来源类型(tradeIn)': i % 2,
            '活动城市(province)': '北京',
            'Status': '已签约',
            '创建时间(createTime)': '2025-01-08 10:00:00'
        })
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()
        
        try:
            # SQLite处理
            logger.info("测试SQLite处理性能...")
            start_time = time.time()
            
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-06",
                activity_code="BJ-JUN",
                city="BJ",
                db_path=temp_db.name
            )
            
            records = pipeline.process(large_contract_data)
            sqlite_time = time.time() - start_time
            
            logger.info(f"SQLite处理 {len(large_contract_data)} 个合同用时: {sqlite_time:.3f}秒")
            logger.info(f"平均每个合同: {sqlite_time/len(large_contract_data)*1000:.2f}毫秒")
            
            # 测试查询性能
            start_time = time.time()
            for i in range(100):
                exists = store.contract_exists(f'2025010800{i:06d}', 'BJ-JUN')
            query_time = time.time() - start_time
            
            logger.info(f"100次去重查询用时: {query_time:.3f}秒")
            logger.info(f"平均每次查询: {query_time/100*1000:.2f}毫秒")
            
        finally:
            os.unlink(temp_db.name)


def demo_data_consistency():
    """演示数据一致性"""
    logger.info("\n=== 数据一致性演示 ===")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()
        
        try:
            pipeline, config, store = create_standard_pipeline(
                config_key="BJ-2025-06",
                activity_code="BJ-JUN",
                city="BJ",
                db_path=temp_db.name
            )
            
            # 第一次处理
            contract_data = create_sample_contract_data()[:2]
            records1 = pipeline.process(contract_data)
            logger.info(f"第一次处理: {len(records1)} 条记录")
            
            # 第二次处理相同数据（应该被去重）
            records2 = pipeline.process(contract_data)
            logger.info(f"第二次处理: {len(records2)} 条记录（应该为0，因为去重）")
            
            # 添加新数据
            new_contract = {
                '合同ID(_id)': '2025010812345681',
                '管家(serviceHousekeeper)': '张三',
                '服务商(orgName)': '北京优质服务商',
                '合同金额(adjustRefundMoney)': 45000,
                '支付金额(paidAmount)': 40000,
                '工单编号(serviceAppointmentNum)': 'WO-2025-002',
                '款项来源类型(tradeIn)': 0,
                '活动城市(province)': '北京',
                'Status': '已签约',
                '创建时间(createTime)': '2025-01-08 13:00:00'
            }
            
            records3 = pipeline.process([new_contract])
            logger.info(f"处理新合同: {len(records3)} 条记录")
            
            # 检查管家累计统计
            if records3:
                stats = records3[0].housekeeper_stats
                logger.info(f"张三累计统计: {stats.contract_count}单, {stats.total_amount}元")
            
        finally:
            os.unlink(temp_db.name)


def main():
    """主演示函数"""
    logger.info("销售激励系统重构 - 核心架构演示")
    logger.info("=" * 50)
    
    try:
        # 演示北京处理
        demo_beijing_processing()
        
        # 演示上海处理
        demo_shanghai_processing()
        
        # 演示性能对比
        demo_performance_comparison()
        
        # 演示数据一致性
        demo_data_consistency()
        
        logger.info("\n演示完成！新架构的主要优势：")
        logger.info("1. 统一的处理管道，消除重复代码")
        logger.info("2. SQLite高性能存储，替代CSV文件扫描")
        logger.info("3. 配置驱动，支持不同城市和活动")
        logger.info("4. 数据一致性保证，支持事务")
        logger.info("5. 模块化设计，易于测试和维护")
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
