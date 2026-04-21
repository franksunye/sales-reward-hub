"""Test package."""

import os
import sys
import types


def _install_requests_stub() -> None:
    if "requests" in sys.modules:
        return

    requests_stub = types.ModuleType("requests")
    requests_exceptions_stub = types.ModuleType("requests.exceptions")

    class _RequestException(Exception):
        pass

    class _Timeout(_RequestException):
        pass

    requests_stub.post = lambda *args, **kwargs: None
    requests_stub.RequestException = _RequestException
    requests_exceptions_stub.Timeout = _Timeout
    sys.modules["requests"] = requests_stub
    sys.modules["requests.exceptions"] = requests_exceptions_stub


def _install_dotenv_stub() -> None:
    if "dotenv" in sys.modules:
        return

    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub


def _seed_test_env() -> None:
    defaults = {
        "CONTACT_PHONE_NUMBER": "13800000000",
        "METABASE_USERNAME": "test@example.com",
        "METABASE_PASSWORD": "test-password",
        "WECOM_WEBHOOK_DEFAULT": "https://example.com/default",
        "WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT": "https://example.com/sign-broadcast",
        "WECOM_WEBHOOK_PENDING_ORDERS_ORG_MAP": '{"北京经常亮工程技术有限公司":"https://example.com/pending-provider-a"}',
        "WECOM_PROJECT_SETTLEMENT_SMARTSHEET_WEBHOOK": "https://example.com/wedoc",
        "WECOM_CONTRACT_COMPLETION_SMARTSHEET_WEBHOOK": "https://example.com/wedoc-contract-completion",
        "WECOM_PAYMENT_RECORDS_SMARTSHEET_WEBHOOK": "https://example.com/wedoc-payment-records",
        "WECOM_CREW_SETTLEMENT_FINANCE_LEDGER_SMARTSHEET_WEBHOOK": "https://example.com/wedoc-crew-settlement-finance-ledger",
        "WECOM_MATERIAL_REPLENISHMENT_SMARTSHEET_WEBHOOK": "https://example.com/wedoc-material-replenishment",
        "DB_SOURCE": "local",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


_install_requests_stub()
_install_dotenv_stub()
_seed_test_env()
