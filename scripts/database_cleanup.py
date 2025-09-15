#!/usr/bin/env python3
"""
数据库清理工具

用于集成测试前清空数据库，确保测试环境干净。
这是端到端测试的必要步骤，模拟真实的手工集成测试环境。

使用方法:
    python scripts/database_cleanup.py --all
    python scripts/database_cleanup.py --activity BJ-SEP
    python scripts/database_cleanup.py --activity SH-SEP
    python scripts/database_cleanup.py --tables performance_records,notification_queue
"""

import sys
import os
import sqlite3
import argparse
import logging
from datetime import datetime
from typing import List, Optional

# 添加modules路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'database_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

class DatabaseCleaner:
    """数据库清理器"""
    
    def __init__(self, db_path: str = 'performance_data.db'):
        self.db_path = db_path
        self.conn = None
        
        # 定义可清理的表
        self.cleanable_tables = {
            'performance_records': '业绩记录表',
            'notification_queue': '通知队列表',
            'housekeeper_stats': '管家统计表',
            'activity_summary': '活动汇总表'
        }
        
        # 定义活动代码
        self.activity_codes = {
            'BJ-SEP': '北京9月销售激励',
            'SH-SEP': '上海9月销售激励',
            'BJ-AUG': '北京8月销售激励',
            'SH-AUG': '上海8月销售激励'
        }

    def connect(self) -> bool:
        """连接数据库"""
        try:
            if not os.path.exists(self.db_path):
                logging.error(f"数据库文件不存在: {self.db_path}")
                return False
                
            self.conn = sqlite3.connect(self.db_path)
            logging.info(f"成功连接数据库: {self.db_path}")
            return True
        except Exception as e:
            logging.error(f"连接数据库失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("数据库连接已关闭")

    def get_table_info(self, table_name: str) -> dict:
        """获取表信息"""
        try:
            cursor = self.conn.cursor()
            
            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            if not cursor.fetchone():
                return {'exists': False, 'count': 0}
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            return {'exists': True, 'count': count}
            
        except Exception as e:
            logging.error(f"获取表信息失败 {table_name}: {e}")
            return {'exists': False, 'count': 0}

    def clean_table_by_activity(self, table_name: str, activity_code: str) -> bool:
        """按活动代码清理表"""
        try:
            cursor = self.conn.cursor()
            
            # 检查表是否存在activity_code字段
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'activity_code' not in columns:
                logging.warning(f"表 {table_name} 没有activity_code字段，跳过")
                return True
            
            # 获取删除前的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE activity_code = ?", (activity_code,))
            before_count = cursor.fetchone()[0]
            
            if before_count == 0:
                logging.info(f"表 {table_name} 中没有活动 {activity_code} 的记录")
                return True
            
            # 执行删除
            cursor.execute(f"DELETE FROM {table_name} WHERE activity_code = ?", (activity_code,))
            deleted_count = cursor.rowcount
            
            self.conn.commit()
            
            logging.info(f"表 {table_name}: 删除了 {deleted_count} 条活动 {activity_code} 的记录")
            return True
            
        except Exception as e:
            logging.error(f"清理表失败 {table_name} (活动 {activity_code}): {e}")
            self.conn.rollback()
            return False

    def clean_table_all(self, table_name: str) -> bool:
        """清空整个表"""
        try:
            cursor = self.conn.cursor()
            
            # 获取删除前的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            before_count = cursor.fetchone()[0]
            
            if before_count == 0:
                logging.info(f"表 {table_name} 已经为空")
                return True
            
            # 执行删除
            cursor.execute(f"DELETE FROM {table_name}")
            deleted_count = cursor.rowcount
            
            self.conn.commit()
            
            logging.info(f"表 {table_name}: 删除了 {deleted_count} 条记录（全部清空）")
            return True
            
        except Exception as e:
            logging.error(f"清空表失败 {table_name}: {e}")
            self.conn.rollback()
            return False

    def vacuum_database(self) -> bool:
        """压缩数据库"""
        try:
            logging.info("开始压缩数据库...")
            self.conn.execute("VACUUM")
            logging.info("数据库压缩完成")
            return True
        except Exception as e:
            logging.error(f"数据库压缩失败: {e}")
            return False

    def generate_cleanup_report(self, tables: List[str], activity_code: Optional[str] = None) -> str:
        """生成清理报告"""
        report = []
        report.append("# 数据库清理报告")
        report.append(f"**清理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**数据库**: {self.db_path}")
        
        if activity_code:
            report.append(f"**清理范围**: 活动 {activity_code}")
        else:
            report.append(f"**清理范围**: 全部数据")
        
        report.append("")
        
        # 表状态
        report.append("## 表状态")
        for table_name in tables:
            info = self.get_table_info(table_name)
            if info['exists']:
                status = "✅ 已清空" if info['count'] == 0 else f"⚠️ 还有 {info['count']} 条记录"
                report.append(f"- **{table_name}**: {status}")
            else:
                report.append(f"- **{table_name}**: ❌ 表不存在")
        
        report.append("")
        
        # 清理建议
        if activity_code:
            report.append("## 清理验证")
            report.append(f"请确认活动 {activity_code} 的相关数据已完全清除，可以开始集成测试。")
        else:
            report.append("## 清理验证")
            report.append("请确认所有相关数据已完全清除，可以开始集成测试。")
        
        return "\n".join(report)

    def clean_for_integration_test(self, activity_code: Optional[str] = None, 
                                 tables: Optional[List[str]] = None) -> bool:
        """为集成测试清理数据库"""
        if not self.connect():
            return False
        
        try:
            # 确定要清理的表
            if tables:
                target_tables = tables
            else:
                target_tables = list(self.cleanable_tables.keys())
            
            logging.info("=" * 60)
            logging.info("开始数据库清理（集成测试准备）")
            logging.info("=" * 60)
            
            if activity_code:
                logging.info(f"清理范围: 活动 {activity_code}")
            else:
                logging.info("清理范围: 全部数据")
            
            logging.info(f"目标表: {', '.join(target_tables)}")
            
            # 执行清理
            all_success = True
            for table_name in target_tables:
                if table_name not in self.cleanable_tables:
                    logging.warning(f"未知表名: {table_name}，跳过")
                    continue
                
                logging.info(f"\n清理表: {table_name} ({self.cleanable_tables[table_name]})")
                
                if activity_code:
                    success = self.clean_table_by_activity(table_name, activity_code)
                else:
                    success = self.clean_table_all(table_name)
                
                if not success:
                    all_success = False
            
            # 压缩数据库
            if all_success:
                self.vacuum_database()
            
            # 生成报告
            report = self.generate_cleanup_report(target_tables, activity_code)
            
            # 保存报告
            report_file = f"database_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logging.info(f"\n清理报告已保存: {report_file}")
            
            if all_success:
                logging.info("\n✅ 数据库清理完成！可以开始集成测试")
            else:
                logging.error("\n❌ 数据库清理过程中发现错误，请检查日志")
            
            return all_success
            
        finally:
            self.disconnect()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库清理工具（集成测试准备）')
    parser.add_argument('--all', action='store_true', help='清空所有相关表的所有数据')
    parser.add_argument('--activity', help='按活动代码清理 (如: BJ-SEP, SH-SEP)')
    parser.add_argument('--tables', help='指定要清理的表，用逗号分隔')
    parser.add_argument('--db', default='performance_data.db', help='数据库文件路径')
    parser.add_argument('--dry-run', action='store_true', help='只显示将要执行的操作，不实际执行')
    
    args = parser.parse_args()
    
    # 参数验证
    if not args.all and not args.activity:
        print("错误: 必须指定 --all 或 --activity 参数")
        parser.print_help()
        return 1
    
    if args.all and args.activity:
        print("错误: --all 和 --activity 参数不能同时使用")
        return 1
    
    setup_logging()
    
    # 解析表列表
    tables = None
    if args.tables:
        tables = [t.strip() for t in args.tables.split(',')]
    
    # 创建清理器
    cleaner = DatabaseCleaner(args.db)
    
    # 显示操作预览
    if args.dry_run:
        print("🔍 预览模式 - 将要执行的操作:")
        if args.all:
            print("- 清空所有相关表的所有数据")
        else:
            print(f"- 清空活动 {args.activity} 的相关数据")
        
        if tables:
            print(f"- 目标表: {', '.join(tables)}")
        else:
            print(f"- 目标表: {', '.join(cleaner.cleanable_tables.keys())}")
        
        print("\n要实际执行，请移除 --dry-run 参数")
        return 0
    
    # 执行清理
    activity_code = None if args.all else args.activity
    success = cleaner.clean_for_integration_test(activity_code, tables)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
