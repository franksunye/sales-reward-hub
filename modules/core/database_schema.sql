-- 销售激励系统重构 - 数据库Schema设计
-- 版本: v1.0
-- 创建日期: 2025-01-08

-- 统一的业绩数据表，支持所有城市和月份
CREATE TABLE performance_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 基础标识字段
    activity_code TEXT NOT NULL,           -- 活动编码: 'BJ-JUN', 'BJ-SEP', 'SH-APR', 'SH-SEP'
    contract_id TEXT NOT NULL,             -- 合同ID
    
    -- 管家和服务商信息
    housekeeper TEXT NOT NULL,             -- 管家姓名
    service_provider TEXT,                 -- 服务商名称
    
    -- 合同金额信息
    contract_amount REAL NOT NULL,         -- 合同金额
    performance_amount REAL NOT NULL,      -- 计入业绩金额
    paid_amount REAL DEFAULT 0,            -- 支付金额
    
    -- 工单信息（北京特有）
    project_id TEXT,                       -- 工单编号，用于北京的项目上限控制
    
    -- 订单类型（上海双轨统计）
    order_type TEXT DEFAULT 'platform',    -- 'platform' 或 'self_referral'
    
    -- 序号信息
    contract_sequence INTEGER DEFAULT 0,   -- 活动期内第几个合同（全局序号）

    -- 奖励信息
    reward_types TEXT,                     -- 奖励类型（JSON格式）
    reward_names TEXT,                     -- 奖励名称（JSON格式）
    
    -- 历史合同标记（北京9月特有）
    is_historical BOOLEAN DEFAULT FALSE,   -- 是否为历史合同
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 扩展字段（JSON格式存储城市特有数据）
    extensions TEXT,                       -- JSON格式存储额外字段
    
    -- 唯一约束：同一活动中的合同ID不能重复
    UNIQUE(activity_code, contract_id)
);

-- 性能优化索引
CREATE INDEX IF NOT EXISTS idx_housekeeper_activity ON performance_data(housekeeper, activity_code);
CREATE INDEX IF NOT EXISTS idx_contract_lookup ON performance_data(contract_id, activity_code);
CREATE INDEX IF NOT EXISTS idx_project_activity ON performance_data(project_id, activity_code);
CREATE INDEX IF NOT EXISTS idx_order_type ON performance_data(order_type, activity_code);
CREATE INDEX IF NOT EXISTS idx_created_at ON performance_data(created_at);

-- 管家累计统计视图（替代复杂的内存计算）
CREATE VIEW housekeeper_stats AS
SELECT
    housekeeper,
    activity_code,
    COUNT(*) as contract_count,
    -- 🔧 修复：累计合同金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN is_historical = FALSE THEN contract_amount ELSE 0 END) as total_amount,
    -- 🔧 修复：累计计入业绩金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN is_historical = FALSE THEN performance_amount ELSE 0 END) as performance_amount,
    -- 双轨统计（上海特有）
    SUM(CASE WHEN order_type = 'platform' THEN 1 ELSE 0 END) as platform_count,
    -- 🔧 修复：累计平台单金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN order_type = 'platform' AND is_historical = FALSE THEN contract_amount ELSE 0 END) as platform_amount,
    SUM(CASE WHEN order_type = 'self_referral' THEN 1 ELSE 0 END) as self_referral_count,
    -- 🔧 修复：累计自引单金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN order_type = 'self_referral' AND is_historical = FALSE THEN contract_amount ELSE 0 END) as self_referral_amount,
    -- 历史合同统计（北京9月特有）
    SUM(CASE WHEN is_historical = TRUE THEN 1 ELSE 0 END) as historical_count,
    SUM(CASE WHEN is_historical = FALSE THEN 1 ELSE 0 END) as new_count
FROM performance_data
GROUP BY housekeeper, activity_code;

-- 工单累计金额视图（北京特有的工单上限控制）
CREATE VIEW project_stats AS
SELECT
    project_id,
    activity_code,
    COUNT(*) as contract_count,
    -- 🔧 修复：工单累计合同金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN is_historical = FALSE THEN contract_amount ELSE 0 END) as total_amount,
    -- 🔧 修复：工单累计业绩金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN is_historical = FALSE THEN performance_amount ELSE 0 END) as performance_amount
FROM performance_data
WHERE project_id IS NOT NULL
GROUP BY project_id, activity_code;

-- 活动统计视图（整体数据概览）
CREATE VIEW activity_stats AS
SELECT
    activity_code,
    COUNT(*) as total_contracts,
    COUNT(DISTINCT housekeeper) as unique_housekeepers,
    -- 🔧 修复：活动总合同金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN is_historical = FALSE THEN contract_amount ELSE 0 END) as total_amount,
    -- 🔧 修复：活动总业绩金额仅计入新工单，不计入历史工单
    SUM(CASE WHEN is_historical = FALSE THEN performance_amount ELSE 0 END) as total_performance_amount,
    -- 🔧 修复：平均合同金额仅基于新工单计算，不包含历史工单
    AVG(CASE WHEN is_historical = FALSE THEN contract_amount ELSE NULL END) as avg_contract_amount,
    MIN(created_at) as first_contract_time,
    MAX(created_at) as last_contract_time
FROM performance_data
GROUP BY activity_code;

-- 数据库版本信息表
CREATE TABLE schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 插入初始版本信息
INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial schema for refactored incentive system');
