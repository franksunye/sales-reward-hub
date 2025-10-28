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

# 导入新架构下的10月和11月job函数
from modules.core.beijing_jobs import signing_and_sales_incentive_oct_beijing, signing_and_sales_incentive_nov_beijing
from modules.core.shanghai_jobs import signing_and_sales_incentive_oct_shanghai

# 设置日志
setup_logging()

# 定义一个函数来串行执行任务
def run_jobs_serially():
    current_month = datetime.datetime.now().month
    print("Current month is:", current_month)

    if current_month == 9:
        # 上海9月份
        try:
            signing_and_sales_incentive_sep_shanghai()
            time.sleep(5)
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_sep_shanghai: {e}")
            logging.error(traceback.format_exc())
        # 北京9月份
        try:
            signing_and_sales_incentive_sep_beijing()
            time.sleep(5)
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_sep_beijing: {e}")
            logging.error(traceback.format_exc())

    elif current_month == 10:
        # 上海10月份（新架构）
        try:
            logging.info("开始执行上海10月销售激励任务（新架构）")
            signing_and_sales_incentive_oct_shanghai()
            time.sleep(5)
            logging.info("上海10月销售激励任务执行完成")
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_oct_shanghai: {e}")
            logging.error(traceback.format_exc())

        # 北京10月份（新架构）
        try:
            logging.info("开始执行北京10月销售激励任务（新架构）")
            signing_and_sales_incentive_oct_beijing()
            time.sleep(5)
            logging.info("北京10月销售激励任务执行完成")
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_oct_beijing: {e}")
            logging.error(traceback.format_exc())

    elif current_month == 11:
        # 北京11月份（新架构 - 仅播报模式）
        try:
            logging.info("开始执行北京11月销售激励任务（仅播报模式）")
            signing_and_sales_incentive_nov_beijing()
            time.sleep(5)
            logging.info("北京11月销售激励任务执行完成")
        except Exception as e:
            logging.error(f"An error occurred while running signing_and_sales_incentive_nov_beijing: {e}")
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

    # # 启动任务调度器线程，注释后可单独测试任务且不会触发GUI操作
    scheduler_thread.start()  # 测试期间禁用，避免发送真实消息

    # 单独测试任务
    # generate_daily_service_report()
    # signing_and_sales_incentive_sep_shanghai()  # 9月上海（旧架构）
    # signing_and_sales_incentive_sep_beijing()   # 9月北京（旧架构）
    # signing_and_sales_incentive_oct_shanghai()  # 10月上海（新架构）
    # signing_and_sales_incentive_oct_beijing()   # 10月北京（新架构）
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