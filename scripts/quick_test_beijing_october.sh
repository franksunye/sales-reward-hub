#!/bin/bash
# 北京2025年10月销售激励活动快速手工测试脚本
# 
# 使用方法:
# bash scripts/quick_test_beijing_october.sh
# 
# 或者分步执行:
# bash scripts/quick_test_beijing_october.sh api-only    # 仅测试API
# bash scripts/quick_test_beijing_october.sh job-only    # 仅执行Job
# bash scripts/quick_test_beijing_october.sh db-only     # 仅检查数据库

set -e  # 遇到错误立即退出

echo "🎯 北京2025年10月销售激励活动快速测试"
echo "=================================================="
echo "📅 测试时间: $(date)"
echo ""

# 检查是否在项目根目录
if [ ! -f "modules/core/beijing_jobs.py" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 清理环境函数
clean_environment() {
    echo "🧹 清理测试环境..."
    rm -f performance_data.db
    rm -f tasks.db
    rm -f performance_data_BJ-OCT.csv
    rm -f beijing_october_test_output.csv
    echo "✅ 环境清理完成"
    echo ""
}

# API测试函数
test_api() {
    echo "🌐 测试API数据获取..."
    echo "──────────────────────────────────────────"
    
    python -c "
import sys
sys.path.insert(0, '.')

try:
    from modules.core.beijing_jobs import _get_contract_data_with_source_type
    
    print('📡 正在获取北京10月API数据...')
    contract_data = _get_contract_data_with_source_type()
    
    print(f'📊 获取到 {len(contract_data)} 条合同数据')
    
    if contract_data:
        # 统计工单类型
        source_type_1 = len([c for c in contract_data if c.get('工单类型(sourceType)') == '1'])
        source_type_2 = len([c for c in contract_data if c.get('工单类型(sourceType)') == '2'])
        
        print(f'📈 数据分布:')
        print(f'  自引单 (sourceType=1): {source_type_1} 条')
        print(f'  平台单 (sourceType=2): {source_type_2} 条')
        print(f'  其他类型: {len(contract_data) - source_type_1 - source_type_2} 条')
        
        # 检查关键字段
        has_source_type = any('工单类型(sourceType)' in c for c in contract_data)
        has_project_address = any('项目地址(projectAddress)' in c for c in contract_data)
        
        print(f'🔍 关键字段检查:')
        print(f'  sourceType字段: {\"✅\" if has_source_type else \"❌\"}')
        print(f'  projectAddress字段: {\"✅\" if has_project_address else \"❌\"}')
        
        # 显示第一条数据示例
        if contract_data:
            first_contract = contract_data[0]
            print(f'📋 第一条数据示例:')
            print(f'  合同ID: {first_contract.get(\"合同ID(_id)\", \"N/A\")}')
            print(f'  管家: {first_contract.get(\"管家(serviceHousekeeper)\", \"N/A\")}')
            print(f'  金额: {first_contract.get(\"合同金额(adjustRefundMoney)\", \"N/A\")}')
            print(f'  工单类型: {first_contract.get(\"工单类型(sourceType)\", \"N/A\")}')
            print(f'  状态: {first_contract.get(\"Status\", \"N/A\")}')
            print(f'  支付状态: {first_contract.get(\"State\", \"N/A\")}')
    else:
        print('❌ 未获取到数据')
        
except Exception as e:
    print(f'❌ API测试失败: {e}')
    import traceback
    traceback.print_exc()
"
    echo ""
}

# Job执行函数
execute_job() {
    echo "🚀 执行北京10月Job函数..."
    echo "──────────────────────────────────────────"
    
    python -c "
import sys
sys.path.insert(0, '.')
from datetime import datetime

try:
    from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing_v2
    
    print('🎯 开始执行北京10月销售激励活动...')
    start_time = datetime.now()
    
    # 执行Job函数
    result = signing_and_sales_incentive_oct_beijing_v2()
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    print(f'✅ 执行完成，耗时: {execution_time:.2f}秒')
    print(f'📊 处理了 {len(result)} 条记录')
    
    # 统计奖励情况
    reward_count = len([r for r in result if r.rewards])
    total_rewards = sum(len(r.rewards) for r in result)
    
    print(f'🏆 获得奖励的记录: {reward_count} 条')
    print(f'🎁 总奖励数量: {total_rewards} 个')
    
    # 统计订单类型
    platform_count = len([r for r in result if r.order_type == 'PLATFORM'])
    self_referral_count = len([r for r in result if r.order_type == 'SELF_REFERRAL'])
    
    print(f'📦 订单类型分布:')
    print(f'  平台单: {platform_count} 条')
    print(f'  自引单: {self_referral_count} 条')
    
    # 显示前3条有奖励的记录
    reward_records = [r for r in result if r.rewards][:3]
    if reward_records:
        print(f'🎉 前3条奖励记录:')
        for i, record in enumerate(reward_records):
            rewards_str = ', '.join([f'{r.reward_type}-{r.reward_name}' for r in record.rewards])
            print(f'  {i+1}. {record.housekeeper} | {record.order_type} | {rewards_str}')
    
except Exception as e:
    print(f'❌ Job执行失败: {e}')
    import traceback
    traceback.print_exc()
"
    echo ""
}

# 数据库检查函数
check_database() {
    echo "🗄️ 检查数据库结果..."
    echo "──────────────────────────────────────────"
    
    if [ ! -f "performance_data.db" ]; then
        echo "❌ 数据库文件不存在"
        return 1
    fi
    
    python -c "
import sqlite3
import os

try:
    conn = sqlite3.connect('performance_data.db')
    cursor = conn.cursor()
    
    # 检查表
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
    tables = [table[0] for table in cursor.fetchall()]
    print(f'📋 数据库表: {tables}')
    
    if 'performance_data' in tables:
        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM performance_data')
        total_count = cursor.fetchone()[0]
        print(f'📊 总记录数: {total_count}')
        
        # 北京10月记录数
        cursor.execute('SELECT COUNT(*) FROM performance_data WHERE activity_code = \"BJ-OCT\"')
        bj_oct_count = cursor.fetchone()[0]
        print(f'🎯 北京10月记录数: {bj_oct_count}')
        
        # 按订单类型统计
        cursor.execute('SELECT order_type, COUNT(*) FROM performance_data WHERE activity_code = \"BJ-OCT\" GROUP BY order_type')
        order_stats = dict(cursor.fetchall())
        print(f'📦 订单类型统计: {order_stats}')
        
        # 奖励统计
        cursor.execute('SELECT COUNT(*) FROM performance_data WHERE activity_code = \"BJ-OCT\" AND rewards IS NOT NULL AND rewards != \"[]\"')
        reward_count = cursor.fetchone()[0]
        print(f'🏆 有奖励记录数: {reward_count}')
        
        # 管家统计（前5名）
        cursor.execute('SELECT housekeeper, COUNT(*) as cnt FROM performance_data WHERE activity_code = \"BJ-OCT\" GROUP BY housekeeper ORDER BY cnt DESC LIMIT 5')
        top_housekeepers = cursor.fetchall()
        print(f'👥 合同数前5名管家:')
        for i, (housekeeper, count) in enumerate(top_housekeepers):
            print(f'  {i+1}. {housekeeper}: {count} 条')
    
    conn.close()
    print('✅ 数据库检查完成')
    
except Exception as e:
    print(f'❌ 数据库检查失败: {e}')
"
    echo ""
}

# 导出结果函数
export_results() {
    echo "📤 导出测试结果..."
    echo "──────────────────────────────────────────"
    
    if [ ! -f "scripts/export_database_to_csv.py" ]; then
        echo "❌ 导出脚本不存在"
        return 1
    fi
    
    python scripts/export_database_to_csv.py --activity BJ-OCT --output beijing_october_test_output.csv
    
    if [ -f "beijing_october_test_output.csv" ]; then
        lines=$(wc -l < beijing_october_test_output.csv)
        size=$(du -h beijing_october_test_output.csv | cut -f1)
        echo "✅ 导出成功"
        echo "📊 文件行数: $lines"
        echo "📁 文件大小: $size"
        echo "📄 文件位置: beijing_october_test_output.csv"
    else
        echo "❌ 导出失败"
    fi
    echo ""
}

# 主执行逻辑
case "${1:-all}" in
    "api-only")
        clean_environment
        test_api
        ;;
    "job-only")
        execute_job
        ;;
    "db-only")
        check_database
        ;;
    "export-only")
        export_results
        ;;
    "all"|"")
        clean_environment
        test_api
        execute_job
        check_database
        export_results
        
        echo "🎉 北京10月功能测试完成！"
        echo "=================================================="
        echo "📋 后续检查建议:"
        echo "1. 检查数据库: sqlite3 performance_data.db"
        echo "2. 查看导出文件: cat beijing_october_test_output.csv"
        echo "3. 验证奖励逻辑是否正确"
        echo "4. 检查消息通知（如果启用）"
        echo ""
        ;;
    *)
        echo "用法: $0 [api-only|job-only|db-only|export-only|all]"
        echo ""
        echo "选项说明:"
        echo "  api-only    - 仅测试API数据获取"
        echo "  job-only    - 仅执行Job函数"
        echo "  db-only     - 仅检查数据库"
        echo "  export-only - 仅导出结果"
        echo "  all         - 执行完整测试（默认）"
        exit 1
        ;;
esac
