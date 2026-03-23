import logging
import schedule
import time
import traceback

from modules.log_config import setup_logging
from modules.config import RUN_JOBS_SERIALLY_SCHEDULE
from modules.core.beijing_jobs import signing_broadcast_beijing


setup_logging()


def run_beijing_sign_broadcast_task():
    """北京签约播报常驻任务（无月份限制）。"""
    try:
        logging.info("开始执行北京签约播报任务")
        signing_broadcast_beijing()
        logging.info("北京签约播报任务执行完成")
    except Exception as e:
        logging.error(f"执行北京签约播报任务失败: {e}")
        logging.error(traceback.format_exc())


# 仅保留北京签约播报任务
schedule.every(RUN_JOBS_SERIALLY_SCHEDULE).minutes.do(run_beijing_sign_broadcast_task)


if __name__ == "__main__":
    logging.info("Program started (Beijing signing broadcast only)")

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Scheduler loop exception: {e}")
            logging.error(traceback.format_exc())
            time.sleep(5)
