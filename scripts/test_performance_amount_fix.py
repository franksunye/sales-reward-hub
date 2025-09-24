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
               performance_amount, historical_count, new_count
        FROM housekeeper_stats
        ORDER BY housekeeper, activity_code
    """)
    
    results = cursor.fetchall()
    
    print(f"{'管家':<8} {'活动':<8} {'合同数':<6} {'总金额':<8} {'业绩金额':<8} {'历史':<4} {'新增':<4}")
    print("-" * 50)
    
    for row in results:
        housekeeper, activity, count, total, performance, historical, new = row
        print(f"{housekeeper:<8} {activity:<8} {count:<6} {total:<8.0f} {performance:<8.0f} {historical:<4} {new:<4}")
    
    # 验证张三的数据
    cursor.execute("""
        SELECT performance_amount FROM housekeeper_stats 
        WHERE housekeeper = '张三' AND activity_code = 'BJ-SEP'
    """)
    zhang_performance = cursor.fetchone()[0]
    
    expected_zhang_performance = 25000  # 只统计新合同：10000 + 15000
    
    print(f"\n🔍 验证结果:")
    print(f"张三的业绩金额: {zhang_performance} (期望: {expected_zhang_performance})")
    
    if zhang_performance == expected_zhang_performance:
        print("✅ 修复成功！只统计了新合同的业绩金额")
    else:
        print("❌ 修复失败！仍然包含了历史合同的业绩金额")
    
    conn.close()
    return zhang_performance == expected_zhang_performance

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
    print("-" * 40)
    
    for row in results:
        project_id, activity, count, total, performance = row
        print(f"{project_id:<12} {activity:<8} {count:<6} {total:<8.0f} {performance:<8.0f}")
    
    # 验证历史工单的业绩金额为0
    cursor.execute("""
        SELECT SUM(performance_amount) FROM project_stats
        WHERE project_id IN ('project_003', 'project_004')
    """)
    historical_performance = cursor.fetchone()[0] or 0

    print(f"\n🔍 验证结果:")
    print(f"历史工单的业绩金额总和: {historical_performance} (期望: 0)")

    if historical_performance == 0:
        print("✅ 修复成功！历史工单的业绩金额被正确排除")
    else:
        print("❌ 修复失败！历史工单仍然被统计")

    conn.close()
    return historical_performance == 0

def test_activity_stats(db_path: str):
    """测试活动统计视图"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 测试 activity_stats 视图:")
    print("-" * 50)
    
    cursor.execute("""
        SELECT activity_code, total_contracts, total_amount, total_performance_amount
        FROM activity_stats
        ORDER BY activity_code
    """)
    
    results = cursor.fetchall()
    
    print(f"{'活动':<8} {'总合同数':<8} {'总金额':<10} {'总业绩金额':<10}")
    print("-" * 50)
    
    for row in results:
        activity, contracts, total, performance = row
        print(f"{activity:<8} {contracts:<8} {total:<10.0f} {performance:<10.0f}")
    
    # 验证BJ-SEP的业绩金额
    cursor.execute("""
        SELECT total_performance_amount FROM activity_stats 
        WHERE activity_code = 'BJ-SEP'
    """)
    bj_performance = cursor.fetchone()[0]
    
    expected_bj_performance = 37000  # 新合同：10000 + 15000 + 12000
    
    print(f"\n🔍 验证结果:")
    print(f"BJ-SEP活动业绩金额: {bj_performance} (期望: {expected_bj_performance})")
    
    if bj_performance == expected_bj_performance:
        print("✅ 修复成功！活动统计只包含新合同的业绩金额")
    else:
        print("❌ 修复失败！活动统计仍然包含历史合同的业绩金额")
    
    conn.close()
    return bj_performance == expected_bj_performance

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
