"""
销售激励系统重构 - 影子模式部署脚本
版本: v1.0
创建日期: 2025-01-08

自动化部署影子模式，集成到现有jobs.py中。
"""

import os
import sys
import shutil
import logging
from datetime import datetime
from typing import List, Dict

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shadow_mode_deployment.log'),
        logging.StreamHandler()
    ]
)


class ShadowModeDeployer:
    """影子模式部署器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.backup_dir = os.path.join(self.project_root, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.jobs_file = os.path.join(self.project_root, "jobs.py")
        
        logging.info(f"项目根目录: {self.project_root}")
        logging.info(f"备份目录: {self.backup_dir}")
        logging.info(f"Jobs文件: {self.jobs_file}")
    
    def validate_environment(self) -> bool:
        """验证部署环境"""
        logging.info("开始环境验证...")
        
        checks = []
        
        # 检查项目根目录
        if not os.path.exists(self.project_root):
            checks.append(f"❌ 项目根目录不存在: {self.project_root}")
        else:
            checks.append(f"✅ 项目根目录存在: {self.project_root}")
        
        # 检查jobs.py文件
        if not os.path.exists(self.jobs_file):
            checks.append(f"❌ jobs.py文件不存在: {self.jobs_file}")
        else:
            checks.append(f"✅ jobs.py文件存在: {self.jobs_file}")
        
        # 检查modules/core目录
        core_dir = os.path.join(self.project_root, "modules", "core")
        if not os.path.exists(core_dir):
            checks.append(f"❌ modules/core目录不存在: {core_dir}")
        else:
            checks.append(f"✅ modules/core目录存在: {core_dir}")
        
        # 检查关键模块文件
        key_files = [
            "modules/core/__init__.py",
            "modules/core/beijing_jobs.py",
            "modules/core/shanghai_jobs.py",
            "modules/core/shadow_mode_integration.py"
        ]
        
        for file_path in key_files:
            full_path = os.path.join(self.project_root, file_path)
            if not os.path.exists(full_path):
                checks.append(f"❌ 关键文件不存在: {file_path}")
            else:
                checks.append(f"✅ 关键文件存在: {file_path}")
        
        # 输出检查结果
        for check in checks:
            logging.info(check)
        
        # 判断是否通过验证
        errors = [check for check in checks if check.startswith('❌')]
        if errors:
            logging.error(f"环境验证失败: {len(errors)} 个错误")
            return False
        
        logging.info("✅ 环境验证通过")
        return True
    
    def backup_existing_code(self) -> bool:
        """备份现有代码"""
        logging.info("开始备份现有代码...")
        
        try:
            # 创建备份目录
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # 备份jobs.py
            if os.path.exists(self.jobs_file):
                backup_jobs = os.path.join(self.backup_dir, "jobs.py")
                shutil.copy2(self.jobs_file, backup_jobs)
                logging.info(f"✅ 备份jobs.py: {backup_jobs}")
            
            # 备份modules目录（如果存在）
            modules_dir = os.path.join(self.project_root, "modules")
            if os.path.exists(modules_dir):
                backup_modules = os.path.join(self.backup_dir, "modules")
                shutil.copytree(modules_dir, backup_modules, dirs_exist_ok=True)
                logging.info(f"✅ 备份modules目录: {backup_modules}")
            
            logging.info(f"✅ 代码备份完成: {self.backup_dir}")
            return True
            
        except Exception as e:
            logging.error(f"❌ 代码备份失败: {e}")
            return False
    
    def generate_shadow_mode_jobs(self) -> str:
        """生成影子模式jobs.py代码"""
        shadow_code = '''
# ============================================================================
# 销售激励系统重构 - 影子模式集成
# 自动生成时间: {timestamp}
# 说明: 新旧系统并行运行，对比验证，确保安全迁移
# ============================================================================

import logging
from modules.core.shadow_mode_integration import (
    shadow_signing_and_sales_incentive_jun_beijing,
    shadow_signing_and_sales_incentive_sep_beijing,
    shadow_signing_and_sales_incentive_apr_shanghai,
    shadow_signing_and_sales_incentive_sep_shanghai,
    generate_shadow_mode_report
)

# 保存原始函数引用
try:
    original_signing_and_sales_incentive_jun_beijing = signing_and_sales_incentive_jun_beijing
    original_signing_and_sales_incentive_sep_beijing = signing_and_sales_incentive_sep_beijing
    original_signing_and_sales_incentive_apr_shanghai = signing_and_sales_incentive_apr_shanghai
    original_signing_and_sales_incentive_sep_shanghai = signing_and_sales_incentive_sep_shanghai
except NameError as e:
    logging.warning(f"原始函数未找到: {{e}}")

# 影子模式函数定义
def signing_and_sales_incentive_jun_beijing():
    """北京6月销售激励 - 影子模式"""
    return shadow_signing_and_sales_incentive_jun_beijing(
        original_signing_and_sales_incentive_jun_beijing
    )()

def signing_and_sales_incentive_sep_beijing():
    """北京9月销售激励 - 影子模式"""
    return shadow_signing_and_sales_incentive_sep_beijing(
        original_signing_and_sales_incentive_sep_beijing
    )()

def signing_and_sales_incentive_apr_shanghai():
    """上海4月销售激励 - 影子模式"""
    return shadow_signing_and_sales_incentive_apr_shanghai(
        original_signing_and_sales_incentive_apr_shanghai
    )()

def signing_and_sales_incentive_sep_shanghai():
    """上海9月销售激励 - 影子模式"""
    return shadow_signing_and_sales_incentive_sep_shanghai(
        original_signing_and_sales_incentive_sep_shanghai
    )()

# 影子模式报告函数
def get_shadow_mode_report():
    """获取影子模式运行报告"""
    return generate_shadow_mode_report()

# 影子模式状态检查
def check_shadow_mode_status():
    """检查影子模式状态"""
    try:
        from modules.core.production_config import production_metrics
        metrics = production_metrics.get_summary()
        logging.info(f"影子模式状态: {{metrics}}")
        return metrics
    except Exception as e:
        logging.error(f"影子模式状态检查失败: {{e}}")
        return {{'status': 'error', 'message': str(e)}}

# ============================================================================
# 影子模式集成完成
# 使用方法:
# 1. 正常调用Job函数，会自动运行新旧系统对比
# 2. 调用get_shadow_mode_report()查看对比报告
# 3. 调用check_shadow_mode_status()检查运行状态
# ============================================================================
'''.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return shadow_code
    
    def deploy_shadow_mode(self) -> bool:
        """部署影子模式"""
        logging.info("开始部署影子模式...")
        
        try:
            # 读取现有jobs.py内容
            original_content = ""
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            
            # 生成影子模式代码
            shadow_code = self.generate_shadow_mode_jobs()
            
            # 合并代码（在原有代码后追加影子模式代码）
            combined_content = original_content + "\\n\\n" + shadow_code
            
            # 写入新的jobs.py
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            logging.info(f"✅ 影子模式部署完成: {self.jobs_file}")
            return True
            
        except Exception as e:
            logging.error(f"❌ 影子模式部署失败: {e}")
            return False
    
    def verify_deployment(self) -> bool:
        """验证部署结果"""
        logging.info("开始验证部署结果...")
        
        try:
            # 尝试导入影子模式模块
            sys.path.insert(0, self.project_root)
            
            from modules.core.shadow_mode_integration import shadow_validator
            from modules.core.production_config import initialize_production_environment
            
            # 初始化生产环境
            initialize_production_environment()
            
            logging.info("✅ 影子模式模块导入成功")
            logging.info("✅ 生产环境初始化成功")
            logging.info("✅ 部署验证通过")
            return True
            
        except Exception as e:
            logging.error(f"❌ 部署验证失败: {e}")
            return False
    
    def rollback(self) -> bool:
        """回滚部署"""
        logging.info("开始回滚部署...")
        
        try:
            # 恢复jobs.py
            backup_jobs = os.path.join(self.backup_dir, "jobs.py")
            if os.path.exists(backup_jobs):
                shutil.copy2(backup_jobs, self.jobs_file)
                logging.info(f"✅ 恢复jobs.py: {self.jobs_file}")
            
            logging.info("✅ 回滚完成")
            return True
            
        except Exception as e:
            logging.error(f"❌ 回滚失败: {e}")
            return False
    
    def deploy(self) -> bool:
        """执行完整部署流程"""
        logging.info("="*60)
        logging.info("开始影子模式部署")
        logging.info("="*60)
        
        # 1. 环境验证
        if not self.validate_environment():
            logging.error("❌ 环境验证失败，部署终止")
            return False
        
        # 2. 代码备份
        if not self.backup_existing_code():
            logging.error("❌ 代码备份失败，部署终止")
            return False
        
        # 3. 部署影子模式
        if not self.deploy_shadow_mode():
            logging.error("❌ 影子模式部署失败，开始回滚")
            self.rollback()
            return False
        
        # 4. 验证部署
        if not self.verify_deployment():
            logging.error("❌ 部署验证失败，开始回滚")
            self.rollback()
            return False
        
        logging.info("="*60)
        logging.info("✅ 影子模式部署成功！")
        logging.info(f"备份位置: {self.backup_dir}")
        logging.info("下一步: 运行Job函数进行影子模式验证")
        logging.info("="*60)
        
        return True


def main():
    """主函数"""
    print("销售激励系统重构 - 影子模式部署")
    print("="*50)
    
    # 创建部署器
    deployer = ShadowModeDeployer()
    
    # 执行部署
    success = deployer.deploy()
    
    if success:
        print("\\n🎉 影子模式部署成功！")
        print("\\n下一步操作:")
        print("1. 运行现有的Job函数（会自动启用影子模式）")
        print("2. 查看日志文件: shadow_mode_deployment.log")
        print("3. 调用get_shadow_mode_report()查看对比报告")
        print("4. 监控运行1周，评估迁移效果")
    else:
        print("\\n❌ 影子模式部署失败！")
        print("请查看日志文件了解详细错误信息")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
