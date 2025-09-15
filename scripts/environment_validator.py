#!/usr/bin/env python3
"""
环境状态验证工具

用于验证集成测试环境是否准备就绪，包括：
- 数据库状态检查
- API连接验证
- 配置文件检查
- 必要文件和目录检查

使用方法:
    python scripts/environment_validator.py
    python scripts/environment_validator.py --activity BJ-SEP
"""

import sys
import os
import sqlite3
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any

# 添加modules路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler()]
    )

class EnvironmentValidator:
    """环境验证器"""
    
    def __init__(self, activity_code: str = None):
        self.activity_code = activity_code
        self.validation_results = {
            'database': {'status': 'unknown', 'details': {}},
            'api': {'status': 'unknown', 'details': {}},
            'config': {'status': 'unknown', 'details': {}},
            'files': {'status': 'unknown', 'details': {}},
            'overall': {'status': 'unknown', 'ready': False}
        }

    def validate_database(self) -> bool:
        """验证数据库状态"""
        print("🔍 验证数据库状态...")
        
        try:
            db_path = 'performance_data.db'
            
            # 检查数据库文件是否存在
            if not os.path.exists(db_path):
                self.validation_results['database'] = {
                    'status': 'error',
                    'details': {'error': '数据库文件不存在'}
                }
                print("❌ 数据库文件不存在")
                return False
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查必要的表
            required_tables = ['performance_records', 'notification_queue']
            table_status = {}
            
            for table_name in required_tables:
                # 检查表是否存在
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                if cursor.fetchone():
                    # 获取记录数
                    if self.activity_code:
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM {table_name} 
                            WHERE activity_code = ?
                        """, (self.activity_code,))
                    else:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    
                    count = cursor.fetchone()[0]
                    table_status[table_name] = {'exists': True, 'count': count}
                    
                    if count > 0:
                        if self.activity_code:
                            print(f"⚠️ 表 {table_name} 中有 {count} 条活动 {self.activity_code} 的记录")
                        else:
                            print(f"⚠️ 表 {table_name} 中有 {count} 条记录")
                    else:
                        print(f"✅ 表 {table_name} 为空（符合测试要求）")
                else:
                    table_status[table_name] = {'exists': False, 'count': 0}
                    print(f"❌ 表 {table_name} 不存在")
            
            conn.close()
            
            # 判断数据库状态
            all_tables_exist = all(status['exists'] for status in table_status.values())
            all_tables_clean = all(status['count'] == 0 for status in table_status.values())
            
            if all_tables_exist and all_tables_clean:
                status = 'ready'
                print("✅ 数据库状态：准备就绪")
            elif all_tables_exist:
                status = 'needs_cleanup'
                print("⚠️ 数据库状态：需要清理")
            else:
                status = 'error'
                print("❌ 数据库状态：缺少必要的表")
            
            self.validation_results['database'] = {
                'status': status,
                'details': {
                    'file_exists': True,
                    'tables': table_status,
                    'needs_cleanup': not all_tables_clean
                }
            }
            
            return status in ['ready', 'needs_cleanup']
            
        except Exception as e:
            self.validation_results['database'] = {
                'status': 'error',
                'details': {'error': str(e)}
            }
            print(f"❌ 数据库验证失败: {e}")
            return False

    def validate_api_connection(self) -> bool:
        """验证API连接"""
        print("\n🔍 验证API连接...")
        
        try:
            from modules.request_module import get_valid_session
            
            # 测试获取session
            session_id = get_valid_session()
            
            if session_id:
                print(f"✅ Metabase连接成功，Session ID: {session_id[:10]}...")
                
                # 如果指定了活动，测试对应的API
                if self.activity_code:
                    api_url = self._get_api_url_for_activity(self.activity_code)
                    if api_url:
                        success = self._test_specific_api(api_url)
                        if success:
                            print(f"✅ 活动 {self.activity_code} 的API连接正常")
                        else:
                            print(f"❌ 活动 {self.activity_code} 的API连接失败")
                            self.validation_results['api'] = {
                                'status': 'error',
                                'details': {'error': f'活动 {self.activity_code} API连接失败'}
                            }
                            return False
                
                self.validation_results['api'] = {
                    'status': 'ready',
                    'details': {'session_id': session_id[:10] + '...'}
                }
                return True
            else:
                print("❌ Metabase连接失败")
                self.validation_results['api'] = {
                    'status': 'error',
                    'details': {'error': 'Metabase连接失败'}
                }
                return False
                
        except Exception as e:
            print(f"❌ API连接验证失败: {e}")
            self.validation_results['api'] = {
                'status': 'error',
                'details': {'error': str(e)}
            }
            return False

    def _get_api_url_for_activity(self, activity_code: str) -> str:
        """获取活动对应的API URL"""
        try:
            from modules.config import API_URL_BJ_SEP, API_URL_SH_SEP
            
            if activity_code == 'BJ-SEP':
                return API_URL_BJ_SEP
            elif activity_code == 'SH-SEP':
                return API_URL_SH_SEP
            else:
                return None
        except:
            return None

    def _test_specific_api(self, api_url: str) -> bool:
        """测试特定的API"""
        try:
            from modules.request_module import send_request_with_managed_session
            
            response = send_request_with_managed_session(api_url)
            
            if response and 'data' in response:
                data_count = len(response['data'].get('rows', []))
                print(f"  API响应正常，获取到 {data_count} 条数据")
                return True
            else:
                print("  API响应异常")
                return False
                
        except Exception as e:
            print(f"  API测试失败: {e}")
            return False

    def validate_configuration(self) -> bool:
        """验证配置文件"""
        print("\n🔍 验证配置文件...")
        
        try:
            # 检查config.py文件
            config_file = 'modules/config.py'
            if not os.path.exists(config_file):
                print("❌ 配置文件不存在")
                self.validation_results['config'] = {
                    'status': 'error',
                    'details': {'error': '配置文件不存在'}
                }
                return False
            
            # 导入配置并检查关键配置项
            from modules import config
            
            required_configs = []
            if self.activity_code == 'BJ-SEP':
                required_configs = ['API_URL_BJ_SEP']
            elif self.activity_code == 'SH-SEP':
                required_configs = ['API_URL_SH_SEP']
            else:
                required_configs = ['API_URL_BJ_SEP', 'API_URL_SH_SEP']
            
            missing_configs = []
            for config_name in required_configs:
                if not hasattr(config, config_name):
                    missing_configs.append(config_name)
            
            if missing_configs:
                print(f"❌ 缺少配置项: {', '.join(missing_configs)}")
                self.validation_results['config'] = {
                    'status': 'error',
                    'details': {'missing_configs': missing_configs}
                }
                return False
            
            print("✅ 配置文件验证通过")
            self.validation_results['config'] = {
                'status': 'ready',
                'details': {'configs_checked': required_configs}
            }
            return True
            
        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
            self.validation_results['config'] = {
                'status': 'error',
                'details': {'error': str(e)}
            }
            return False

    def validate_files_and_directories(self) -> bool:
        """验证必要的文件和目录"""
        print("\n🔍 验证文件和目录...")
        
        required_items = [
            {'path': 'modules', 'type': 'directory', 'name': 'modules目录'},
            {'path': 'scripts', 'type': 'directory', 'name': 'scripts目录'},
            {'path': 'integration_test_september_jobs.py', 'type': 'file', 'name': '集成测试脚本'},
            {'path': 'scripts/detailed_field_validator.py', 'type': 'file', 'name': '字段验证工具'},
            {'path': 'scripts/database_cleanup.py', 'type': 'file', 'name': '数据库清理工具'}
        ]
        
        missing_items = []
        
        for item in required_items:
            path = item['path']
            item_type = item['type']
            name = item['name']
            
            if item_type == 'directory':
                if os.path.isdir(path):
                    print(f"✅ {name}: 存在")
                else:
                    print(f"❌ {name}: 不存在")
                    missing_items.append(name)
            else:  # file
                if os.path.isfile(path):
                    print(f"✅ {name}: 存在")
                else:
                    print(f"❌ {name}: 不存在")
                    missing_items.append(name)
        
        if missing_items:
            self.validation_results['files'] = {
                'status': 'error',
                'details': {'missing_items': missing_items}
            }
            return False
        else:
            self.validation_results['files'] = {
                'status': 'ready',
                'details': {'all_items_present': True}
            }
            return True

    def generate_validation_report(self) -> str:
        """生成验证报告"""
        report = []
        report.append("# 集成测试环境验证报告")
        report.append(f"**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.activity_code:
            report.append(f"**验证范围**: 活动 {self.activity_code}")
        else:
            report.append(f"**验证范围**: 通用环境")
        
        report.append("")
        
        # 各项验证结果
        for category, result in self.validation_results.items():
            if category == 'overall':
                continue
                
            status = result['status']
            if status == 'ready':
                status_icon = "✅"
            elif status == 'needs_cleanup':
                status_icon = "⚠️"
            else:
                status_icon = "❌"
            
            report.append(f"## {status_icon} {category.title()}")
            report.append(f"**状态**: {status}")
            
            if 'error' in result['details']:
                report.append(f"**错误**: {result['details']['error']}")
            
            report.append("")
        
        # 总体状态
        overall_status = self.validation_results['overall']
        if overall_status['ready']:
            report.append("## ✅ 总体状态: 准备就绪")
            report.append("环境验证通过，可以开始集成测试。")
        else:
            report.append("## ❌ 总体状态: 未准备就绪")
            report.append("请解决上述问题后重新验证。")
        
        return "\n".join(report)

    def validate_environment(self) -> bool:
        """执行完整的环境验证"""
        print("🚀 开始集成测试环境验证")
        print("=" * 60)
        
        # 执行各项验证
        db_ok = self.validate_database()
        api_ok = self.validate_api_connection()
        config_ok = self.validate_configuration()
        files_ok = self.validate_files_and_directories()
        
        # 判断总体状态
        all_ready = db_ok and api_ok and config_ok and files_ok
        needs_cleanup = (self.validation_results['database']['status'] == 'needs_cleanup' and 
                        api_ok and config_ok and files_ok)
        
        if all_ready:
            overall_status = 'ready'
            ready = True
        elif needs_cleanup:
            overall_status = 'needs_cleanup'
            ready = False
        else:
            overall_status = 'error'
            ready = False
        
        self.validation_results['overall'] = {
            'status': overall_status,
            'ready': ready
        }
        
        # 输出总结
        print("\n" + "=" * 60)
        print("📊 环境验证总结")
        print("=" * 60)
        
        if ready:
            print("✅ 环境验证通过！可以开始集成测试")
        elif needs_cleanup:
            print("⚠️ 环境基本就绪，但需要清理数据库")
            print("建议运行: python scripts/database_cleanup.py --activity", self.activity_code or "--all")
        else:
            print("❌ 环境验证失败，请解决上述问题")
        
        return ready

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='集成测试环境验证工具')
    parser.add_argument('--activity', help='指定活动代码 (如: BJ-SEP, SH-SEP)')
    parser.add_argument('--report', help='保存验证报告到文件')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # 创建验证器
    validator = EnvironmentValidator(args.activity)
    
    # 执行验证
    success = validator.validate_environment()
    
    # 生成报告
    if args.report:
        report = validator.generate_validation_report()
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📄 验证报告已保存到: {args.report}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
