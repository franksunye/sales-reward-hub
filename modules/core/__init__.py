"""
销售激励系统重构 - 核心模块
版本: v1.0
创建日期: 2025-01-08

这个包提供了重构后的核心功能：
- 统一的数据处理管道
- 配置驱动的奖励计算
- SQLite存储层
- 标准化的数据模型
"""

# 数据模型
from .data_models import (
    HousekeeperStats,
    ProcessingConfig,
    ContractData,
    RewardInfo,
    PerformanceRecord,
    JobConfig,
    OrderType,
    City
)

# 存储层
from .storage import (
    PerformanceDataStore,
    SQLitePerformanceDataStore,
    create_data_store
)

# 处理管道
from .processing_pipeline import (
    DataProcessingPipeline,
    PipelineValidator,
    create_processing_pipeline
)

# 奖励计算
from .reward_calculator import (
    RewardCalculator,
    create_reward_calculator
)

# 记录构建
from .record_builder import (
    RecordBuilder,
    BatchRecordBuilder,
    create_record_builder,
    create_batch_record_builder
)

# 配置适配器
from .config_adapter import (
    ConfigAdapter,
    get_reward_config,
    get_bonus_pool_ratio,
    validate_all_configs
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Refactoring Team"
__description__ = "销售激励系统重构核心模块"

# 导出的主要接口
__all__ = [
    # 数据模型
    'HousekeeperStats',
    'ProcessingConfig', 
    'ContractData',
    'RewardInfo',
    'PerformanceRecord',
    'JobConfig',
    'OrderType',
    'City',
    
    # 存储层
    'PerformanceDataStore',
    'SQLitePerformanceDataStore',
    'create_data_store',
    
    # 处理管道
    'DataProcessingPipeline',
    'PipelineValidator',
    'create_processing_pipeline',
    
    # 奖励计算
    'RewardCalculator',
    'create_reward_calculator',
    
    # 记录构建
    'RecordBuilder',
    'BatchRecordBuilder',
    'create_record_builder',
    'create_batch_record_builder',

    # 配置适配器
    'ConfigAdapter',
    'get_reward_config',
    'get_bonus_pool_ratio',
    'validate_all_configs',
]


def get_version_info():
    """获取版本信息"""
    return {
        'version': __version__,
        'author': __author__,
        'description': __description__
    }


def create_standard_pipeline(config_key: str, activity_code: str, city: str, **kwargs):
    """创建标准处理管道的便捷函数"""
    import os
    from .data_models import City, ProcessingConfig
    
    # DB_SOURCE 优先于调用方硬编码，确保本地/云端可统一切换
    db_source = os.getenv("DB_SOURCE", "").strip().lower()
    requested_storage = kwargs.get("storage_type", "sqlite")
    if db_source == "cloud":
        resolved_storage = "turso"
    elif db_source == "local":
        resolved_storage = "sqlite"
    else:
        resolved_storage = requested_storage

    # 创建处理配置
    config = ProcessingConfig(
        config_key=config_key,
        activity_code=activity_code,
        city=City(city),
        housekeeper_key_format=kwargs.get('housekeeper_key_format', '管家'),
        storage_type=resolved_storage,
        enable_dual_track=kwargs.get('enable_dual_track', False),
        enable_historical_contracts=kwargs.get('enable_historical_contracts', False),
        enable_project_limit=kwargs.get('enable_project_limit', False),
        enable_csv_output=kwargs.get('enable_csv_output', False)  # 默认关闭CSV输出
    )
    
    # 创建存储实例
    storage_kwargs = {k: v for k, v in kwargs.items() if k not in ['housekeeper_key_format', 'storage_type', 'enable_dual_track', 'enable_historical_contracts', 'enable_project_limit', 'enable_csv_output']}
    if config.storage_type == "sqlite":
        storage_kwargs.setdefault("db_path", os.getenv("LOCAL_DB_PATH", kwargs.get("db_path", "performance_data.db")))
    elif config.storage_type == "turso":
        storage_kwargs.setdefault("db_url", os.getenv("TURSO_DB_URL"))
        storage_kwargs.setdefault("auth_token", os.getenv("TURSO_AUTH_TOKEN"))

    store = create_data_store(
        storage_type=config.storage_type,
        **storage_kwargs
    )
    
    # 创建处理管道
    pipeline = create_processing_pipeline(config, store)
    
    return pipeline, config, store
