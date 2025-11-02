# config.py

# 上海的特殊配置选项（已弃用，请使用 REWARD_CONFIGS 中的配置）
# @deprecated: 以下配置已被通用化配置替换，仅保留用于兼容性
PERFORMANCE_AMOUNT_CAP = 40000  # 单个合同计入业绩金额上限 - 已弃用
ENABLE_PERFORMANCE_AMOUNT_CAP = False  # 是否启用业绩金额上限 - 已弃用

# 通用奖励配置
REWARD_CONFIGS = {
    # 北京2025年6月活动配置（8月复用此配置）
    "BJ-2025-06": {
        "lucky_number": "8",  # 8月活动使用幸运数字8
        "lucky_rewards": {
            "base": {"name": "接好运", "threshold": 0},
            "high": {"name": "接好运万元以上", "threshold": 10000}
        },
        "performance_limits": {
            "single_project_limit": 500000,
            "enable_cap": True,
            "single_contract_cap": 500000
        },
        "tiered_rewards": {
            "min_contracts": 6,
            "tiers": [
                {"name": "达标奖", "threshold": 80000},
                {"name": "优秀奖", "threshold": 120000},
                {"name": "精英奖", "threshold": 180000}
            ]
        },
        "awards_mapping": {
            "接好运": "36",
            "接好运万元以上": "66",
            "达标奖": "200",
            "优秀奖": "400",
            "精英奖": "600"
        }
    },
    # 北京2025年8月活动配置
    "BJ-2025-08": {
        "lucky_number": "8",
        "lucky_rewards": {
            "base": {"name": "接好运", "threshold": 0},
            "high": {"name": "接好运万元以上", "threshold": 10000}
        },
        "performance_limits": {
            "single_project_limit": 500000,
            "enable_cap": True,
            "single_contract_cap": 500000
        },
        "tiered_rewards": {
            "min_contracts": 6,
            "tiers": [
                {"name": "达标奖", "threshold": 80000},
                {"name": "优秀奖", "threshold": 120000},
                {"name": "精英奖", "threshold": 180000}
            ]
        },
        "awards_mapping": {
            "接好运": "36",
            "接好运万元以上": "66",
            "达标奖": "200",
            "优秀奖": "400",
            "精英奖": "600"
        }
    },
    # 北京2025年9月活动配置
    "BJ-2025-09": {
        "lucky_number": "5",  # 基于个人合同顺序的倍数
        "lucky_number_mode": "personal_sequence",  # 个人顺序模式
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
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },

    # 上海2025年4月活动配置
    "SH-2025-04": {
        "lucky_number": "",  # 禁用幸运奖（最简单的方案）
        "performance_limits": {
            "enable_cap": False,  # 上海不启用业绩上限，使用 total_amount
            "single_contract_cap": 40000  # 单合同上限（如果启用的话）
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 上海需要5个合同
            "tiers": [
                {"name": "基础奖", "threshold": 40000},
                {"name": "达标奖", "threshold": 60000},
                {"name": "优秀奖", "threshold": 80000},
                {"name": "精英奖", "threshold": 120000},
                {"name": "卓越奖", "threshold": 160000}
            ]
        },
        "awards_mapping": {
            "接好运": "36",
            "接好运万元以上": "66",
            "基础奖": "200",
            "达标奖": "300",
            "优秀奖": "400",
            "精英奖": "800",
            "卓越奖": "1200"
        }
    },
    # 上海2025年9月活动配置
    "SH-2025-09": {
        "lucky_number": "",  # 禁用幸运奖
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
        }
    },
}

# 归档文件夹
ARCHIVE_DIR = 'archive'

# 业务数据源服务器配置
METABASE_URL = 'http://metabase.fsgo365.cn:3000'
METABASE_SESSION = METABASE_URL + '/api/session/'

# 获取数据 账号密码
METABASE_USERNAME = '****@xlink.bj.cn'
METABASE_PASSWORD = '****'

RUN_JOBS_SERIALLY_SCHEDULE = 3 # 每3分钟执行一次

# 任务调度器检查间隔（秒）
TASK_CHECK_INTERVAL = 10

# 北京地区
# 北京运营企微群机器人通讯地址
# WEBHOOK_URL_DEFAULT = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4fbae71d-8d83-479f-a2db-7690eeb37a5c'
WEBHOOK_URL_DEFAULT = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=689cebff-3328-4150-9741-fed8b8ce4713'
PHONE_NUMBER = '15327103039'

# 第七个任务，待预约工单提醒
API_URL_PENDING_ORDERS_REMINDER = METABASE_URL + "/api/card/1712/query"
STATUS_FILENAME_PENDING_ORDERS = './state/pending_orders_reminder_status.json'

## 上海地区，2025年8月活动
API_URL_SH_AUG = METABASE_URL + "/api/card/1801/query"

# 销售激励活动 JOB signing_and_sales_incentive_aug_shanghai
TEMP_CONTRACT_DATA_FILE_SH_AUG = 'state/ContractData-SH-Aug.csv'
PERFORMANCE_DATA_FILENAME_SH_AUG = 'state/PerformanceData-SH-Aug.csv'
STATUS_FILENAME_SH_AUG = 'state/send_status_sh_aug.json'

# Pro
WECOM_GROUP_NAME_SH_AUG = '（上海）运营群'
CAMPAIGN_CONTACT_SH_AUG = '满浩浩'

## 上海地区，2025年9月活动
API_URL_SH_SEP = METABASE_URL + "/api/card/1838/query"

# 销售激励活动 JOB signing_and_sales_incentive_sep_shanghai
TEMP_CONTRACT_DATA_FILE_SH_SEP = 'state/ContractData-SH-Sep.csv'
PERFORMANCE_DATA_FILENAME_SH_SEP = 'state/PerformanceData-SH-Sep.csv'
STATUS_FILENAME_SH_SEP = 'state/send_status_shanghai_sep.json'

# # 通知配置
# WECOM_GROUP_NAME_SH_SEP = '（上海）运营群'
# CAMPAIGN_CONTACT_SH_SEP = '满浩浩'

## 上海的通用配置选项
WECOM_GROUP_NAME_SH = '（上海）运营群'
CAMPAIGN_CONTACT_SH = '满浩浩'
# 销售激励活动 奖金池计算比例
BONUS_POOL_RATIO = 0.002  # 默认为0.2%,可根据需要调整

# 注意：业绩金额上限配置和是否启用业绩金额上限已移至文件顶部

## 北京地区，2025年8月活动
API_URL_BJ_AUG = METABASE_URL + "/api/card/1800/query"

# 北京销售激励活动 JOB signing_and_sales_incentive_aug_beijing
TEMP_CONTRACT_DATA_FILE_BJ_AUG = 'state/ContractData-BJ-Aug.csv'
PERFORMANCE_DATA_FILENAME_BJ_AUG = 'state/PerformanceData-BJ-Aug.csv'
STATUS_FILENAME_BJ_AUG = 'state/send_status_bj_aug.json'

# Pro
WECOM_GROUP_NAME_BJ_AUG = '（北京）修链服务运营'
CAMPAIGN_CONTACT_BJ_AUG = '王爽'

## 北京地区，2025年9月活动
API_URL_BJ_SEP = METABASE_URL + "/api/card/1864/query"  # 新的API端点

# 北京销售激励活动 JOB signing_and_sales_incentive_sep_beijing
TEMP_CONTRACT_DATA_FILE_BJ_SEP = 'state/ContractData-BJ-Sep.csv'
PERFORMANCE_DATA_FILENAME_BJ_SEP = 'state/PerformanceData-BJ-Sep.csv'
STATUS_FILENAME_BJ_SEP = 'state/send_status_bj_sep.json'

# 通知配置
# WECOM_GROUP_NAME_BJ_SEP = '（北京）修链服务运营'
# CAMPAIGN_CONTACT_BJ_SEP = '王爽'

## 北京的通用配置选项

WECOM_GROUP_NAME_BJ = '北京运营中心系统通知群'
CAMPAIGN_CONTACT_BJ = '王爽'

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
ORG_WEBHOOKS = {
    # 服务商专属webhook配置
    "北京经常亮工程技术有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=44b3d3db-009e-4477-bdbb-88832b232155",
    "虹途控股（北京）有限责任公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0cd6ba04-719d-4817-a8a5-4034c2e4781d",
    "北京顺建为安工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b81aae61-820c-4123-8ed7-0287540be82d",
    "北京九鼎建工科技工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c6f36d8e-6b06-4614-9869-a095168de0dc",
    "北京久盾宏盛建筑工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=2ea71190-53b6-46ff-ad83-9d249d9d67e3",
    "三河市中豫防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8a3c889a-1109-477c-8bd8-bdb3ca8599ce",
    "北京恒润万通防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=77214359-c515-4463-a8d8-a80d691437d1",
    "北京浩圣科技有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=23f3fac2-5390-45e8-b54b-619b025e335a",
    "北京华夏精程防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=d6958739-31d9-4cfb-9ef0-238ff003061d",
    "北京腾飞瑞欧建筑装饰有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=d60d7366-e66d-4202-88d3-bd87f43f7cab",
    "云尚虹（北京）建筑工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=1f383a88-107a-4760-a455-f00297203675",
    "北京博远恒泰装饰装修有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=a7696a0a-a392-412a-a5b6-ed34486ea6a0",
    "北京华庭装饰工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9f0621da-2e4c-484b-b1f9-b65bcdd48cee",
    "北京德客声商贸有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4ea9922b-1333-4e34-9fca-62cec5408c73",
    "北京虹象防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b61d1232-ddfd-4cc4-81ed-f8f6b9cdc7b9",
    "北京建君盛华技术服务有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b72b9e1d-1c82-4be6-8b58-239b2f941570",
    "北京怀军防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=09a26589-f1b2-4d1c-b27d-01703ec32820",
    "北京盛达洪雨防水技术有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=32aedd2b-ec5a-4fd8-a1bf-8a1e1a16ed6c",
    # 上海地区
    "上海国坦装潢设计工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4b25fb8e-b08f-4260-9f5c-eff87766ea2a",
    "上海昊炫建筑材料有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=daaf7c55-639c-4366-9d47-0909a4d8cf59",
    "上海昆昱防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c05e83b9-1f4a-4603-a8bc-2de74f42eaf8",
    "上海妙才建筑防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=68489387-abc8-4f49-9804-d0c8b08e8288",
    "上海荃璆实业有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9a4e331e-44ef-4356-a5b6-40108e4ccd53",
    "上海锐常实业有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=957f398b-686b-4c42-b02a-51f91fac0fff",
    "上海若金汤防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=71152288-4a43-4ac7-a393-49f3636b4391",
    "上海位卫防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4703b5a8-994a-401b-a06c-b04a86bed01a",
    "上海雁棠建筑工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b74d3962-2399-423c-9491-b21dff0fe1a7",
    "上海哲佑防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=84eb80c4-def8-40c8-82e3-842fd0b01e7d",
    "上海涛芫防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9a4e331e-44ef-4356-a5b6-40108e4ccd53",
    "上海云风防水工程有限公司": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c05e83b9-1f4a-4603-a8bc-2de74f42eaf8",
    # 其他未配置专属webhook的服务商将使用默认webhook
}

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
