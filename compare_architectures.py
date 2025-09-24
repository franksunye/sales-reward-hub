#!/usr/bin/env python3
"""
新旧架构消息内容1对1对比测试
确保功能完全相等（消息格式与内容）
"""

import sys
import os
import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple
import difflib

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from modules.core.notification_service import create_notification_service
from modules.core.storage import create_data_store
from modules.core.data_models import ProcessingConfig, City

class ArchitectureComparator:
    """新旧架构对比器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.old_tasks = []
        self.new_tasks = []
        self.comparison_results = {
            'total_old': 0,
            'total_new': 0,
            'matched_pairs': 0,
            'differences': [],
            'summary': {}
        }
    
    def reset_notification_status(self):
        """重置通知状态，准备对比测试"""
        print("🔄 重置通知状态...")
        
        try:
            # 重置SQLite数据库中的通知状态
            with sqlite3.connect('performance_data.db') as conn:
                cursor = conn.execute("""
                    UPDATE performance_data 
                    SET notification_sent = 0 
                    WHERE activity_code = 'BJ-SEP'
                """)
                updated_count = cursor.rowcount
                conn.commit()
                print(f"   重置了 {updated_count} 条记录的通知状态")
            
            return True
        except Exception as e:
            print(f"❌ 重置通知状态失败: {e}")
            return False
    
    def backup_current_tasks(self):
        """备份当前的Task记录"""
        print("💾 备份当前Task记录...")
        
        try:
            with sqlite3.connect('tasks.db') as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM tasks 
                    WHERE created_at >= datetime('now', '-2 hours')
                """)
                current_count = cursor.fetchone()[0]
                print(f"   当前2小时内的Task记录: {current_count} 条")
                
                # 标记当前记录为新架构生成的
                conn.execute("""
                    UPDATE tasks 
                    SET status = 'new_architecture_backup'
                    WHERE created_at >= datetime('now', '-2 hours') 
                    AND status != 'old_architecture'
                """)
                conn.commit()
                print("   已标记当前记录为新架构备份")
            
            return True
        except Exception as e:
            print(f"❌ 备份Task记录失败: {e}")
            return False
    
    def run_old_architecture(self):
        """运行旧架构生成基准数据"""
        print("🏗️ 运行旧架构...")
        
        try:
            # 运行旧架构的北京9月任务
            import subprocess
            result = subprocess.run([
                'python', 'jobs.py', 'signing_and_sales_incentive_sep_beijing'
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("   ✅ 旧架构运行成功")
                
                # 标记旧架构生成的Task记录
                with sqlite3.connect('tasks.db') as conn:
                    conn.execute("""
                        UPDATE tasks 
                        SET status = 'old_architecture'
                        WHERE created_at >= datetime('now', '-10 minutes')
                        AND status IS NULL
                    """)
                    conn.commit()
                
                return True
            else:
                print(f"   ❌ 旧架构运行失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 运行旧架构失败: {e}")
            return False
    
    def run_new_architecture(self):
        """运行新架构生成对比数据"""
        print("🚀 运行新架构...")
        
        try:
            # 创建存储实例
            storage = create_data_store(
                storage_type="sqlite",
                db_path="performance_data.db"
            )
            
            # 创建配置
            config = ProcessingConfig(
                config_key="BJ-2025-09",
                activity_code="BJ-SEP",
                city=City.BEIJING,
                housekeeper_key_format="管家",
                storage_type="sqlite"
            )
            
            # 创建通知服务并发送通知
            notification_service = create_notification_service(storage, config)
            stats = notification_service.send_notifications()
            
            print(f"   ✅ 新架构运行成功 - 总计: {stats['total']}")
            
            # 标记新架构生成的Task记录
            with sqlite3.connect('tasks.db') as conn:
                conn.execute("""
                    UPDATE tasks 
                    SET status = 'new_architecture'
                    WHERE created_at >= datetime('now', '-10 minutes')
                    AND status IS NULL
                """)
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ 运行新架构失败: {e}")
            return False
    
    def extract_tasks(self):
        """提取新旧架构生成的Task记录"""
        print("📊 提取Task记录...")

        try:
            with sqlite3.connect('tasks.db') as conn:
                conn.row_factory = sqlite3.Row

                # 先检查所有状态
                cursor = conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
                status_counts = cursor.fetchall()
                print("   当前Task状态统计:")
                for status, count in status_counts:
                    print(f"     {status}: {count} 条")

                # 提取旧架构Task记录（20-30分钟前的记录）
                cursor = conn.execute("""
                    SELECT * FROM tasks
                    WHERE created_at >= datetime('now', '-30 minutes')
                    AND created_at < datetime('now', '-15 minutes')
                    ORDER BY created_at
                """)
                self.old_tasks = [dict(row) for row in cursor.fetchall()]

                # 提取新架构Task记录（最近10分钟内的记录）
                cursor = conn.execute("""
                    SELECT * FROM tasks
                    WHERE created_at >= datetime('now', '-10 minutes')
                    ORDER BY created_at
                """)
                all_new_tasks = [dict(row) for row in cursor.fetchall()]

                # 从新架构记录中排除备份记录，只保留新生成的记录
                self.new_tasks = [task for task in all_new_tasks
                                if task.get('status') != 'new_architecture_backup']

            print(f"   旧架构Task记录: {len(self.old_tasks)} 条")
            print(f"   新架构Task记录: {len(self.new_tasks)} 条")

            self.comparison_results['total_old'] = len(self.old_tasks)
            self.comparison_results['total_new'] = len(self.new_tasks)

            return True

        except Exception as e:
            print(f"❌ 提取Task记录失败: {e}")
            return False
    
    def extract_contract_info_from_message(self, message: str) -> Dict:
        """从消息中提取合同信息用于匹配"""
        info = {'housekeeper': '', 'contract_num': '', 'message_type': ''}
        
        try:
            if '🧨🧨🧨 签约喜报 🧨🧨🧨' in message:
                # 群通知消息
                info['message_type'] = 'group'
                lines = message.split('\n')
                for line in lines:
                    if '恭喜' in line and '签约合同' in line:
                        # 提取管家姓名和合同编号
                        parts = line.split('签约合同')
                        if len(parts) >= 2:
                            housekeeper_part = parts[0].replace('恭喜', '').strip()
                            contract_part = parts[1].split('并完成')[0].strip()
                            info['housekeeper'] = housekeeper_part
                            info['contract_num'] = contract_part
                        break
            else:
                # 奖励通知消息
                info['message_type'] = 'reward'
                # 从消息中提取管家姓名和合同编号
                if '签约合同' in message:
                    parts = message.split('签约合同')
                    if len(parts) >= 2:
                        housekeeper_part = parts[0].strip()
                        contract_part = parts[1].split('）')[0] + '）'
                        info['housekeeper'] = housekeeper_part
                        info['contract_num'] = contract_part
        
        except Exception as e:
            self.logger.error(f"提取合同信息失败: {e}")
        
        return info
    
    def match_tasks(self) -> List[Tuple[Dict, Dict]]:
        """匹配新旧架构的Task记录"""
        print("🔗 匹配Task记录...")
        
        matched_pairs = []
        old_task_map = {}
        
        # 为旧架构Task建立索引
        for task in self.old_tasks:
            info = self.extract_contract_info_from_message(task['message'])
            key = f"{info['housekeeper']}_{info['contract_num']}_{info['message_type']}"
            old_task_map[key] = task
        
        # 匹配新架构Task
        for new_task in self.new_tasks:
            info = self.extract_contract_info_from_message(new_task['message'])
            key = f"{info['housekeeper']}_{info['contract_num']}_{info['message_type']}"
            
            if key in old_task_map:
                matched_pairs.append((old_task_map[key], new_task))
                del old_task_map[key]  # 避免重复匹配
        
        print(f"   成功匹配: {len(matched_pairs)} 对")
        print(f"   未匹配的旧架构记录: {len(old_task_map)} 条")
        print(f"   未匹配的新架构记录: {len(self.new_tasks) - len(matched_pairs)} 条")
        
        self.comparison_results['matched_pairs'] = len(matched_pairs)
        return matched_pairs
    
    def compare_messages(self, matched_pairs: List[Tuple[Dict, Dict]]):
        """详细对比消息内容"""
        print("🔍 详细对比消息内容...")
        
        identical_count = 0
        different_count = 0
        
        for i, (old_task, new_task) in enumerate(matched_pairs):
            old_msg = old_task['message'].strip()
            new_msg = new_task['message'].strip()
            
            if old_msg == new_msg:
                identical_count += 1
            else:
                different_count += 1
                
                # 记录差异
                diff = {
                    'pair_index': i + 1,
                    'task_type': old_task['task_type'],
                    'recipient': old_task['recipient'],
                    'old_message': old_msg,
                    'new_message': new_msg,
                    'diff_details': list(difflib.unified_diff(
                        old_msg.splitlines(keepends=True),
                        new_msg.splitlines(keepends=True),
                        fromfile='旧架构',
                        tofile='新架构',
                        lineterm=''
                    ))
                }
                
                self.comparison_results['differences'].append(diff)
        
        print(f"   完全相同: {identical_count} 条")
        print(f"   存在差异: {different_count} 条")
        
        self.comparison_results['summary'] = {
            'identical': identical_count,
            'different': different_count,
            'accuracy_rate': f"{identical_count / len(matched_pairs) * 100:.2f}%" if matched_pairs else "0%"
        }
    
    def generate_report(self):
        """生成详细的对比报告"""
        print("📋 生成对比报告...")
        
        report_file = f"architecture_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("新旧架构消息内容1对1对比报告\n")
            f.write("=" * 80 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 总体统计
            f.write("📊 总体统计:\n")
            f.write(f"  旧架构Task记录: {self.comparison_results['total_old']} 条\n")
            f.write(f"  新架构Task记录: {self.comparison_results['total_new']} 条\n")
            f.write(f"  成功匹配对数: {self.comparison_results['matched_pairs']} 对\n")
            f.write(f"  完全相同消息: {self.comparison_results['summary']['identical']} 条\n")
            f.write(f"  存在差异消息: {self.comparison_results['summary']['different']} 条\n")
            f.write(f"  准确率: {self.comparison_results['summary']['accuracy_rate']}\n\n")
            
            # 差异详情
            if self.comparison_results['differences']:
                f.write("❌ 差异详情:\n")
                f.write("-" * 80 + "\n")
                
                for i, diff in enumerate(self.comparison_results['differences']):
                    f.write(f"\n差异 #{i+1}:\n")
                    f.write(f"  任务类型: {diff['task_type']}\n")
                    f.write(f"  接收者: {diff['recipient']}\n")
                    f.write(f"  \n旧架构消息:\n{diff['old_message']}\n")
                    f.write(f"  \n新架构消息:\n{diff['new_message']}\n")
                    f.write(f"  \n详细差异:\n")
                    for line in diff['diff_details']:
                        f.write(f"    {line}")
                    f.write("\n" + "-" * 80 + "\n")
            else:
                f.write("✅ 所有消息内容完全相同！\n")
        
        print(f"   报告已保存到: {report_file}")
        return report_file

def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🎯 新旧架构消息内容1对1对比测试")
    print("=" * 60)
    
    comparator = ArchitectureComparator()
    
    try:
        # 步骤1: 重置通知状态
        if not comparator.reset_notification_status():
            return False
        
        # 步骤2: 备份当前Task记录
        if not comparator.backup_current_tasks():
            return False
        
        # 步骤3: 运行旧架构
        if not comparator.run_old_architecture():
            return False
        
        # 步骤4: 运行新架构
        if not comparator.run_new_architecture():
            return False
        
        # 步骤5: 提取Task记录
        if not comparator.extract_tasks():
            return False
        
        # 步骤6: 匹配Task记录
        matched_pairs = comparator.match_tasks()
        
        # 步骤7: 对比消息内容
        comparator.compare_messages(matched_pairs)
        
        # 步骤8: 生成报告
        report_file = comparator.generate_report()
        
        # 显示结果摘要
        print("\n🎉 对比测试完成!")
        print(f"📋 详细报告: {report_file}")
        print(f"✅ 准确率: {comparator.comparison_results['summary']['accuracy_rate']}")
        
        if comparator.comparison_results['summary']['different'] == 0:
            print("🎊 恭喜！新旧架构消息内容完全相同！")
        else:
            print(f"⚠️  发现 {comparator.comparison_results['summary']['different']} 处差异，请查看详细报告")
        
        return True
        
    except Exception as e:
        print(f"❌ 对比测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
