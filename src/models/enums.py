from enum import Enum

class RoutingServiceType(Enum):
    OTHER = "OTHER"
    CHANGENOW = "CHANGENOW"
    CCTP = "CCTP"
    DIRECT_TRANSFER = "DIRECT_TRANSFER"

class PayOrderStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    FAILED = "FAILED"
    RECEIVED = "RECEIVED"

class PayOrderMode(Enum):
    SALE = "SALE"
    DEPOSIT = "DEPOSIT"



