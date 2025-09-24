#!/usr/bin/env python3
"""
测试 performance_amount 修复效果
"""

import sqlite3
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_test_data(db_path: str):
    """创建测试数据"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 插入测试数据：包含历史合同和新合同
    test_data = [
        # 新合同
        ('BJ-SEP', 'contract_001', '张三', '服务商A', 10000, 10000, 'platform', 'project_001', False),
        ('BJ-SEP', 'contract_002', '张三', '服务商A', 15000, 15000, 'platform', 'project_002', False),
        # 历史合同
        ('BJ-SEP', 'contract_003', '张三', '服务商A', 20000, 20000, 'platform', 'project_003', True),
        ('BJ-SEP', 'contract_004', '张三', '服务商A', 8000, 8000, 'platform', 'project_004', True),
        # 李四的合同（新合同）
        ('BJ-SEP', 'contract_005', '李四', '服务商B', 12000, 12000, 'platform', 'project_005', False),
        # 上海数据
        ('SH-SEP', 'contract_006', '王五', '服务商C', 18000, 18000, 'platform', None, False),
        ('SH-SEP', 'contract_007', '王五', '服务商C', 22000, 22000, 'self_referral', None, False),
    ]
    
    for data in test_data:
        cursor.execute("""
            INSERT OR REPLACE INTO performance_data 
            (activity_code, contract_id, housekeeper, service_provider, 
             contract_amount, performance_amount, order_type, project_id, is_historical)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
    
    conn.commit()
    conn.close()
    print("✅ 测试数据创建完成")

def test_housekeeper_stats(db_path: str):
    """测试管家统计视图"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 测试 housekeeper_stats 视图:")
    print("-" * 50)
    
    cursor.execute("""
        SELECT housekeeper, activity_code, contract_count, total_amount,
               performance_amount, platform_amount, self_referral_amount, historical_count, new_count
        FROM housekeeper_stats
        ORDER BY housekeeper, activity_code
    """)

    results = cursor.fetchall()

    print(f"{'管家':<8} {'活动':<8} {'合同数':<6} {'总金额':<8} {'业绩金额':<8} {'平台金额':<8} {'自引金额':<8} {'历史':<4} {'新增':<4}")
    print("-" * 80)

    for row in results:
        housekeeper, activity, count, total, performance, platform, self_ref, historical, new = row
        print(f"{housekeeper:<8} {activity:<8} {count:<6} {total:<8.0f} {performance:<8.0f} {platform:<8.0f} {self_ref:<8.0f} {historical:<4} {new:<4}")

    # 验证张三的数据
    cursor.execute("""
        SELECT total_amount, performance_amount, platform_amount FROM housekeeper_stats
        WHERE housekeeper = '张三' AND activity_code = 'BJ-SEP'
    """)
    zhang_data = cursor.fetchone()
    zhang_total, zhang_performance, zhang_platform = zhang_data

    expected_zhang_total = 25000       # 只统计新合同：10000 + 15000
    expected_zhang_performance = 25000  # 只统计新合同：10000 + 15000
    expected_zhang_platform = 25000    # 只统计新合同平台单：10000 + 15000

    print(f"\n🔍 验证结果:")
    print(f"张三的总金额: {zhang_total} (期望: {expected_zhang_total})")
    print(f"张三的业绩金额: {zhang_performance} (期望: {expected_zhang_performance})")
    print(f"张三的平台单金额: {zhang_platform} (期望: {expected_zhang_platform})")

    all_correct = (zhang_total == expected_zhang_total and
                   zhang_performance == expected_zhang_performance and
                   zhang_platform == expected_zhang_platform)

    if all_correct:
        print("✅ 修复成功！所有累计金额字段都只统计了新合同")
    else:
        print("❌ 修复失败！部分字段仍然包含了历史合同")

    conn.close()
    return all_correct

def test_project_stats(db_path: str):
    """测试工单统计视图"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 测试 project_stats 视图:")
    print("-" * 40)
    
    cursor.execute("""
        SELECT project_id, activity_code, contract_count, total_amount, performance_amount
        FROM project_stats
        ORDER BY project_id
    """)

    results = cursor.fetchall()

    print(f"{'工单ID':<12} {'活动':<8} {'合同数':<6} {'总金额':<8} {'业绩金额':<8}")
    print("-" * 50)

    for row in results:
        project_id, activity, count, total, performance = row
        print(f"{project_id:<12} {activity:<8} {count:<6} {total:<8.0f} {performance:<8.0f}")

    # 验证历史工单的所有金额字段为0
    cursor.execute("""
        SELECT SUM(total_amount), SUM(performance_amount) FROM project_stats
        WHERE project_id IN ('project_003', 'project_004')
    """)
    historical_data = cursor.fetchone()
    historical_total = historical_data[0] or 0
    historical_performance = historical_data[1] or 0

    print(f"\n🔍 验证结果:")
    print(f"历史工单的总金额: {historical_total} (期望: 0)")
    print(f"历史工单的业绩金额: {historical_performance} (期望: 0)")

    all_correct = historical_total == 0 and historical_performance == 0

    if all_correct:
        print("✅ 修复成功！历史工单的所有金额字段被正确排除")
    else:
        print("❌ 修复失败！历史工单仍然被统计")

    conn.close()
    return all_correct

def test_activity_stats(db_path: str):
    """测试活动统计视图"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 测试 activity_stats 视图:")
    print("-" * 50)
    
    cursor.execute("""
        SELECT activity_code, total_contracts, total_amount, total_performance_amount, avg_contract_amount
        FROM activity_stats
        ORDER BY activity_code
    """)

    results = cursor.fetchall()

    print(f"{'活动':<8} {'总合同数':<8} {'总金额':<10} {'总业绩金额':<10} {'平均金额':<10}")
    print("-" * 60)

    for row in results:
        activity, contracts, total, performance, avg_amount = row
        avg_display = f"{avg_amount:.0f}" if avg_amount else "0"
        print(f"{activity:<8} {contracts:<8} {total:<10.0f} {performance:<10.0f} {avg_display:<10}")

    # 验证BJ-SEP的各项金额
    cursor.execute("""
        SELECT total_amount, total_performance_amount, avg_contract_amount FROM activity_stats
        WHERE activity_code = 'BJ-SEP'
    """)
    bj_data = cursor.fetchone()
    bj_total, bj_performance, bj_avg = bj_data

    expected_bj_total = 37000       # 新合同：10000 + 15000 + 12000
    expected_bj_performance = 37000  # 新合同：10000 + 15000 + 12000
    expected_bj_avg = 12333.33      # 平均：37000 / 3 ≈ 12333.33

    print(f"\n🔍 验证结果:")
    print(f"BJ-SEP活动总金额: {bj_total} (期望: {expected_bj_total})")
    print(f"BJ-SEP活动业绩金额: {bj_performance} (期望: {expected_bj_performance})")
    print(f"BJ-SEP平均合同金额: {bj_avg:.2f} (期望: {expected_bj_avg:.2f})")

    # 允许平均值有小的浮点误差
    avg_correct = abs(bj_avg - expected_bj_avg) < 1
    all_correct = (bj_total == expected_bj_total and
                   bj_performance == expected_bj_performance and
                   avg_correct)

    if all_correct:
        print("✅ 修复成功！活动统计的所有金额字段都只包含新合同")
    else:
        print("❌ 修复失败！活动统计仍然包含历史合同")

    conn.close()
    return all_correct

def main():
    """主函数"""
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'performance_data.db'
    
    print("🧪 测试 performance_amount 修复效果")
    print("=" * 60)
    
    # 创建测试数据
    create_test_data(db_path)
    
    # 运行测试
    test1_passed = test_housekeeper_stats(db_path)
    test2_passed = test_project_stats(db_path)
    test3_passed = test_activity_stats(db_path)
    
    # 总结
    print("\n📋 测试总结:")
    print("-" * 30)
    print(f"管家统计视图: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"工单统计视图: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"活动统计视图: {'✅ 通过' if test3_passed else '❌ 失败'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print("\n🎉 所有测试通过！performance_amount 修复成功")
        print("💡 现在业绩金额统计只包含新工单，不包含历史工单")
    else:
        print("\n❌ 部分测试失败，需要进一步检查")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
