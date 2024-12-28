from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    FIXED = "fixed" # Payment amounts are fixed
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"

class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"

class OrderType(str, Enum):
    SALE = "sale", # product or item sale
    CHOOSE_AMOUNT = "choose_amount", # let the user specify the amount to pay, e.g. donation or when depositing into a wallet

class RoutingServiceType(int, Enum):
    OTHER = 0
    CHANGENOW = 1
    UNISWAP = 2


