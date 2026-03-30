"""企业微信 webhook 路由管理。"""

from typing import Optional

from modules.config import (
    PENDING_ORDER_ORG_WEBHOOKS,
    WECOM_WEBHOOK_PENDING_ORDERS_DEFAULT,
    WECOM_WEBHOOK_PENDING_ORDERS_FORCE_URL,
    WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT,
)


CHANNEL_SIGN_BROADCAST = "sign_broadcast"
CHANNEL_PENDING_ORDERS = "pending_orders_reminder"


def resolve_wecom_webhook(channel: str, org_name: Optional[str] = None) -> str:
    """按业务通道和服务商解析 webhook。"""
    if channel == CHANNEL_PENDING_ORDERS:
        if WECOM_WEBHOOK_PENDING_ORDERS_FORCE_URL:
            return WECOM_WEBHOOK_PENDING_ORDERS_FORCE_URL
        if org_name and org_name in PENDING_ORDER_ORG_WEBHOOKS:
            return PENDING_ORDER_ORG_WEBHOOKS[org_name]
        return WECOM_WEBHOOK_PENDING_ORDERS_DEFAULT

    if channel == CHANNEL_SIGN_BROADCAST:
        return WECOM_WEBHOOK_SIGN_BROADCAST_DEFAULT

    raise ValueError(f"Unsupported webhook channel: {channel}")
