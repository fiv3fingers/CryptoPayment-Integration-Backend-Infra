from enum import Enum


class RoutingServiceType(Enum):
    OTHER = "OTHER"
    CHANGENOW = "CHANGENOW"
    CCTP = "CCTP"
    DIRECT_TRANSFER = "DIRECT_TRANSFER"


class PayOrderStatus(Enum):
    PENDING = "PENDING"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PayOrderMode(Enum):
    SALE = "SALE"
    DEPOSIT = "DEPOSIT"
