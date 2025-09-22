import logging
import time
import threading
from modules.message_sender import send_wechat_message, send_wecom_message
from modules.log_config import setup_logging
from task_manager import get_pending_tasks, update_task

setup_logging()  # 设置日志

task_lock = threading.Lock()
is_task_running = False  # 标志位，表示任务是否正在运行

def execute_task(task):
    global is_task_running
    with task_lock:  # 确保在执行任务时获得锁
        is_task_running = True  # 设置任务正在运行
        logging.info(f"Executing task ID: {task['id']} of type: {task['task_type']}")  # 记录任务执行
        try:
            if task['task_type'] == 'send_wechat_message':
                send_wechat_message(task['recipient'], task['message'])
            elif task['task_type'] == 'send_wecom_message':
                send_wecom_message(task['recipient'], task['message'])
            update_task(task['id'], 'completed')  # 使用 update_task 更新任务状态
            logging.info(f"Task ID: {task['id']} completed successfully.")  # 记录任务完成
        except Exception as e:
            logging.error(f"Error executing task ID: {task['id']}: {e}")  # 记录错误
        finally:
            is_task_running = False  # 任务完成，重置标志位

def check_tasks():
    global is_task_running
    logging.info("Checking for pending tasks...")  # Log the start of task checking
    if not is_task_running:  # Only check tasks if no task is running
        tasks = get_pending_tasks()  # 调用任务管理中的函数
        for task in tasks:
            execute_task(task)
    logging.info("Task check completed.")  # Log the end of task checking

def start():
    from modules.config import TASK_CHECK_INTERVAL
    logging.info("Task scheduler started.")

    while True:
        try:
            check_tasks()  # 直接调用检查任务
            time.sleep(TASK_CHECK_INTERVAL)  # 使用配置的间隔时间
        except Exception as e:
            logging.error(f"Error in task scheduler: {e}")
            time.sleep(5)
