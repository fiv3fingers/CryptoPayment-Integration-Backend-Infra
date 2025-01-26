from enum import Enum


class RoutingServiceType(str, Enum):
    OTHER = "OTHER"
    CHANGENOW = "CHANGENOW"
    CCTP = "CCTP"
    DIRECT_TRANSFER = "DIRECT_TRANSFER"


class PayOrderStatus(str, Enum):
    PENDING = "PENDING"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PayOrderMode(str, Enum):
    SALE = "SALE"
    DEPOSIT = "DEPOSIT"
