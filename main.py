import schedule
import time
import traceback
import logging
import threading
from modules.log_config import setup_logging
from jobs import *
from modules.config import RUN_JOBS_SERIALLY_SCHEDULE
import datetime
import task_scheduler # 引入任务调度模块

# 设置日志
setup_logging()

# 定义一个函数来串行执行任务
def run_jobs_serially():
    current_month = datetime.datetime.now().month
    print("Current month is:", current_month)

    if current_month == 8:
        # 上海8月份
        try:
            signing_and_sales_incentive_aug_shanghai()
            time.sleep(5)
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_aug_shanghai: {e}")
            logging.error(traceback.format_exc())

        # 北京8月份
        try:
            signing_and_sales_incentive_aug_beijing()
            time.sleep(5)
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_aug_beijing: {e}")
            logging.error(traceback.format_exc())

    elif current_month == 7:
        # 上海7月份
        try:
            signing_and_sales_incentive_july_shanghai()
            time.sleep(5)
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_july_shanghai: {e}")
            logging.error(traceback.format_exc())
        # 北京7月份
        try:
            signing_and_sales_incentive_july_beijing()
            time.sleep(5)
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_july_beijing: {e}")
            logging.error(traceback.format_exc())
    else:
        logging.info("No tasks scheduled for this month.")

# 定义一个函数来执行日报任务
def daily_service_report_task():
    try:
        generate_daily_service_report()  # 调用生成日报的函数
        logging.info("Daily service report generated successfully.")
    except Exception as e:
        logging.error(f"An error occurred while generating daily service report: {e}")
        logging.error(traceback.format_exc())

# 定义一个函数来执行待预约工单提醒任务
def pending_orders_reminder_task():
    try:
        send_pending_orders_reminder()  # 调用待预约工单提醒函数
        logging.info("Pending orders reminder sent successfully.")
    except Exception as e:
        logging.error(f"An error occurred while sending pending orders reminder: {e}")
        logging.error(traceback.format_exc())

# 使用schedule库调度串行执行任务的函数，定时执行一次，在config中配置
schedule.every(RUN_JOBS_SERIALLY_SCHEDULE).minutes.do(run_jobs_serially)

# 使用schedule库调度日报任务，每天11点执行
schedule.every().day.at("11:00").do(daily_service_report_task)

# 使用schedule库调度待预约工单提醒任务，每天9点执行
schedule.every().day.at("09:00").do(pending_orders_reminder_task)

if __name__ == '__main__':
    logging.info('Program started')

    # 启动任务调度器
    scheduler_thread = threading.Thread(target=task_scheduler.start)
    scheduler_thread.daemon = True  # 设置为守护线程

    # 启动任务调度器线程，注释后可单独测试任务且不会触发GUI操作
    scheduler_thread.start()

    # 单独测试任务
    # generate_daily_service_report()
    # check_technician_status()
    # signing_and_sales_incentive_aug_beijing()
    # signing_and_sales_incentive_aug_shanghai()
    # signing_and_sales_incentive_july_beijing()
    # signing_and_sales_incentive_july_shanghai()
    # pending_orders_reminder_task()

    # 启动调度循环
    while True:
        try:
            schedule.run_pending()  # 这里也在运行schedule的任务
            time.sleep(1)
        except Exception as e:
            logging.error(f"Job failed with exception: {e}")
            logging.error(traceback.format_exc())
            time.sleep(5)