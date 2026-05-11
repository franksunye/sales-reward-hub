#!/usr/bin/env python3
"""Run one scheduled task once (for GitHub Actions/cron)."""

import argparse
import logging

from modules.log_config import setup_logging
from main import run_contract_completion_smartsheet_task
from main import run_beijing_performance_broadcast_task
from main import run_beijing_sign_broadcast_task
from main import run_crew_settlement_finance_ledger_smartsheet_task
from main import run_daily_service_report_task
from main import run_material_replenishment_smartsheet_task
from main import run_pending_orders_reminder_task
from main import run_payment_records_smartsheet_task
from main import run_project_settlement_smartsheet_task


def main():
    parser = argparse.ArgumentParser(description="Run one scheduled task once and exit.")
    parser.add_argument(
        "--task",
        choices=[
            "beijing-sign-broadcast",
            "beijing-performance-broadcast",
            "pending-orders-reminder",
            "project-settlement-smartsheet",
            "contract-completion-smartsheet",
            "payment-records-smartsheet",
            "crew-settlement-finance-ledger-smartsheet",
            "material-replenishment-smartsheet",
            "daily-service-report",
        ],
        required=True,
        help="Task selector.",
    )
    args = parser.parse_args()

    setup_logging()
    logging.info("Running scheduled task: %s", args.task)

    if args.task == "beijing-sign-broadcast":
        run_beijing_sign_broadcast_task()
    elif args.task == "beijing-performance-broadcast":
        run_beijing_performance_broadcast_task()
    elif args.task == "daily-service-report":
        run_daily_service_report_task()
    elif args.task == "contract-completion-smartsheet":
        run_contract_completion_smartsheet_task()
    elif args.task == "payment-records-smartsheet":
        run_payment_records_smartsheet_task()
    elif args.task == "crew-settlement-finance-ledger-smartsheet":
        run_crew_settlement_finance_ledger_smartsheet_task()
    elif args.task == "material-replenishment-smartsheet":
        run_material_replenishment_smartsheet_task()
    elif args.task == "project-settlement-smartsheet":
        run_project_settlement_smartsheet_task()
    else:
        run_pending_orders_reminder_task()

    logging.info("Scheduled task completed: %s", args.task)


if __name__ == "__main__":
    main()
