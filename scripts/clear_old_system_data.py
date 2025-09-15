#!/usr/bin/env python3
"""
清空旧系统数据脚本
版本: v1.0
创建日期: 2025-09-15

用途：清空旧系统的所有数据文件，包括：
- CSV数据文件（合同数据、业绩数据）
- JSON状态文件（发送状态、任务状态）
- SQLite数据库文件
- 归档文件
- 临时文件

使用方法：
python scripts/clear_old_system_data.py [--confirm] [--keep-archive]
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_data_files():
    """获取所有需要清理的数据文件列表"""
    
    # 基于config.py中的配置定义数据文件
    data_files = {
        # 北京地区数据文件
        'beijing': [
            'state/ContractData-BJ-Aug.csv',
            'state/PerformanceData-BJ-Aug.csv', 
            'state/send_status_bj_aug.json',
            'state/ContractData-BJ-Sep.csv',
            'state/PerformanceData-BJ-Sep.csv',
            'state/send_status_bj_sep.json',
        ],
        
        # 上海地区数据文件
        'shanghai': [
            'state/ContractData-SH-Aug.csv',
            'state/PerformanceData-SH-Aug.csv',
            'state/send_status_sh_aug.json',
            'state/ContractData-SH-Sep.csv', 
            'state/PerformanceData-SH-Sep.csv',
            'state/send_status_shanghai_sep.json',
        ],
        
        # 系统状态文件
        'system': [
            'state/pending_orders_reminder_status.json',
            'state/daily_service_report_record.csv',
            'state/daily_service_report_record.json',
            'state/sla_violations.json',
            'metabase_session.json',
        ],
        
        # 数据库文件
        'database': [
            'performance_data.db',
            'tasks.db',
        ],
        
        # 测试文件
        'test': [
            'modules/core/performance_data_BJ-JUN_20250908_083348.csv',
            'modules/core/tests/performance_data_SH-APR_20250908_085943.csv',
            'modules/core/tests/performance_data_SH-AUG_20250908_085943.csv',
            'modules/core/tests/performance_data_SH-SEP_dual_track_20250908_085943.csv',
        ]
    }
    
    return data_files

def clear_files(file_list, category_name, dry_run=False):
    """清理指定的文件列表"""
    cleared_count = 0
    
    logging.info(f"🗂️  清理 {category_name} 文件...")
    
    for file_path in file_list:
        if os.path.exists(file_path):
            if dry_run:
                logging.info(f"  [DRY RUN] 将删除: {file_path}")
            else:
                try:
                    os.remove(file_path)
                    logging.info(f"  ✅ 已删除: {file_path}")
                    cleared_count += 1
                except Exception as e:
                    logging.error(f"  ❌ 删除失败: {file_path} - {e}")
        else:
            logging.debug(f"  ⏭️  文件不存在: {file_path}")
    
    if not dry_run:
        logging.info(f"  📊 {category_name}: 清理了 {cleared_count} 个文件")
    
    return cleared_count

def clear_archive_directory(keep_archive=False, dry_run=False):
    """清理归档目录"""
    archive_dir = 'archive'
    
    if not os.path.exists(archive_dir):
        logging.info("📁 归档目录不存在，跳过")
        return 0
    
    if keep_archive:
        logging.info("📁 保留归档目录（--keep-archive 选项）")
        return 0
    
    cleared_count = 0
    
    logging.info("🗂️  清理归档目录...")
    
    for root, dirs, files in os.walk(archive_dir, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            if dry_run:
                logging.info(f"  [DRY RUN] 将删除: {file_path}")
            else:
                try:
                    os.remove(file_path)
                    logging.debug(f"  ✅ 已删除: {file_path}")
                    cleared_count += 1
                except Exception as e:
                    logging.error(f"  ❌ 删除失败: {file_path} - {e}")
        
        # 删除空目录
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if dry_run:
                logging.info(f"  [DRY RUN] 将删除目录: {dir_path}")
            else:
                try:
                    os.rmdir(dir_path)
                    logging.debug(f"  ✅ 已删除目录: {dir_path}")
                except Exception as e:
                    logging.debug(f"  ⏭️  目录非空或删除失败: {dir_path}")
    
    # 删除归档根目录
    if not dry_run:
        try:
            os.rmdir(archive_dir)
            logging.info(f"  ✅ 已删除归档根目录: {archive_dir}")
        except Exception as e:
            logging.debug(f"  ⏭️  归档根目录删除失败: {e}")
    
    if not dry_run:
        logging.info(f"  📊 归档目录: 清理了 {cleared_count} 个文件")
    
    return cleared_count

def main():
    parser = argparse.ArgumentParser(description='清空旧系统数据')
    parser.add_argument('--confirm', action='store_true', 
                       help='确认执行清理（不加此参数将只显示要删除的文件）')
    parser.add_argument('--keep-archive', action='store_true',
                       help='保留归档目录')
    parser.add_argument('--category', choices=['beijing', 'shanghai', 'system', 'database', 'test', 'all'],
                       default='all', help='指定清理的数据类别')
    
    args = parser.parse_args()
    
    # 检查是否在正确的目录
    if not os.path.exists('modules/config.py'):
        logging.error("❌ 请在项目根目录下运行此脚本")
        sys.exit(1)
    
    dry_run = not args.confirm
    
    if dry_run:
        logging.info("🔍 预览模式 - 显示将要删除的文件（使用 --confirm 参数实际执行删理）")
    else:
        logging.info("🗑️  开始清理旧系统数据...")
    
    data_files = get_data_files()
    total_cleared = 0
    
    # 根据选择的类别清理文件
    if args.category == 'all':
        categories = data_files.keys()
    else:
        categories = [args.category]
    
    for category in categories:
        if category in data_files:
            cleared = clear_files(data_files[category], category, dry_run)
            total_cleared += cleared
    
    # 清理归档目录
    if args.category in ['all', 'system']:
        archive_cleared = clear_archive_directory(args.keep_archive, dry_run)
        total_cleared += archive_cleared
    
    if dry_run:
        logging.info("🔍 预览完成 - 使用 --confirm 参数实际执行清理")
    else:
        logging.info(f"🎉 清理完成！总共清理了 {total_cleared} 个文件")

if __name__ == '__main__':
    main()
