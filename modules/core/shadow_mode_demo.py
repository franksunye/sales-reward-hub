"""
销售激励系统重构 - 影子模式演示
版本: v1.0
创建日期: 2025-01-08

演示影子模式的工作原理和效果。
"""

import logging
import time
import os
import sys
from typing import List, Dict

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.core.shadow_mode_integration import (
    shadow_mode_wrapper,
    shadow_validator,
    generate_shadow_mode_report
)
from modules.core.beijing_jobs import signing_and_sales_incentive_jun_beijing_v2
from modules.core.production_config import initialize_production_environment

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def simulate_old_beijing_june_function() -> List[Dict]:
    """模拟旧的北京6月函数"""
    logging.info("模拟旧系统：北京6月销售激励处理")
    
    # 模拟处理时间
    time.sleep(0.1)
    
    # 模拟旧系统输出格式
    return [
        {
            '活动编号': 'BJ-JUN',
            '合同ID(_id)': '2025010812345678',
            '管家(serviceHousekeeper)': '张三',
            '合同金额(adjustRefundMoney)': 15000,
            '管家累计单数': 1,
            '管家累计金额': 15000,
            '计入业绩金额': 15000,
            '奖励类型': '幸运数字',
            '奖励名称': '接好运万元以上',
            '活动期内第几个合同': 1
        }
    ]


def simulate_old_beijing_september_function() -> List[Dict]:
    """模拟旧的北京9月函数"""
    logging.info("模拟旧系统：北京9月销售激励处理")
    
    # 模拟处理时间
    time.sleep(0.15)
    
    # 模拟旧系统输出格式
    return [
        {
            '活动编号': 'BJ-SEP',
            '合同ID(_id)': '2025010912345679',
            '管家(serviceHousekeeper)': '李四',
            '合同金额(adjustRefundMoney)': 25000,
            '管家累计单数': 1,
            '管家累计金额': 25000,
            '计入业绩金额': 25000,
            '奖励类型': '',
            '奖励名称': '',
            '活动期内第几个合同': 1
        }
    ]


def demo_shadow_mode():
    """演示影子模式"""
    print("\n" + "="*60)
    print("销售激励系统重构 - 影子模式演示")
    print("="*60)
    
    try:
        # 初始化生产环境
        print("1. 初始化生产环境...")
        initialize_production_environment()
        print("✅ 生产环境初始化完成")
        
        # 创建影子模式包装函数
        print("\n2. 创建影子模式包装函数...")
        
        # 北京6月影子模式
        shadow_beijing_june = shadow_mode_wrapper(
            signing_and_sales_incentive_jun_beijing_v2,
            simulate_old_beijing_june_function,
            "北京6月销售激励演示"
        )
        
        print("✅ 影子模式包装函数创建完成")
        
        # 运行影子模式演示
        print("\n3. 运行影子模式演示...")
        print("-" * 40)
        
        # 第一次运行
        print("第1次运行:")
        result1 = shadow_beijing_june()
        print(f"返回结果: {len(result1)} 条记录")
        
        # 第二次运行（模拟不同场景）
        print("\n第2次运行:")
        result2 = shadow_beijing_june()
        print(f"返回结果: {len(result2)} 条记录")
        
        print("-" * 40)
        
        # 生成报告
        print("\n4. 生成影子模式报告...")
        report = generate_shadow_mode_report()
        print(report)
        
        # 显示验证统计
        print("\n5. 验证统计详情...")
        summary = shadow_validator.get_summary_report()
        print(f"总对比次数: {summary.get('total_comparisons', 0)}")
        print(f"等价对比次数: {summary.get('equivalent_comparisons', 0)}")
        print(f"等价率: {summary.get('equivalence_rate', 0):.1%}")
        print(f"系统状态: {summary.get('status', 'unknown')}")
        
        print("\n" + "="*60)
        print("✅ 影子模式演示完成！")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 影子模式演示失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False


def demo_production_integration():
    """演示生产环境集成"""
    print("\n" + "="*60)
    print("生产环境集成演示")
    print("="*60)
    
    print("影子模式在生产环境中的工作流程:")
    print("1. 用户调用原有的Job函数")
    print("2. 影子模式自动运行新旧两套系统")
    print("3. 对比结果并记录差异")
    print("4. 返回旧系统结果（保证业务连续性）")
    print("5. 生成详细的对比报告")
    
    print("\n集成代码示例:")
    print("-" * 40)
    
    integration_code = '''
# 在现有的jobs.py中添加以下代码:

from modules.core.shadow_mode_integration import shadow_signing_and_sales_incentive_jun_beijing

# 保存原始函数
original_function = signing_and_sales_incentive_jun_beijing

# 替换为影子模式版本
def signing_and_sales_incentive_jun_beijing():
    """北京6月销售激励 - 影子模式"""
    return shadow_signing_and_sales_incentive_jun_beijing(original_function)()

# 查看影子模式报告
def get_shadow_mode_report():
    from modules.core.shadow_mode_integration import generate_shadow_mode_report
    return generate_shadow_mode_report()
'''
    
    print(integration_code)
    print("-" * 40)
    
    print("\n监控要点:")
    print("- 处理时间对比")
    print("- 数据输出等价性")
    print("- 错误率统计")
    print("- 性能改善情况")
    
    print("\n建议运行周期:")
    print("- 第1-3天: 密切监控，每天查看报告")
    print("- 第4-7天: 定期检查，确保稳定性")
    print("- 第8天: 评估结果，决定是否正式迁移")


def main():
    """主函数"""
    print("销售激励系统重构 - 影子模式完整演示")
    
    # 演示影子模式
    success = demo_shadow_mode()
    
    if success:
        # 演示生产环境集成
        demo_production_integration()
        
        print("\n🎉 影子模式演示成功！")
        print("\n下一步:")
        print("1. 在生产环境中部署影子模式")
        print("2. 运行1周进行充分验证")
        print("3. 根据验证结果决定正式迁移")
    else:
        print("\n❌ 影子模式演示失败，请检查错误信息")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
