# config.py
import os
from dotenv import load_dotenv

# 鍔犺浇鐜鍙橀噺
load_dotenv()

# 涓婃捣鐨勭壒娈婇厤缃€夐」锛堝凡寮冪敤锛岃浣跨敤 REWARD_CONFIGS 涓殑閰嶇疆锛?
# @deprecated: 浠ヤ笅閰嶇疆宸茶閫氱敤鍖栭厤缃浛鎹紝浠呬繚鐣欑敤浜庡吋瀹规€?
PERFORMANCE_AMOUNT_CAP = 40000  # 鍗曚釜鍚堝悓璁″叆涓氱哗閲戦涓婇檺 - 宸插純鐢?
ENABLE_PERFORMANCE_AMOUNT_CAP = False  # 鏄惁鍚敤涓氱哗閲戦涓婇檺 - 宸插純鐢?


## 鍖椾含鐨勯€氱敤閰嶇疆閫夐」-杩愯惀缇ゅ悕绉颁互鍙婅繍钀ユ墽琛屼汉

WECOM_GROUP_NAME_BJ = '锛堝寳浜級淇摼鏈嶅姟杩愯惀'
CAMPAIGN_CONTACT_BJ = '鐜嬬埥'

## 涓婃捣鐨勯€氱敤閰嶇疆閫夐」-杩愯惀缇ゅ悕绉颁互鍙婅繍钀ユ墽琛屼汉
WECOM_GROUP_NAME_SH = '锛堜笂娴凤級杩愯惀缇?
CAMPAIGN_CONTACT_SH = '婊℃旦娴?


# 閫氱敤濂栧姳閰嶇疆
REWARD_CONFIGS = {
    # 鍖椾含2025骞?鏈堟椿鍔ㄩ厤缃?
    "BJ-2025-09": {
        "lucky_number": "5",  # 鍩轰簬涓汉鍚堝悓椤哄簭鐨勫€嶆暟
        "lucky_number_mode": "personal_sequence",  # 涓汉椤哄簭妯″紡
        "lucky_number_sequence_type": "personal",  # 骞歌繍鏁板瓧浣跨敤鐨勫簭鍙风被鍨嬶細personal锛堜釜浜哄簭鍙凤級鎴?global锛堝叏灞€搴忓彿锛?
        "lucky_rewards": {
            "base": {"name": "鎺ュソ杩?, "threshold": 0},
            "high": {"name": "鎺ュソ杩?, "threshold": 999999999}  # 缁熶竴濂栧姳锛屼笉鍖哄垎閲戦
        },
        "performance_limits": {
            "single_project_limit": 50000,  # 璋冩暣涓?涓?
            "enable_cap": True,
            "single_contract_cap": 50000
        },
        "tiered_rewards": {
            "min_contracts": 10,  # 鎻愬崌鑷?0涓悎鍚?
            "tiers": [
                {"name": "杈炬爣濂?, "threshold": 80000},
                {"name": "浼樼濂?, "threshold": 180000},
                {"name": "绮捐嫳濂?, "threshold": 280000}
            ]
        },
        "awards_mapping": {
            "鎺ュソ杩?: "58",  # 缁熶竴58鍏?
            "杈炬爣濂?: "400",  # 缈诲€?
            "浼樼濂?: "800",  # 缈诲€?
            "绮捐嫳濂?: "1600"  # 缈诲€?
        },
        # 濂栧姳璁＄畻绛栫暐閰嶇疆
        "reward_calculation_strategy": {
            "type": "single_track",  # 鍗曡建婵€鍔?
            "rules": {
                "default": {
                    "enable_tiered_rewards": True,
                    "stats_source": "total"  # 浣跨敤鎬荤粺璁℃暟鎹?
                }
            }
        },
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },
    # 鍖椾含2025骞?0鏈堟椿鍔ㄩ厤缃?
    "BJ-2025-10": {
        "lucky_number": "5",  # 鍩轰簬涓汉鈥滃钩鍙板崟鈥濆悎鍚岄『搴忕殑鍊嶆暟
        "lucky_number_mode": "personal_sequence",  # 涓汉鍚堝悓椤哄簭妯″紡
        "lucky_number_sequence_type": "platform_only",  # 骞歌繍鏁板瓧浠呭熀浜庡钩鍙板崟搴忓彿
        "lucky_rewards": {
            "base": {"name": "鎺ュソ杩?, "threshold": 0},
            "high": {"name": "鎺ュソ杩?, "threshold": 999999999}  # 缁熶竴濂栧姳锛屼笉鍖哄垎閲戦
        },
        "performance_limits": {
            "single_project_limit": 50000,  # 骞冲彴鍗曞伐鍗曚笂闄?涓?
            "enable_cap": True,
            "single_contract_cap": 50000,  # 骞冲彴鍗曞悎鍚屼笂闄?涓?
            # 鏂板锛氬樊寮傚寲閲戦涓婇檺閰嶇疆
            "self_referral_contract_cap": 200000,  # 鑷紩鍗曞悎鍚屼笂闄?0涓?
            "self_referral_project_limit": 200000   # 鑷紩鍗曞伐鍗曚笂闄?0涓?
        },
        "tiered_rewards": {
            "min_contracts": 10,  # 10涓悎鍚岋紝鈥滃钩鍙板崟鈥濅互鍙娾€滆嚜寮曞崟鈥濓紝鍗虫墍鏈夊悎鍚岀疮璁?
            "tiers": [
                {"name": "杈炬爣濂?, "threshold": 100000},
                {"name": "浼樼濂?, "threshold": 180000},
                {"name": "绮捐嫳濂?, "threshold": 300000},
                {"name": "鍗撹秺濂?, "threshold": 460000}
            ]
        },
        "awards_mapping": {
            "鎺ュソ杩?: "58",  
            "杈炬爣濂?: "200",  
            "浼樼濂?: "400",  
            "绮捐嫳濂?: "800",
            "鍗撹秺濂?: "1600"
        },
        # 鑷紩鍗曞鍔遍厤缃紙鍖椾含10鏈堜笉鍚敤锛?
        "self_referral_rewards": {
            "enable": False  # 鍖椾含10鏈堜笉闇€瑕佽嚜寮曞崟鐙珛濂栧姳
        },
        # 濂栧姳璁＄畻绛栫暐閰嶇疆
        "reward_calculation_strategy": {
            "type": "dual_track",  # 鍚敤鍙岃建缁熻
            "rules": {
                "default": {
                    "enable_tiered_rewards": True,
                    "stats_source": "total"  # 鑺傝妭楂樹娇鐢ㄦ€荤粺璁℃暟鎹?
                }
            }
        },
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },
    # 涓婃捣2025骞?鏈堟椿鍔ㄩ厤缃?
    "SH-2025-09": {
        "lucky_number": "",  # 绂佺敤骞歌繍濂?
        "lucky_number_sequence_type": "global",  # 濡傛灉鍚敤骞歌繍濂栵紝涓婃捣鏃╂湡浣跨敤鍏ㄥ眬搴忓彿
        "performance_limits": {
            "enable_cap": False,  # 涓婃捣涓嶅惎鐢ㄤ笟缁╀笂闄?
            "single_contract_cap": 40000
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 骞冲彴鍗曢渶瑕?涓悎鍚?
            "tiers": [
                {"name": "鍩虹濂?, "threshold": 40000},
                {"name": "杈炬爣濂?, "threshold": 60000},
                {"name": "浼樼濂?, "threshold": 80000},
                {"name": "绮捐嫳濂?, "threshold": 120000},
                {"name": "鍗撹秺濂?, "threshold": 160000}
            ]
        },
        "awards_mapping": {
            # 骞冲彴鍗曞鍔憋紙澶嶇敤涓婃捣4鏈堥厤缃級
            "鍩虹濂?: "200",
            "杈炬爣濂?: "300",
            "浼樼濂?: "400",
            "绮捐嫳濂?: "800",
            "鍗撹秺濂?: "1200",
            # 鑷紩鍗曞鍔憋紙鏂板锛?
            "绾㈠寘": "50"
        },
        # 鏂板锛氳嚜寮曞崟濂栧姳閰嶇疆
        "self_referral_rewards": {
            "enable": True,  # 鍚敤鑷紩鍗曞鍔?
            "reward_type": "鑷紩鍗?,
            "reward_name": "绾㈠寘",
            "deduplication_field": "projectAddress"  # 鍘婚噸瀛楁
            # 娉ㄦ剰锛氬鍔遍噾棰濈粺涓€鍦╝wards_mapping涓畾涔夛紝閬垮厤閲嶅閰嶇疆
        },
        # 濂栧姳璁＄畻绛栫暐閰嶇疆
        "reward_calculation_strategy": {
            "type": "dual_track",  # 鍙岃建婵€鍔?
            "rules": {
                "platform": {
                    "enable_tiered_rewards": True,
                    "stats_source": "platform_only"  # 浣跨敤骞冲彴鍗曠粺璁℃暟鎹?
                },
                "self_referral": {
                    "enable_tiered_rewards": False,  # 鑷紩鍗曚笉鍙備笌鑺傝妭楂樺鍔?
                    "stats_source": "self_referral_only"  # 浣跨敤鑷紩鍗曠粺璁℃暟鎹?
                }
            }
        }
    },
    # 涓婃捣2025骞?0鏈堟椿鍔ㄩ厤缃?
    "SH-2025-10": {
        "lucky_number": "",  # 绂佺敤骞歌繍濂?
        "lucky_number_sequence_type": "global",  # 濡傛灉鍚敤骞歌繍濂栵紝涓婃捣鏃╂湡浣跨敤鍏ㄥ眬搴忓彿
        "performance_limits": {
            "enable_cap": False,  # 涓婃捣涓嶅惎鐢ㄤ笟缁╀笂闄?
            "single_contract_cap": 40000
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 骞冲彴鍗曢渶瑕?涓悎鍚?
            "tiers": [
                {"name": "鍩虹濂?, "threshold": 40000},
                {"name": "杈炬爣濂?, "threshold": 60000},
                {"name": "浼樼濂?, "threshold": 80000},
                {"name": "绮捐嫳濂?, "threshold": 120000},
                {"name": "鍗撹秺濂?, "threshold": 160000}
            ]
        },
        "awards_mapping": {
            # 骞冲彴鍗曞鍔憋紙澶嶇敤涓婃捣4鏈堥厤缃級
            "鍩虹濂?: "200",
            "杈炬爣濂?: "300",
            "浼樼濂?: "400",
            "绮捐嫳濂?: "800",
            "鍗撹秺濂?: "1200",
            # 鑷紩鍗曞鍔憋紙鏂板锛?
            # "绾㈠寘": "50"
        },
        # 鏂板锛氳嚜寮曞崟濂栧姳閰嶇疆
        "self_referral_rewards": {
            "enable": False,  # 鍚敤鑷紩鍗曞鍔?
            "reward_type": "鑷紩鍗?,
            "reward_name": "绾㈠寘",
            "deduplication_field": "projectAddress"  # 鍘婚噸瀛楁
            # 娉ㄦ剰锛氬鍔遍噾棰濈粺涓€鍦╝wards_mapping涓畾涔夛紝閬垮厤閲嶅閰嶇疆
        },
        # 濂栧姳璁＄畻绛栫暐閰嶇疆
        "reward_calculation_strategy": {
            "type": "single_track",  # 鍗曡建婵€鍔憋細浠呭钩鍙板崟
            "rules": {
                "platform": {
                    "enable_tiered_rewards": True,
                    "stats_source": "platform_only"  # 浣跨敤骞冲彴鍗曠粺璁℃暟鎹?
                },
                "self_referral": {
                    "enable_tiered_rewards": False,  # 鑷紩鍗曚笉鍙備笌鑺傝妭楂樺鍔?
                    "stats_source": "self_referral_only"  # 浣跨敤鑷紩鍗曠粺璁℃暟鎹?
                }
            }
        }
    },
    # 涓婃捣2025骞?1鏈堟椿鍔ㄩ厤缃紙瑙勫垯涓?0鏈堝畬鍏ㄤ竴鑷达級
    "SH-2025-11": {
        "lucky_number": "",  # 绂佺敤骞歌繍濂?
        "lucky_number_sequence_type": "global",  # 濡傛灉鍚敤骞歌繍濂栵紝涓婃捣鏃╂湡浣跨敤鍏ㄥ眬搴忓彿
        "performance_limits": {
            "enable_cap": False,  # 涓婃捣涓嶅惎鐢ㄤ笟缁╀笂闄?
            "single_contract_cap": 40000
        },
        "tiered_rewards": {
            "min_contracts": 5,  # 骞冲彴鍗曢渶瑕?涓悎鍚?
            "tiers": [
                {"name": "鍩虹濂?, "threshold": 40000},
                {"name": "杈炬爣濂?, "threshold": 60000},
                {"name": "浼樼濂?, "threshold": 80000},
                {"name": "绮捐嫳濂?, "threshold": 120000},
                {"name": "鍗撹秺濂?, "threshold": 160000}
            ]
        },
        "awards_mapping": {
            # 骞冲彴鍗曞鍔憋紙澶嶇敤涓婃捣4鏈堥厤缃級
            "鍩虹濂?: "200",
            "杈炬爣濂?: "300",
            "浼樼濂?: "400",
            "绮捐嫳濂?: "800",
            "鍗撹秺濂?: "1200",
            # 鑷紩鍗曞鍔憋紙鏂板锛?
            # "绾㈠寘": "50"
        },
        # 鏂板锛氳嚜寮曞崟濂栧姳閰嶇疆
        "self_referral_rewards": {
            "enable": False,  # 鍚敤鑷紩鍗曞鍔?
            "reward_type": "鑷紩鍗?,
            "reward_name": "绾㈠寘",
            "deduplication_field": "projectAddress"  # 鍘婚噸瀛楁
            # 娉ㄦ剰锛氬鍔遍噾棰濈粺涓€鍦╝wards_mapping涓畾涔夛紝閬垮厤閲嶅閰嶇疆
        },
        # 濂栧姳璁＄畻绛栫暐閰嶇疆
        "reward_calculation_strategy": {
            "type": "single_track",  # 鍗曡建婵€鍔憋細浠呭钩鍙板崟
            "rules": {
                "platform": {
                    "enable_tiered_rewards": True,
                    "stats_source": "platform_only"  # 浣跨敤骞冲彴鍗曠粺璁℃暟鎹?
                },
                "self_referral": {
                    "enable_tiered_rewards": False,  # 鑷紩鍗曚笉鍙備笌鑺傝妭楂樺鍔?
                    "stats_source": "self_referral_only"  # 浣跨敤鑷紩鍗曠粺璁℃暟鎹?
                }
            }
        }
    },
    # 鍖椾含2025骞?1鏈堟椿鍔ㄩ厤缃?
    "BJ-2025-11": {
        # 绂佺敤骞歌繍鏁板瓧
        "lucky_number": "",
        "lucky_number_mode": "personal_sequence",
        "lucky_number_sequence_type": "personal",

        # 绂佺敤骞歌繍鏁板瓧濂栧姳
        "lucky_rewards": {
            "base": {"name": "", "threshold": 0},
            "high": {"name": "", "threshold": 999999999}
        },

        # 鎬ц兘闄愬埗閰嶇疆锛堝彲閫夛紝鍥犱负鏃犲鍔辫绠楋級
        "performance_limits": {
            "single_project_limit": 50000,
            "enable_cap": False,  # 涓嶅惎鐢ㄤ笂闄?
            "single_contract_cap": 50000
        },

        # 绂佺敤鑺傝妭楂樺鍔?
        "tiered_rewards": {
            "min_contracts": 0,  # 鏃犻棬妲?
            "tiers": []  # 绌哄鍔卞垪琛?
        },

        # 绌哄鍔辨槧灏?
        "awards_mapping": {},

        # 绂佺敤鑷紩鍗曞鍔?
        "self_referral_rewards": {
            "enable": False
        },

        # 濂栧姳璁＄畻绛栫暐锛氫粎鎾姤妯″紡
        "reward_calculation_strategy": {
            "type": "announcement_only",  # 鏂板绛栫暐绫诲瀷
            "rules": {
                "default": {
                    "enable_tiered_rewards": False,
                    "stats_source": "platform_only"
                }
            }
        },

        # 閫氱煡閰嶇疆锛氫粎鎾姤妯″紡
        "notification_config": {
            "template_type": "announcement_only",  # 娑堟伅妯℃澘绫诲瀷
            "enable_award_notification": False,  # 绂佺敤涓汉濂栧姳閫氱煡
            "show_order_type": False,  # 涓嶆樉绀哄伐鍗曠被鍨?
            "show_dual_track_stats": False,  # 涓嶆樉绀哄弻杞ㄧ粺璁?
            "show_reward_progress": False,  # 涓嶆樉绀哄鍔辫繘搴?
            "closing_message": "缁х画鍔犳补锛屽啀鎺ュ啀鍘夛紒"  # 鍥哄畾缁撴潫璇?
        },

        # 鏁版嵁澶勭悊閰嶇疆
        "processing_config": {
            "process_platform_only": True,  # 浠呭鐞嗗钩鍙板崟
            "enable_historical_contracts": False  # 涓嶅鐞嗗巻鍙插悎鍚?
        },

        # 寰界珷閰嶇疆
        "badge_config": {
            "enable_elite_badge": False,
            "enable_rising_star_badge": False
        }
    },
}

# 褰掓。鏂囦欢澶?
ARCHIVE_DIR = 'archive'

# 涓氬姟鏁版嵁婧愭湇鍔″櫒閰嶇疆
METABASE_URL = 'http://metabase.fsgo365.cn:3000'
METABASE_SESSION = METABASE_URL + '/api/session/'

# 鑾峰彇鏁版嵁 璐﹀彿瀵嗙爜锛堜粠鐜鍙橀噺璇诲彇锛屽繀椤婚厤缃級
METABASE_USERNAME = os.getenv('METABASE_USERNAME')
METABASE_PASSWORD = os.getenv('METABASE_PASSWORD')

# 楠岃瘉蹇呴渶鐨勭幆澧冨彉閲?
if not METABASE_USERNAME:
    raise ValueError("METABASE_USERNAME 鐜鍙橀噺鏈缃紝璇峰湪 .env 鏂囦欢涓厤缃?)
if not METABASE_PASSWORD:
    raise ValueError("METABASE_PASSWORD 鐜鍙橀噺鏈缃紝璇峰湪 .env 鏂囦欢涓厤缃?)

RUN_JOBS_SERIALLY_SCHEDULE = 3 # 姣?鍒嗛挓鎵ц涓€娆?

# 浠诲姟璋冨害鍣ㄦ鏌ラ棿闅旓紙绉掞級
TASK_CHECK_INTERVAL = 10

# 鍖椾含鍦板尯
# 鍖椾含杩愯惀浼佸井缇ゆ満鍣ㄤ汉閫氳鍦板潃锛堜粠鐜鍙橀噺璇诲彇锛屽繀椤婚厤缃級
WEBHOOK_URL_DEFAULT = os.getenv('WECOM_WEBHOOK_DEFAULT')
PHONE_NUMBER = os.getenv('CONTACT_PHONE_NUMBER')

# 楠岃瘉蹇呴渶鐨勭幆澧冨彉閲?
if not WEBHOOK_URL_DEFAULT:
    raise ValueError("WECOM_WEBHOOK_DEFAULT 鐜鍙橀噺鏈缃紝璇峰湪 .env 鏂囦欢涓厤缃?)
if not PHONE_NUMBER:
    raise ValueError("CONTACT_PHONE_NUMBER 鐜鍙橀噺鏈缃紝璇峰湪 .env 鏂囦欢涓厤缃?)

# 绗竷涓换鍔★紝寰呴绾﹀伐鍗曟彁閱?
API_URL_PENDING_ORDERS_REMINDER = METABASE_URL + "/api/card/1712/query"
STATUS_FILENAME_PENDING_ORDERS = './state/pending_orders_reminder_status.json'

## 涓婃捣鍦板尯锛?025骞?0鏈堟椿鍔?
API_URL_SH_OCT = METABASE_URL + "/api/card/1884/query"

# 閿€鍞縺鍔辨椿鍔?JOB signing_and_sales_incentive_oct_shanghai
TEMP_CONTRACT_DATA_FILE_SH_OCT = 'state/ContractData-SH-Oct.csv'
PERFORMANCE_DATA_FILENAME_SH_OCT = 'state/PerformanceData-SH-Oct.csv'
STATUS_FILENAME_SH_OCT = 'state/send_status_shanghai_oct.json'

## 涓婃捣鍦板尯锛?025骞?1鏈堟椿鍔?
API_URL_SH_NOV = METABASE_URL + "/api/card/1884/query"

# 閿€鍞縺鍔辨椿鍔?JOB signing_and_sales_incentive_nov_shanghai
TEMP_CONTRACT_DATA_FILE_SH_NOV = 'state/ContractData-SH-Nov.csv'
PERFORMANCE_DATA_FILENAME_SH_NOV = 'state/PerformanceData-SH-Nov.csv'
STATUS_FILENAME_SH_NOV = 'state/send_status_shanghai_nov.json'



# 閿€鍞縺鍔辨椿鍔?濂栭噾姹犺绠楁瘮渚?
BONUS_POOL_RATIO = 0.002  # 榛樿涓?.2%,鍙牴鎹渶瑕佽皟鏁?

# 娉ㄦ剰锛氫笟缁╅噾棰濅笂闄愰厤缃拰鏄惁鍚敤涓氱哗閲戦涓婇檺宸茬Щ鑷虫枃浠堕《閮?

## 鍖椾含鍦板尯锛?025骞?0鏈堟椿鍔?
API_URL_BJ_OCT = METABASE_URL + "/api/card/1883/query"

# 鍖椾含閿€鍞縺鍔辨椿鍔?JOB signing_and_sales_incentive_oct_beijing
TEMP_CONTRACT_DATA_FILE_BJ_OCT = 'state/ContractData-BJ-Oct.csv'
PERFORMANCE_DATA_FILENAME_BJ_OCT = 'state/PerformanceData-BJ-Oct.csv'
STATUS_FILENAME_BJ_OCT = 'state/send_status_bj_oct.json'

## 鍖椾含鍦板尯锛?025骞?1鏈堟椿鍔?
API_URL_BJ_NOV = METABASE_URL + "/api/card/1864/query"

# 鍖椾含閿€鍞縺鍔辨椿鍔?JOB signing_and_sales_incentive_nov_beijing_v2
TEMP_CONTRACT_DATA_FILE_BJ_NOV = 'state/ContractData-BJ-Nov.csv'
PERFORMANCE_DATA_FILENAME_BJ_NOV = 'state/PerformanceData-BJ-Nov.csv'
STATUS_FILENAME_BJ_NOV = 'state/send_status_bj_nov.json'


# 閿€鍞縺鍔辨椿鍔?濂栭噾姹犺绠楁瘮渚?
BONUS_POOL_RATIO_BJ_FEB = 0.002  # 榛樿涓?.2%,鍙牴鎹渶瑕佽皟鏁?

# 鍗曚釜椤圭洰鍚堝悓閲戦涓婇檺
SINGLE_PROJECT_CONTRACT_AMOUNT_LIMIT_BJ_FEB = 50000  # 鍗曚釜椤圭洰鍚堝悓閲戦涓婇檺
# 涓氱哗閲戦涓婇檺閰嶇疆
PERFORMANCE_AMOUNT_CAP_BJ_FEB = 50000  # 鍗曚釜鍚堝悓璁″叆涓氱哗閲戦涓婇檺
# 鏄惁鍚敤涓氱哗閲戦涓婇檺
ENABLE_PERFORMANCE_AMOUNT_CAP_BJ_FEB = True

# 鏄ㄦ棩鎸囧畾鏈嶅姟鏃舵晥瑙勮寖鎵ц鎯呭喌鏃ユ姤 JOB generate_daily_service_report
API_URL_DAILY_SERVICE_REPORT = METABASE_URL + "/api/card/1514/query"
TEMP_DAILY_SERVICE_REPORT_FILE = 'state/daily_service_report_record.csv'
DAILY_SERVICE_REPORT_RECORD_FILE = 'state/daily_service_report_record.json'
# SLA杩濊璁板綍鏂囦欢璺緞
SLA_VIOLATIONS_RECORDS_FILE = './state/sla_violations.json'
# SLA鐩戞帶閰嶇疆
SLA_CONFIG = {
    "FORCE_MONDAY": False,  # 娴嬭瘯鏃惰涓?True锛屾寮忕幆澧冭涓?False
}

# 鏈嶅姟鍟唚ebhook鏄犲皠锛堝緟棰勭害宸ュ崟鎻愰啋涓撶敤锛?
ORG_WEBHOOKS = {
    # 鏈嶅姟鍟嗕笓灞瀢ebhook閰嶇疆
    "鍖椾含缁忓父浜伐绋嬫妧鏈湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=44b3d3db-009e-4477-bdbb-88832b232155",
    "铏归€旀帶鑲★紙鍖椾含锛夋湁闄愯矗浠诲叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0cd6ba04-719d-4817-a8a5-4034c2e4781d",
    "鍖椾含椤哄缓涓哄畨宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b81aae61-820c-4123-8ed7-0287540be82d",
    "鍖椾含涔濋紟寤哄伐绉戞妧宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c6f36d8e-6b06-4614-9869-a095168de0dc",
    "鍖椾含涔呯浘瀹忕洓寤虹瓚宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=2ea71190-53b6-46ff-ad83-9d249d9d67e3",
    "涓夋渤甯備腑璞槻姘村伐绋嬫湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8a3c889a-1109-477c-8bd8-bdb3ca8599ce",
    "鍖椾含鎭掓鼎涓囬€氶槻姘村伐绋嬫湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=77214359-c515-4463-a8d8-a80d691437d1",
    "鍖椾含娴╁湥绉戞妧鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=23f3fac2-5390-45e8-b54b-619b025e335a",
    "鍖椾含鍗庡绮剧▼闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=d6958739-31d9-4cfb-9ef0-238ff003061d",
    "鍖椾含鑵鹃鐟炴寤虹瓚瑁呴グ鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=d60d7366-e66d-4202-88d3-bd87f43f7cab",
    "浜戝皻铏癸紙鍖椾含锛夊缓绛戝伐绋嬫湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=1f383a88-107a-4760-a455-f00297203675",
    "鍖椾含鍗氳繙鎭掓嘲瑁呴グ瑁呬慨鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=a7696a0a-a392-412a-a5b6-ed34486ea6a0",
    "鍖椾含鍗庡涵瑁呴グ宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9f0621da-2e4c-484b-b1f9-b65bcdd48cee",
    "鍖椾含寰峰澹板晢璐告湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4ea9922b-1333-4e34-9fca-62cec5408c73",
    "鍖椾含铏硅薄闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b61d1232-ddfd-4cc4-81ed-f8f6b9cdc7b9",
    "鍖椾含寤哄悰鐩涘崕鎶€鏈湇鍔℃湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b72b9e1d-1c82-4be6-8b58-239b2f941570",
    "鍖椾含鎬€鍐涢槻姘村伐绋嬫湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=09a26589-f1b2-4d1c-b27d-01703ec32820",
    "鍖椾含鐩涜揪娲洦闃叉按鎶€鏈湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=32aedd2b-ec5a-4fd8-a1bf-8a1e1a16ed6c",
    "鍖椾含鍚夋熆寤虹瓚宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=91a6546d-fbb8-43db-9650-4d2efcc4b78a",
    # 涓婃捣鍦板尯
    "涓婃捣鍥藉潶瑁呮舰璁捐宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4b25fb8e-b08f-4260-9f5c-eff87766ea2a",
    "涓婃捣鏄婄偒寤虹瓚鏉愭枡鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=daaf7c55-639c-4366-9d47-0909a4d8cf59",
    "涓婃捣鏄嗘槺闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c05e83b9-1f4a-4603-a8bc-2de74f42eaf8",
    "涓婃捣濡欐墠寤虹瓚闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=68489387-abc8-4f49-9804-d0c8b08e8288",
    "涓婃捣鑽冪拞瀹炰笟鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9a4e331e-44ef-4356-a5b6-40108e4ccd53",
    "涓婃捣閿愬父瀹炰笟鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=957f398b-686b-4c42-b02a-51f91fac0fff",
    "涓婃捣鑻ラ噾姹ら槻姘村伐绋嬫湁闄愬叕鍙?: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=71152288-4a43-4ac7-a393-49f3636b4391",
    "涓婃捣浣嶅崼闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4703b5a8-994a-401b-a06c-b04a86bed01a",
    "涓婃捣闆佹寤虹瓚宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b74d3962-2399-423c-9491-b21dff0fe1a7",
    "涓婃捣鍝蹭綉闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=84eb80c4-def8-40c8-82e3-842fd0b01e7d",
    "涓婃捣娑涜姭闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9a4e331e-44ef-4356-a5b6-40108e4ccd53",
    "涓婃捣浜戦闃叉按宸ョ▼鏈夐檺鍏徃": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c05e83b9-1f4a-4603-a8bc-2de74f42eaf8",
    # 鍏朵粬鏈厤缃笓灞瀢ebhook鐨勬湇鍔″晢灏嗕娇鐢ㄩ粯璁ebhook
}

##------ 寰界珷鍔熻兘 ------##
# 鏄惁鍚敤寰界珷锛?025骞?鏈堟柊澧?
ENABLE_BADGE_MANAGEMENT = True

# 绮捐嫳绠″寰界珷閰嶇疆
ELITE_BADGE_EMOJI = "\U0001F396"  # 濂栫珷
ELITE_BADGE_NAME = f"銆恵ELITE_BADGE_EMOJI}绮捐嫳绠″銆?
# 绮捐嫳绠″鍒楄〃锛?025骞?鏈堜唤澧炲姞鐨勯€昏緫锛岀簿鑻辩瀹舵槸鎶€鏈伐绋嬪笀鐨勪竴涓ご琛?
ELITE_HOUSEKEEPER = ["浣欓噾鍑?]  # 鍙互鏍规嵁闇€瑕佹坊鍔犳洿澶氱瀹?

# 鏂伴攼绠″寰界珷閰嶇疆锛?025骞?鏈堟柊澧?
RISING_STAR_BADGE_EMOJI = "\U0001F195"  # 鏂?
RISING_STAR_BADGE_NAME = f"銆恵RISING_STAR_BADGE_EMOJI}鏂伴攼绠″銆?
RISING_STAR_HOUSEKEEPER = [
    "闄堜俊涓?, "濮滀笢鍗?, "钂嬫案杈?, "寮犵珛鏄?, "璧电娉?, "椹繆鏉?, "瀛斿嚒娌?, "姊佸簡榫?, 
    "澶忔湅椋?, "寮犱簤鍏?, "鍚村厜杈?, "鏉庨渿", "浜庨偊浜?, "涔旀枃绁?, "鏉庤嫳鏉?, "閮戦懌", 
    "鏉庡繝", "浣欒豹甯?, "鏉庡浗鏃?, "寮犳湅鍧?, "鏋楁棴涓?, "璋蜂含铏?, "鐔婂崕绁?, "鏉庢磥", 
    "鍒樺浗椤?, "璐轰寒", "鐜嬪竻", "鏉庣倻鍧?, "鑺﹂箯椋?, "鐜嬫槉瀹?, "鐜嬪媷", "鏉庢窇鐕?, 
    "寮犲嚡鏃?, "鐭宠繋涓?, "鑻忓溅濂?, "钄″畯绋?, "浣欎附绾?, "瀛欏潳灞?, "宕旀ⅵ宀?, "楂樿妸", 
    "鏃舵．鏋?, "璧佃姵寰?, "鐜嬭彶", "榫氭櫒鍑?, "鐜嬫湞杈?, "寮犲箍杈?, "寮犵珛", "鍚存枃鍏?, 
    "榛勪匠閼?, "绉﹀崥鏂?, "缈佸涵宄?, "鍒樻枃寮?, "骞虫爲浼?, "鐜嬪穽", "鎴烽儹绾?, "鍒橀摥", 
    "鏇归搧浼?, "鏇规椽浼?, "鏉庨珮浼?, "濮滀笢鍗?, "闊╁啗鍗?, "椹繚姝?, "鏇规尟閿?, "鏉庝細寮?, 
    "榛勬案杈?, "钖涙晱濞?
]
