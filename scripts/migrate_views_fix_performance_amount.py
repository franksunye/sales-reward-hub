#!/usr/bin/env python3
"""
数据库视图迁移脚本 - 修复 performance_amount 统计问题

问题描述：
- 数据库视图中的多个金额字段统计了所有合同（包括历史合同）
- 需求是累计金额统计只计入新工单，不计入历史工单
- 历史工单仅作为后台计算的逻辑数据，不参与前端的数据统计

修复内容：
1. 重新创建 housekeeper_stats 视图，所有累计金额字段只统计非历史合同
2. 重新创建 project_stats 视图，所有累计金额字段只统计非历史合同
3. 重新创建 activity_stats 视图，所有累计金额字段只统计非历史合同

使用方法:
    python scripts/migrate_views_fix_performance_amount.py --db performance_data.db
    python scripts/migrate_views_fix_performance_amount.py --db performance_data.db --dry-run
"""

import sqlite3
import os
import sys
import argparse
import logging
from datetime import datetime

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'migrate_views_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def check_database_exists(db_path: str) -> bool:
    """检查数据库文件是否存在"""
    if not os.path.exists(db_path):
        logging.error(f"数据库文件不存在: {db_path}")
        return False
    return True

def backup_database(db_path: str) -> str:
    """备份数据库文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logging.info(f"数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"备份数据库失败: {e}")
        raise

def check_views_exist(conn: sqlite3.Connection) -> dict:
    """检查视图是否存在"""
    cursor = conn.cursor()
    
    views_to_check = ['housekeeper_stats', 'project_stats', 'activity_stats']
    view_status = {}
    
    for view_name in views_to_check:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='view' AND name=?
        """, (view_name,))
        
        exists = cursor.fetchone() is not None
        view_status[view_name] = exists
        
        if exists:
            logging.info(f"✅ 视图 {view_name} 存在")
        else:
            logging.warning(f"⚠️ 视图 {view_name} 不存在")
    
    return view_status

def drop_views(conn: sqlite3.Connection, dry_run: bool = False) -> bool:
    """删除现有视图"""
    views_to_drop = ['housekeeper_stats', 'project_stats', 'activity_stats']
    
    try:
        cursor = conn.cursor()
        
        for view_name in views_to_drop:
            sql = f"DROP VIEW IF EXISTS {view_name}"
            
            if dry_run:
                logging.info(f"[DRY RUN] 将执行: {sql}")
            else:
                cursor.execute(sql)
                logging.info(f"✅ 删除视图: {view_name}")
        
        if not dry_run:
            conn.commit()
            
        return True
        
    except Exception as e:
        logging.error(f"删除视图失败: {e}")
        if not dry_run:
            conn.rollback()
        return False

def create_fixed_views(conn: sqlite3.Connection, dry_run: bool = False) -> bool:
    """创建修复后的视图"""
    
    # 修复后的 housekeeper_stats 视图
    housekeeper_stats_sql = """
    CREATE VIEW housekeeper_stats AS
    SELECT
        housekeeper,
        activity_code,
        COUNT(*) as contract_count,
        -- 🔧 修复：累计合同金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN is_historical = FALSE THEN contract_amount ELSE 0 END) as total_amount,
        -- 🔧 修复：累计计入业绩金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN is_historical = FALSE THEN performance_amount ELSE 0 END) as performance_amount,
        -- 双轨统计（上海特有）
        SUM(CASE WHEN order_type = 'platform' THEN 1 ELSE 0 END) as platform_count,
        -- 🔧 修复：累计平台单金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN order_type = 'platform' AND is_historical = FALSE THEN contract_amount ELSE 0 END) as platform_amount,
        SUM(CASE WHEN order_type = 'self_referral' THEN 1 ELSE 0 END) as self_referral_count,
        -- 🔧 修复：累计自引单金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN order_type = 'self_referral' AND is_historical = FALSE THEN contract_amount ELSE 0 END) as self_referral_amount,
        -- 历史合同统计（北京9月特有）
        SUM(CASE WHEN is_historical = TRUE THEN 1 ELSE 0 END) as historical_count,
        SUM(CASE WHEN is_historical = FALSE THEN 1 ELSE 0 END) as new_count
    FROM performance_data
    GROUP BY housekeeper, activity_code
    """
    
    # 修复后的 project_stats 视图
    project_stats_sql = """
    CREATE VIEW project_stats AS
    SELECT
        project_id,
        activity_code,
        COUNT(*) as contract_count,
        -- 🔧 修复：工单累计合同金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN is_historical = FALSE THEN contract_amount ELSE 0 END) as total_amount,
        -- 🔧 修复：工单累计业绩金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN is_historical = FALSE THEN performance_amount ELSE 0 END) as performance_amount
    FROM performance_data
    WHERE project_id IS NOT NULL
    GROUP BY project_id, activity_code
    """
    
    # 修复后的 activity_stats 视图
    activity_stats_sql = """
    CREATE VIEW activity_stats AS
    SELECT
        activity_code,
        COUNT(*) as total_contracts,
        COUNT(DISTINCT housekeeper) as unique_housekeepers,
        -- 🔧 修复：活动总合同金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN is_historical = FALSE THEN contract_amount ELSE 0 END) as total_amount,
        -- 🔧 修复：活动总业绩金额仅计入新工单，不计入历史工单
        SUM(CASE WHEN is_historical = FALSE THEN performance_amount ELSE 0 END) as total_performance_amount,
        -- 🔧 修复：平均合同金额仅基于新工单计算，不包含历史工单
        AVG(CASE WHEN is_historical = FALSE THEN contract_amount ELSE NULL END) as avg_contract_amount,
        MIN(created_at) as first_contract_time,
        MAX(created_at) as last_contract_time
    FROM performance_data
    GROUP BY activity_code
    """
    
    views_to_create = [
        ('housekeeper_stats', housekeeper_stats_sql),
        ('project_stats', project_stats_sql),
        ('activity_stats', activity_stats_sql)
    ]
    
    try:
        cursor = conn.cursor()
        
        for view_name, sql in views_to_create:
            if dry_run:
                logging.info(f"[DRY RUN] 将创建视图: {view_name}")
                logging.debug(f"[DRY RUN] SQL: {sql}")
            else:
                cursor.execute(sql)
                logging.info(f"✅ 创建视图: {view_name}")
        
        if not dry_run:
            conn.commit()
            
        return True
        
    except Exception as e:
        logging.error(f"创建视图失败: {e}")
        if not dry_run:
            conn.rollback()
        return False

def update_schema_version(conn: sqlite3.Connection, dry_run: bool = False) -> bool:
    """更新schema版本信息"""
    version = "1.0.2"
    description = "Fix all amount calculations to exclude historical contracts"
    
    try:
        cursor = conn.cursor()
        
        sql = """
        INSERT OR REPLACE INTO schema_version (version, description, applied_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """
        
        if dry_run:
            logging.info(f"[DRY RUN] 将更新schema版本到: {version}")
        else:
            cursor.execute(sql, (version, description))
            conn.commit()
            logging.info(f"✅ 更新schema版本到: {version}")
            
        return True
        
    except Exception as e:
        logging.error(f"更新schema版本失败: {e}")
        if not dry_run:
            conn.rollback()
        return False

def verify_migration(conn: sqlite3.Connection) -> bool:
    """验证迁移结果"""
    try:
        cursor = conn.cursor()
        
        # 检查视图是否存在
        view_status = check_views_exist(conn)
        all_views_exist = all(view_status.values())
        
        if not all_views_exist:
            logging.error("❌ 部分视图创建失败")
            return False
        
        # 测试视图查询
        test_queries = [
            "SELECT COUNT(*) FROM housekeeper_stats",
            "SELECT COUNT(*) FROM project_stats", 
            "SELECT COUNT(*) FROM activity_stats"
        ]
        
        for query in test_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()[0]
                logging.info(f"✅ 视图查询测试通过: {query} -> {result} 行")
            except Exception as e:
                logging.error(f"❌ 视图查询测试失败: {query} -> {e}")
                return False
        
        # 检查schema版本
        cursor.execute("SELECT version, description FROM schema_version ORDER BY applied_at DESC LIMIT 1")
        version_info = cursor.fetchone()
        if version_info:
            logging.info(f"✅ 当前schema版本: {version_info[0]} - {version_info[1]}")
        
        return True
        
    except Exception as e:
        logging.error(f"验证迁移失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库视图迁移脚本 - 修复 performance_amount 统计问题')
    parser.add_argument('--db', default='performance_data.db', help='数据库文件路径')
    parser.add_argument('--dry-run', action='store_true', help='只显示将要执行的操作，不实际执行')
    parser.add_argument('--no-backup', action='store_true', help='跳过数据库备份（不推荐）')
    
    args = parser.parse_args()
    
    setup_logging()
    
    logging.info("🔧 数据库视图迁移脚本 - 修复 performance_amount 统计问题")
    logging.info("=" * 60)
    
    # 检查数据库文件
    if not check_database_exists(args.db):
        return 1
    
    # 备份数据库
    if not args.dry_run and not args.no_backup:
        try:
            backup_path = backup_database(args.db)
            logging.info(f"💾 数据库已备份，如有问题可恢复: cp {backup_path} {args.db}")
        except Exception as e:
            logging.error(f"备份失败，停止迁移: {e}")
            return 1
    
    # 连接数据库
    try:
        conn = sqlite3.connect(args.db)
        logging.info(f"📊 连接数据库: {args.db}")
        
        # 检查当前视图状态
        logging.info("\n📋 检查当前视图状态:")
        view_status = check_views_exist(conn)
        
        # 执行迁移
        logging.info(f"\n🚀 开始迁移 {'(预览模式)' if args.dry_run else ''}:")
        
        # 1. 删除现有视图
        if not drop_views(conn, args.dry_run):
            logging.error("❌ 删除视图失败，停止迁移")
            return 1
        
        # 2. 创建修复后的视图
        if not create_fixed_views(conn, args.dry_run):
            logging.error("❌ 创建视图失败，停止迁移")
            return 1
        
        # 3. 更新schema版本
        if not update_schema_version(conn, args.dry_run):
            logging.error("❌ 更新schema版本失败")
            return 1
        
        # 4. 验证迁移结果
        if not args.dry_run:
            logging.info("\n🔍 验证迁移结果:")
            if not verify_migration(conn):
                logging.error("❌ 迁移验证失败")
                return 1
        
        if args.dry_run:
            logging.info("\n✅ 预览完成！要实际执行迁移，请移除 --dry-run 参数")
        else:
            logging.info("\n✅ 迁移完成！performance_amount 现在只统计新工单，不包括历史工单")
            logging.info("💡 建议运行测试验证修复效果")
        
        return 0
        
    except Exception as e:
        logging.error(f"迁移过程中发生错误: {e}")
        return 1
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
