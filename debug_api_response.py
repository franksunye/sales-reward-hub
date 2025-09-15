#!/usr/bin/env python3
"""
调试API响应格式

检查真实Metabase API返回的字段名和数据结构
"""

import sys
import os
import json

# 添加modules路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

def debug_beijing_api():
    """调试北京API响应"""
    print("🔍 调试北京9月API响应...")
    
    try:
        from modules.request_module import send_request_with_managed_session
        from modules.config import API_URL_BJ_SEP
        
        response = send_request_with_managed_session(API_URL_BJ_SEP)
        
        if response and 'data' in response:
            data = response['data']
            
            print(f"📊 数据行数: {len(data.get('rows', []))}")
            print(f"📋 字段数: {len(data.get('cols', []))}")
            
            # 显示字段信息
            if 'cols' in data:
                print("\n📝 字段列表:")
                for i, col in enumerate(data['cols']):
                    print(f"  {i:2d}. {col.get('display_name', 'N/A'):30} | {col.get('name', 'N/A'):20} | {col.get('base_type', 'N/A')}")
            
            # 显示前几行数据
            if 'rows' in data and len(data['rows']) > 0:
                print(f"\n📋 前3行数据:")
                for i, row in enumerate(data['rows'][:3]):
                    print(f"  行{i+1}: {row[:5]}...")  # 只显示前5个字段
            
            # 保存完整响应到文件
            with open('beijing_api_response.json', 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            print(f"\n💾 完整响应已保存到: beijing_api_response.json")
            
        else:
            print("❌ API响应异常")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")

def debug_shanghai_api():
    """调试上海API响应"""
    print("\n🔍 调试上海9月API响应...")
    
    try:
        from modules.request_module import send_request_with_managed_session
        from modules.config import API_URL_SH_SEP
        
        response = send_request_with_managed_session(API_URL_SH_SEP)
        
        if response and 'data' in response:
            data = response['data']
            
            print(f"📊 数据行数: {len(data.get('rows', []))}")
            print(f"📋 字段数: {len(data.get('cols', []))}")
            
            # 显示字段信息
            if 'cols' in data:
                print("\n📝 字段列表:")
                for i, col in enumerate(data['cols']):
                    print(f"  {i:2d}. {col.get('display_name', 'N/A'):30} | {col.get('name', 'N/A'):20} | {col.get('base_type', 'N/A')}")
            
            # 显示前几行数据
            if 'rows' in data and len(data['rows']) > 0:
                print(f"\n📋 前3行数据:")
                for i, row in enumerate(data['rows'][:3]):
                    print(f"  行{i+1}: {row[:5]}...")  # 只显示前5个字段
            
            # 保存完整响应到文件
            with open('shanghai_api_response.json', 'w', encoding='utf-8') as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            print(f"\n💾 完整响应已保存到: shanghai_api_response.json")
            
        else:
            print("❌ API响应异常")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")

if __name__ == "__main__":
    debug_beijing_api()
    debug_shanghai_api()
