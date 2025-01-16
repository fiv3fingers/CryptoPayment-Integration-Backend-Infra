from enum import Enum

class RoutingServiceType(int, Enum):
    OTHER = 0
    CHANGENOW = 1
    CCTP = 3
    DIRECT_TRANSFER = 4

class PayOrderStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    AWAITING_PAYMENT = "awaiting_payment"
    FAILED = "failed"

class PayOrderMode(Enum):
    SALE = "sale"
    DEPOSIT = "deposit"



