# config.py
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 上海的特殊配置选项（已弃用，请使用 REWARD_CONFIGS 中的配置）
# @deprecated: 以下配置已被通用化配置替换，仅保留用于兼容性
PERFORMANCE_AMOUNT_CAP = 40000  # 单个合同计入业绩金额上限 - 已弃用
ENABLE_PERFORMANCE_AMOUNT_CAP = False  # 是否启用业绩金额上限 - 已弃用


## 北京的通用配置选项-运营群名称以及运营执行人

WECOM_GROUP_NAME_BJ = '（北京）修链服务运营'
CAMPAIGN_CONTACT_BJ = '王爽'

## 上海的通用配置选项-运营群名称以及运营执行人
WECOM_GROUP_NAME_SH = '（上海）运营群'
CAMPAIGN_CONTACT_SH = '满浩浩'


# 通用奖励配置
REWARD_CONFIGS = {
    # 北京2025年9月活动配置
    "BJ-2025-09": {
        "lucky_number": "5",  # 基于个人合同顺序的倍数
        "lucky_number_mode": "personal_sequence",  # 个人顺序模式
        "lucky_number_sequence_type": "personal",  # 幸运数字使用的序号类型：personal（个人序号）或 global（全局序号）
        "lucky_rewards": {
            "base": {"name": "接好运", "threshold": 0},
            "high": {"name": "接好运", "threshold": 999999999}  # 统一奖励，不区分金额
        },
        "performance_limits": {
            "single_project_limit": 50000,  # 调整为5万
            "enable_cap": True,
            "single_contract_cap": 50000
        },
        "tiered_rewards": {
            "min_contracts": 10,  # 提升至10个合同
            "tiers": [
                {"name": "达标奖", "threshold": 80000},
                {"name": "优秀奖", "threshold": 180000},
                {"name": "精英奖", "threshold": 280000}
            ]
        },
        "awards_mapping": {
            "接好运": "58",  # 统一58元
            "达标奖": "400",  # 翻倍
            "优秀奖": "800",  # 翻倍
            "精英奖": "1600"  # 翻倍
        },
        # 奖励计算策略配置
        "reward_calculation_strategy": {
            "type": "single_track",  # 单轨激励
            "rules": {
                "default": {
                    "enable_tiered_rewards": True,
                    "stats_source": "total"  # 使用总统计数据
                }
            }
        },
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },
    # 北京2025年10月活动配置
    "BJ-2025-10": {
        "lucky_number": "5",  # 基于个人“平台单”合同顺序的倍数
        "lucky_number_mode": "personal_sequence",  # 个人合同顺序模式
        "lucky_number_sequence_type": "platform_only",  # 幸运数字仅基于平台单序号
        "lucky_rewards": {
            "base": {"name": "接好运", "threshold": 0},
            "high": {"name": "接好运", "threshold": 999999999}  # 统一奖励，不区分金额
        },
        "performance_limits": {
            "single_project_limit": 50000,  # 平台单工单上限5万
            "enable_cap": True,
            "single_contract_cap": 50000,  # 平台单合同上限5万
            # 新增：差异化金额上限配置
            "self_referral_contract_cap": 200000,  # 自引单合同上限20万
            "self_referral_project_limit": 200000   # 自引单工单上限20万
        },
        "tiered_rewards": {
            "min_contracts": 10,  # 10个合同，“平台单”以及“自引单”，即所有合同累计
            "tiers": [
                {"name": "达标奖", "threshold": 100000},
                {"name": "优秀奖", "threshold": 180000},
                {"name": "精英奖", "threshold": 300000},
                {"name": "卓越奖", "threshold": 460000}
            ]
        },
        "awards_mapping": {
            "接好运": "58",  
            "达标奖": "200",  
            "优秀奖": "400",  
            "精英奖": "800",
            "卓越奖": "1600"
        },
        # 自引单奖励配置（北京10月不启用）
        "self_referral_rewards": {
            "enable": False  # 北京10月不需要自引单独立奖励
        },
        # 奖励计算策略配置
        "reward_calculation_strategy": {
            "type": "dual_track",  # 启用双轨统计
            "rules": {
                "default": {
                    "enable_tiered_rewards": True,
                    "stats_source": "total"  # 节节高使用总统计数据
                }
            }
        },
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },
    # 上海2025年9月活动配置
    "SH-2025-09": {
        "lucky_number": "",  # 禁用幸运奖
        "lucky_number_sequence_type": "global",  # 如果启用幸运奖，上海早期使用全局序号
        "performance_limits": {
            "enable_cap": False,  # 上海不启用业绩上限
            "single_contract_cap": 40000
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 平台单需要5个合同
            "tiers": [
                {"name": "基础奖", "threshold": 40000},
                {"name": "达标奖", "threshold": 60000},
                {"name": "优秀奖", "threshold": 80000},
                {"name": "精英奖", "threshold": 120000},
                {"name": "卓越奖", "threshold": 160000}
            ]
        },
        "awards_mapping": {
            # 平台单奖励（复用上海4月配置）
            "基础奖": "200",
            "达标奖": "300",
            "优秀奖": "400",
            "精英奖": "800",
            "卓越奖": "1200",
            # 自引单奖励（新增）
            "红包": "50"
        },
        # 新增：自引单奖励配置
        "self_referral_rewards": {
            "enable": True,  # 启用自引单奖励
            "reward_type": "自引单",
            "reward_name": "红包",
            "deduplication_field": "projectAddress"  # 去重字段
            # 注意：奖励金额统一在awards_mapping中定义，避免重复配置
        },
        # 奖励计算策略配置
        "reward_calculation_strategy": {
            "type": "dual_track",  # 双轨激励
            "rules": {
                "platform": {
                    "enable_tiered_rewards": True,
                    "stats_source": "platform_only"  # 使用平台单统计数据
                },
                "self_referral": {
                    "enable_tiered_rewards": False,  # 自引单不参与节节高奖励
                    "stats_source": "self_referral_only"  # 使用自引单统计数据
                }
            }
        }
    },
    # 上海2025年10月活动配置
    "SH-2025-10": {
        "lucky_number": "",  # 禁用幸运奖
        "lucky_number_sequence_type": "global",  # 如果启用幸运奖，上海早期使用全局序号
        "performance_limits": {
            "enable_cap": False,  # 上海不启用业绩上限
            "single_contract_cap": 40000
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 平台单需要5个合同
            "tiers": [
                {"name": "基础奖", "threshold": 40000},
                {"name": "达标奖", "threshold": 60000},
                {"name": "优秀奖", "threshold": 80000},
                {"name": "精英奖", "threshold": 120000},
                {"name": "卓越奖", "threshold": 160000}
            ]
        },
        "awards_mapping": {
            # 平台单奖励（复用上海4月配置）
            "基础奖": "200",
            "达标奖": "300",
            "优秀奖": "400",
            "精英奖": "800",
            "卓越奖": "1200",
            # 自引单奖励（新增）
            # "红包": "50"
        },
        # 新增：自引单奖励配置
        "self_referral_rewards": {
            "enable": False,  # 启用自引单奖励
            "reward_type": "自引单",
            "reward_name": "红包",
            "deduplication_field": "projectAddress"  # 去重字段
            # 注意：奖励金额统一在awards_mapping中定义，避免重复配置
        },
        # 奖励计算策略配置
        "reward_calculation_strategy": {
            "type": "single_track",  # 单轨激励：仅平台单
            "rules": {
                "platform": {
                    "enable_tiered_rewards": True,
                    "stats_source": "platform_only"  # 使用平台单统计数据
                },
                "self_referral": {
                    "enable_tiered_rewards": False,  # 自引单不参与节节高奖励
                    "stats_source": "self_referral_only"  # 使用自引单统计数据
                }
            }
        }
    },
    # 上海2025年11月活动配置（规则与10月完全一致）
    "SH-2025-11": {
        "lucky_number": "",  # 禁用幸运奖
        "lucky_number_sequence_type": "global",  # 如果启用幸运奖，上海早期使用全局序号
        "performance_limits": {
            "enable_cap": False,  # 上海不启用业绩上限
            "single_contract_cap": 40000
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 平台单需要5个合同
            "tiers": [
                {"name": "基础奖", "threshold": 40000},
                {"name": "达标奖", "threshold": 60000},
                {"name": "优秀奖", "threshold": 80000},
                {"name": "精英奖", "threshold": 120000},
                {"name": "卓越奖", "threshold": 160000}
            ]
        },
        "awards_mapping": {
            # 平台单奖励（复用上海4月配置）
            "基础奖": "200",
            "达标奖": "300",
            "优秀奖": "400",
            "精英奖": "800",
            "卓越奖": "1200",
            # 自引单奖励（新增）
            # "红包": "50"
        },
        # 新增：自引单奖励配置
        "self_referral_rewards": {
            "enable": False,  # 启用自引单奖励
            "reward_type": "自引单",
            "reward_name": "红包",
            "deduplication_field": "projectAddress"  # 去重字段
            # 注意：奖励金额统一在awards_mapping中定义，避免重复配置
        },
        # 奖励计算策略配置
        "reward_calculation_strategy": {
            "type": "single_track",  # 单轨激励：仅平台单
            "rules": {
                "platform": {
                    "enable_tiered_rewards": True,
                    "stats_source": "platform_only"  # 使用平台单统计数据
                },
                "self_referral": {
                    "enable_tiered_rewards": False,  # 自引单不参与节节高奖励
                    "stats_source": "self_referral_only"  # 使用自引单统计数据
                }
            }
        }
    },
    # 上海2025年12月活动配置（仅播报模式，不计算奖励）
    "SH-2025-12": {
        # 禁用幸运数字
        "lucky_number": "",
        "lucky_number_sequence_type": "global",

        # 禁用幸运数字奖励
        "lucky_rewards": {
            "base": {"name": "", "threshold": 0},
            "high": {"name": "", "threshold": 999999999}
        },

        # 性能限制配置（可选，因为无奖励计算）
        "performance_limits": {
            "enable_cap": False,  # 不启用上限
            "single_contract_cap": 40000
        },

        # 禁用节节高奖励
        "tiered_rewards": {
            "min_contracts": 0,  # 无门槛
            "tiers": []  # 空奖励列表
        },

        # 空奖励映射
        "awards_mapping": {},

        # 禁用自引单奖励
        "self_referral_rewards": {
            "enable": False
        },

        # 奖励计算策略：仅播报模式
        "reward_calculation_strategy": {
            "type": "announcement_only",  # 仅播报策略
            "rules": {
                "default": {
                    "enable_tiered_rewards": False,
                    "stats_source": "platform_only"
                }
            }
        },

        # 通知配置：仅播报模式
        "notification_config": {
            "template_type": "announcement_only",  # 消息模板类型
            "enable_award_notification": False,  # 禁用个人奖励通知
            "show_order_type": False,  # 不显示工单类型
            "show_dual_track_stats": False,  # 不显示双轨统计
            "show_reward_progress": False,  # 不显示奖励进度
            "closing_message": "继续加油，再接再厉！"  # 固定结束语
        },

        # 数据处理配置
        "processing_config": {
            "process_platform_only": True,  # 仅处理平台单（修复后支持字符串类型的sourceType）
            "enable_historical_contracts": False  # 不处理历史合同
        },

        # 徽章配置
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },
    # 北京2025年11月活动配置
    "BJ-2025-11": {
        # 禁用幸运数字
        "lucky_number": "",
        "lucky_number_mode": "personal_sequence",
        "lucky_number_sequence_type": "personal",

        # 禁用幸运数字奖励
        "lucky_rewards": {
            "base": {"name": "", "threshold": 0},
            "high": {"name": "", "threshold": 999999999}
        },

        # 性能限制配置（可选，因为无奖励计算）
        "performance_limits": {
            "single_project_limit": 50000,
            "enable_cap": False,  # 不启用上限
            "single_contract_cap": 50000
        },

        # 禁用节节高奖励
        "tiered_rewards": {
            "min_contracts": 0,  # 无门槛
            "tiers": []  # 空奖励列表
        },

        # 空奖励映射
        "awards_mapping": {},

        # 禁用自引单奖励
        "self_referral_rewards": {
            "enable": False
        },

        # 奖励计算策略：仅播报模式
        "reward_calculation_strategy": {
            "type": "announcement_only",  # 新增策略类型
            "rules": {
                "default": {
                    "enable_tiered_rewards": False,
                    "stats_source": "platform_only"
                }
            }
        },

        # 通知配置：仅播报模式
        "notification_config": {
            "template_type": "announcement_only",  # 消息模板类型
            "enable_award_notification": False,  # 禁用个人奖励通知
            "show_order_type": False,  # 不显示工单类型
            "show_dual_track_stats": False,  # 不显示双轨统计
            "show_reward_progress": False,  # 不显示奖励进度
            "closing_message": "继续加油，再接再厉！"  # 固定结束语
        },

        # 数据处理配置
        "processing_config": {
            "process_platform_only": True,  # 仅处理平台单
            "enable_historical_contracts": False  # 不处理历史合同
        },

        # 徽章配置
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },
}

# 归档文件夹
ARCHIVE_DIR = 'archive'

# 业务数据源服务器配置
# 默认切换为北京签约播报新源，可通过环境变量 METABASE_URL 覆盖
METABASE_URL = os.getenv('METABASE_URL', 'http://112.126.77.6:3000')
METABASE_SESSION = METABASE_URL + '/api/session/'

# 获取数据 账号密码（从环境变量读取，必须配置）
METABASE_USERNAME = os.getenv('METABASE_USERNAME')
METABASE_PASSWORD = os.getenv('METABASE_PASSWORD')

# 验证必需的环境变量
if not METABASE_USERNAME:
    raise ValueError("METABASE_USERNAME 环境变量未设置，请在 .env 文件中配置")
if not METABASE_PASSWORD:
    raise ValueError("METABASE_PASSWORD 环境变量未设置，请在 .env 文件中配置")

RUN_JOBS_SERIALLY_SCHEDULE = 3 # 每3分钟执行一次

# 任务调度器检查间隔（秒）
TASK_CHECK_INTERVAL = 10

# 北京地区
# 默认 webhook（兼容旧代码），建议新代码使用通道化路由函数
WEBHOOK_URL_DEFAULT = os.getenv(
    'WECOM_WEBHOOK_DEFAULT',
    'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4fbae71d-8d83-479f-a2db-7690eeb37a5c'
)
WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT = os.getenv(
    'WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT',
    WEBHOOK_URL_DEFAULT
)
WECOM_WEBHOOK_PENDING_ORDERS_DEFAULT = os.getenv(
    'WECOM_WEBHOOK_PENDING_ORDERS_DEFAULT',
    WEBHOOK_URL_DEFAULT
)
WECOM_WEBHOOK_PENDING_ORDERS_FORCE_URL = os.getenv(
    'WECOM_WEBHOOK_PENDING_ORDERS_FORCE_URL',
    ''
).strip()
PHONE_NUMBER = os.getenv('CONTACT_PHONE_NUMBER')

# 验证必需的环境变量
if not WEBHOOK_URL_DEFAULT:
    raise ValueError("WECOM_WEBHOOK_DEFAULT 环境变量未设置，请在 .env 文件中配置")
if not PHONE_NUMBER:
    raise ValueError("CONTACT_PHONE_NUMBER 环境变量未设置，请在 .env 文件中配置")

# 第七个任务，待预约工单提醒
API_URL_PENDING_ORDERS_REMINDER = os.getenv(
    "API_URL_PENDING_ORDERS_REMINDER",
    METABASE_URL + "/api/card/1712/query"
)
STATUS_FILENAME_PENDING_ORDERS = './state/pending_orders_reminder_status.json'

## 上海地区，2025年10月活动
API_URL_SH_OCT = METABASE_URL + "/api/card/1884/query"

# 销售激励活动 JOB signing_and_sales_incentive_oct_shanghai
TEMP_CONTRACT_DATA_FILE_SH_OCT = 'state/ContractData-SH-Oct.csv'
PERFORMANCE_DATA_FILENAME_SH_OCT = 'state/PerformanceData-SH-Oct.csv'
STATUS_FILENAME_SH_OCT = 'state/send_status_shanghai_oct.json'

## 上海地区，2025年11月活动
API_URL_SH_NOV = METABASE_URL + "/api/card/1884/query"

# 销售激励活动 JOB signing_and_sales_incentive_nov_shanghai
TEMP_CONTRACT_DATA_FILE_SH_NOV = 'state/ContractData-SH-Nov.csv'
PERFORMANCE_DATA_FILENAME_SH_NOV = 'state/PerformanceData-SH-Nov.csv'
STATUS_FILENAME_SH_NOV = 'state/send_status_shanghai_nov.json'

## 上海地区，2025年12月活动（仅播报模式，API沿用11月）
API_URL_SH_DEC = METABASE_URL + "/api/card/1884/query"



# 销售激励活动 奖金池计算比例
BONUS_POOL_RATIO = 0.002  # 默认为0.2%,可根据需要调整

# 注意：业绩金额上限配置和是否启用业绩金额上限已移至文件顶部

## 北京地区，2025年10月活动
API_URL_BJ_OCT = METABASE_URL + "/api/card/1883/query"

# 北京销售激励活动 JOB signing_and_sales_incentive_oct_beijing
TEMP_CONTRACT_DATA_FILE_BJ_OCT = 'state/ContractData-BJ-Oct.csv'
PERFORMANCE_DATA_FILENAME_BJ_OCT = 'state/PerformanceData-BJ-Oct.csv'
STATUS_FILENAME_BJ_OCT = 'state/send_status_bj_oct.json'

## 北京地区，签约播报（新常驻任务，无月份限制）
API_URL_BJ_SIGN_BROADCAST = os.getenv(
    "API_URL_BJ_SIGN_BROADCAST",
    METABASE_URL + "/question/2003"
)

## 北京地区，2025年11月活动
API_URL_BJ_NOV = METABASE_URL + "/api/card/1864/query"

# 北京销售激励活动 JOB signing_and_sales_incentive_nov_beijing_v2
TEMP_CONTRACT_DATA_FILE_BJ_NOV = 'state/ContractData-BJ-Nov.csv'
PERFORMANCE_DATA_FILENAME_BJ_NOV = 'state/PerformanceData-BJ-Nov.csv'
STATUS_FILENAME_BJ_NOV = 'state/send_status_bj_nov.json'

## 北京地区，2025年12月活动（规则与11月一致，API沿用11月）
API_URL_BJ_DEC = METABASE_URL + "/api/card/1864/query"


# 销售激励活动 奖金池计算比例
BONUS_POOL_RATIO_BJ_FEB = 0.002  # 默认为0.2%,可根据需要调整

# 单个项目合同金额上限
SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB = 50000  # 单个项目合同金额上限
# 业绩金额上限配置
PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000  # 单个合同计入业绩金额上限
# 是否启用业绩金额上限
ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB = True

# 昨日指定服务时效规范执行情况日报 JOB generate_daily_service_report
API_URL_DAILY_SERVICE_REPORT = METABASE_URL + "/api/card/1514/query"
TEMP_DAILY_SERVICE_REPORT_FILE = 'state/daily_service_report_record.csv'
DAILY_SERVICE_REPORT_RECORD_FILE = 'state/daily_service_report_record.json'
# SLA违规记录文件路径
SLA_VIOLATIONS_RECORDS_FILE = './state/sla_violations.json'
# SLA监控配置
SLA_CONFIG = {
    "FORCE_MONDAY": False,  # 测试时设为 True，正式环境设为 False
}

# 服务商webhook映射（待预约工单提醒专用）
PENDING_ORDER_ORG_WEBHOOKS = {}
_pending_order_org_overrides_env = os.getenv("WECOM_WEBHOOK_PENDING_ORDERS_ORG_MAP", "").strip()
if _pending_order_org_overrides_env:
    try:
        loaded_map = json.loads(_pending_order_org_overrides_env)
        if not isinstance(loaded_map, dict):
            raise ValueError("WECOM_WEBHOOK_PENDING_ORDERS_ORG_MAP 必须是 JSON object")
        PENDING_ORDER_ORG_WEBHOOKS.update(loaded_map)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"WECOM_WEBHOOK_PENDING_ORDERS_ORG_MAP 配置非法: {exc}")

# 兼容旧代码
ORG_WEBHOOKS = PENDING_ORDER_ORG_WEBHOOKS

##------ 徽章功能 ------##
# 是否启用徽章，2025年4月新增
ENABLE_BADGE_MANAGEMENT = True

# 精英管家徽章配置
ELITE_BADGE_EMOJI = "\U0001F396"  # 奖章
ELITE_BADGE_NAME = f"【{ELITE_BADGE_EMOJI}精英管家】"
# 精英管家列表，2025年4月份增加的逻辑，精英管家是技术工程师的一个头衔
ELITE_HOUSEKEEPER = ["余金凤"]  # 可以根据需要添加更多管家

# 新锐管家徽章配置，2025年5月新增
RISING_STAR_BADGE_EMOJI = "\U0001F195"  # 新
RISING_STAR_BADGE_NAME = f"【{RISING_STAR_BADGE_EMOJI}新锐管家】"
RISING_STAR_HOUSEKEEPER = [
    "陈信丞", "姜东博", "蒋永辉", "张立明", "赵禾泽", "马俊杰", "孔凡沛", "梁庆龙", 
    "夏朋飞", "张争光", "吴光辉", "李震", "于邦亮", "乔文祥", "李英杰", "郑鑫", 
    "李忠", "余豪帅", "李国旗", "张朋坡", "林旭东", "谷京虎", "熊华祥", "李洁", 
    "刘国顺", "贺亮", "王帅", "李炜坤", "芦鹏飞", "王昊宇", "王勇", "李淑燕", 
    "张凯旋", "石迎丰", "苏彦奇", "蔡宏程", "余丽红", "孙坤展", "崔梦岩", "高芊", 
    "时森林", "赵芳德", "王菲", "龚晨凯", "王朝辉", "张广辉", "张立", "吴文全", 
    "黄佳鑫", "秦博文", "翁庭峰", "刘文强", "平树伟", "王巍", "户郭红", "刘铭", 
    "曹铁伟", "曹洪伟", "李高伟", "姜东升", "韩军华", "马保歌", "曹振锋", "李会强", 
    "黄永辉", "薛敏娃"
]
