#!/usr/bin/env python3
"""
验证视图定义脚本
"""

import sqlite3
import sys

def verify_views(db_path: str):
    """验证视图定义"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有视图的定义
        cursor.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='view' 
            ORDER BY name
        """)
        
        views = cursor.fetchall()
        
        print("📋 当前数据库中的视图定义:")
        print("=" * 60)
        
        for view_name, view_sql in views:
            print(f"\n🔍 视图: {view_name}")
            print("-" * 40)
            print(view_sql)
            print()
        
        # 检查schema版本
        cursor.execute("SELECT version, description, applied_at FROM schema_version ORDER BY applied_at DESC LIMIT 1")
        version_info = cursor.fetchone()
        if version_info:
            print(f"📊 Schema版本: {version_info[0]}")
            print(f"📝 描述: {version_info[1]}")
            print(f"🕒 应用时间: {version_info[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'performance_data.db'
    verify_views(db_path)
