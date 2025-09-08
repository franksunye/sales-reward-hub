"""
销售激励系统重构 - 生产环境配置
版本: v1.0
创建日期: 2025-01-08

生产环境专用配置，优化性能和稳定性。
"""

import os
import logging
from typing import Dict, Any

# 生产环境数据库配置
PRODUCTION_DB_CONFIG = {
    'db_path': os.getenv('INCENTIVE_DB_PATH', 'performance_data.db'),
    'timeout': 30.0,  # 数据库连接超时
    'check_same_thread': False,  # 支持多线程访问
    'isolation_level': None,  # 自动提交模式
}

# 生产环境日志配置
PRODUCTION_LOG_CONFIG = {
    'level': logging.INFO,
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': [
        {
            'type': 'file',
            'filename': os.getenv('INCENTIVE_LOG_FILE', 'incentive_system.log'),
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5
        },
        {
            'type': 'console',
            'level': logging.WARNING  # 控制台只显示警告和错误
        }
    ]
}

# 生产环境性能配置
PRODUCTION_PERFORMANCE_CONFIG = {
    'batch_size': 1000,  # 批处理大小
    'max_memory_usage': 512 * 1024 * 1024,  # 512MB内存限制
    'enable_cache': True,  # 启用缓存
    'cache_size': 1000,  # 缓存大小
}

# 生产环境安全配置
PRODUCTION_SECURITY_CONFIG = {
    'enable_data_validation': True,  # 启用数据验证
    'max_contract_amount': 10000000,  # 最大合同金额（1000万）
    'enable_audit_log': True,  # 启用审计日志
    'sensitive_fields': [  # 敏感字段（日志中会被脱敏）
        '客户联系地址(contactsAddress)',
        '项目地址(projectAddress)',
        '管家ID(serviceHousekeeperId)'
    ]
}

# 生产环境监控配置
PRODUCTION_MONITORING_CONFIG = {
    'enable_metrics': True,  # 启用指标收集
    'metrics_interval': 60,  # 指标收集间隔（秒）
    'alert_thresholds': {
        'processing_time': 300,  # 处理时间超过5分钟告警
        'error_rate': 0.05,  # 错误率超过5%告警
        'memory_usage': 0.8,  # 内存使用率超过80%告警
    }
}


def setup_production_logging():
    """设置生产环境日志"""
    import logging.handlers
    
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(PRODUCTION_LOG_CONFIG['level'])
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        filename=PRODUCTION_LOG_CONFIG['handlers'][0]['filename'],
        maxBytes=PRODUCTION_LOG_CONFIG['handlers'][0]['max_bytes'],
        backupCount=PRODUCTION_LOG_CONFIG['handlers'][0]['backup_count'],
        encoding='utf-8'
    )
    file_handler.setLevel(PRODUCTION_LOG_CONFIG['level'])
    file_handler.setFormatter(logging.Formatter(PRODUCTION_LOG_CONFIG['format']))
    root_logger.addHandler(file_handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(PRODUCTION_LOG_CONFIG['handlers'][1]['level'])
    console_handler.setFormatter(logging.Formatter(PRODUCTION_LOG_CONFIG['format']))
    root_logger.addHandler(console_handler)
    
    logging.info("生产环境日志配置完成")


def validate_production_environment():
    """验证生产环境配置"""
    checks = []
    
    # 检查数据库路径
    db_path = PRODUCTION_DB_CONFIG['db_path']
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if not os.path.exists(db_dir):
        checks.append(f"❌ 数据库目录不存在: {db_dir}")
    elif not os.access(db_dir, os.W_OK):
        checks.append(f"❌ 数据库目录无写权限: {db_dir}")
    else:
        checks.append(f"✅ 数据库路径检查通过: {db_path}")
    
    # 检查日志路径
    log_file = PRODUCTION_LOG_CONFIG['handlers'][0]['filename']
    log_dir = os.path.dirname(os.path.abspath(log_file))
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
            checks.append(f"✅ 创建日志目录: {log_dir}")
        except Exception as e:
            checks.append(f"❌ 无法创建日志目录: {log_dir}, 错误: {e}")
    else:
        checks.append(f"✅ 日志路径检查通过: {log_file}")
    
    # 检查内存限制
    import psutil
    available_memory = psutil.virtual_memory().available
    required_memory = PRODUCTION_PERFORMANCE_CONFIG['max_memory_usage']
    if available_memory < required_memory * 2:  # 至少需要2倍的可用内存
        checks.append(f"⚠️ 可用内存不足: {available_memory / 1024 / 1024:.0f}MB < {required_memory * 2 / 1024 / 1024:.0f}MB")
    else:
        checks.append(f"✅ 内存检查通过: {available_memory / 1024 / 1024:.0f}MB 可用")
    
    # 检查磁盘空间
    disk_usage = psutil.disk_usage(db_dir)
    if disk_usage.free < 1024 * 1024 * 1024:  # 至少需要1GB空闲空间
        checks.append(f"⚠️ 磁盘空间不足: {disk_usage.free / 1024 / 1024 / 1024:.1f}GB")
    else:
        checks.append(f"✅ 磁盘空间检查通过: {disk_usage.free / 1024 / 1024 / 1024:.1f}GB 可用")
    
    return checks


def get_production_config() -> Dict[str, Any]:
    """获取完整的生产环境配置"""
    return {
        'database': PRODUCTION_DB_CONFIG,
        'logging': PRODUCTION_LOG_CONFIG,
        'performance': PRODUCTION_PERFORMANCE_CONFIG,
        'security': PRODUCTION_SECURITY_CONFIG,
        'monitoring': PRODUCTION_MONITORING_CONFIG,
    }


class ProductionMetrics:
    """生产环境指标收集器"""
    
    def __init__(self):
        self.metrics = {
            'processing_count': 0,
            'processing_time_total': 0.0,
            'error_count': 0,
            'last_processing_time': None,
        }
    
    def record_processing(self, processing_time: float, record_count: int, success: bool = True):
        """记录处理指标"""
        self.metrics['processing_count'] += 1
        self.metrics['processing_time_total'] += processing_time
        self.metrics['last_processing_time'] = processing_time
        
        if not success:
            self.metrics['error_count'] += 1
        
        # 记录详细指标
        logging.info(f"处理指标: 时间={processing_time:.2f}s, 记录数={record_count}, 成功={success}")
        
        # 检查告警阈值
        self._check_alerts(processing_time)
    
    def _check_alerts(self, processing_time: float):
        """检查告警阈值"""
        thresholds = PRODUCTION_MONITORING_CONFIG['alert_thresholds']
        
        if processing_time > thresholds['processing_time']:
            logging.warning(f"处理时间告警: {processing_time:.2f}s > {thresholds['processing_time']}s")
        
        if self.metrics['processing_count'] > 0:
            error_rate = self.metrics['error_count'] / self.metrics['processing_count']
            if error_rate > thresholds['error_rate']:
                logging.warning(f"错误率告警: {error_rate:.2%} > {thresholds['error_rate']:.2%}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        if self.metrics['processing_count'] == 0:
            return {'status': 'no_data'}
        
        avg_time = self.metrics['processing_time_total'] / self.metrics['processing_count']
        error_rate = self.metrics['error_count'] / self.metrics['processing_count']
        
        return {
            'total_processing': self.metrics['processing_count'],
            'average_time': avg_time,
            'error_rate': error_rate,
            'last_processing_time': self.metrics['last_processing_time'],
            'status': 'healthy' if error_rate < 0.05 else 'warning'
        }


# 全局指标收集器实例
production_metrics = ProductionMetrics()


def initialize_production_environment():
    """初始化生产环境"""
    print("初始化生产环境...")
    
    # 设置日志
    setup_production_logging()
    
    # 验证环境
    checks = validate_production_environment()
    for check in checks:
        print(check)
    
    # 检查是否有错误
    errors = [check for check in checks if check.startswith('❌')]
    if errors:
        raise RuntimeError(f"生产环境检查失败: {len(errors)} 个错误")
    
    logging.info("生产环境初始化完成")
    return True


if __name__ == "__main__":
    # 测试生产环境配置
    try:
        initialize_production_environment()
        print("✅ 生产环境配置验证通过")
        
        # 显示配置摘要
        config = get_production_config()
        print(f"数据库路径: {config['database']['db_path']}")
        print(f"日志文件: {config['logging']['handlers'][0]['filename']}")
        print(f"内存限制: {config['performance']['max_memory_usage'] / 1024 / 1024:.0f}MB")
        
    except Exception as e:
        print(f"❌ 生产环境配置验证失败: {e}")
        exit(1)
