#!/usr/bin/env python3
"""Run one scheduled task once (for GitHub Actions/cron)."""

import argparse
import logging

from modules.log_config import setup_logging
from main import run_beijing_sign_broadcast_task
from main import run_pending_orders_reminder_task


def main():
    parser = argparse.ArgumentParser(description="Run one scheduled task once and exit.")
    parser.add_argument(
        "--task",
        choices=["beijing-sign-broadcast", "pending-orders-reminder"],
        required=True,
        help="Task selector.",
    )
    args = parser.parse_args()

    setup_logging()
    logging.info("Running scheduled task: %s", args.task)

    if args.task == "beijing-sign-broadcast":
        run_beijing_sign_broadcast_task()
    else:
        run_pending_orders_reminder_task()

    logging.info("Scheduled task completed: %s", args.task)


if __name__ == "__main__":
    main()
