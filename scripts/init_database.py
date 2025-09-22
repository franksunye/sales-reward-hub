#!/usr/bin/env python3
"""
数据库初始化脚本
创建必要的数据库表
"""

import sqlite3
import os
import sys

def init_database():
    """初始化数据库，确保新架构能正确创建schema"""

    # 数据库文件路径
    db_path = 'performance_data.db'

    try:
        # 如果数据库文件存在，删除它以确保新架构创建正确的schema
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ 删除旧数据库文件: {db_path}")

        # 创建一个空的数据库文件，让新架构自己初始化schema
        conn = sqlite3.connect(db_path)

        # 只创建 tasks 表（旧架构需要的通知表）
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

        print("✅ 数据库初始化成功")
        print(f"📊 数据库文件: {db_path}")
        print("💡 新架构将自动创建正确的performance_data表")

        return True

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 数据库初始化工具")
    print("=" * 40)
    
    if init_database():
        print("🎉 数据库初始化完成")
        sys.exit(0)
    else:
        print("💥 数据库初始化失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
