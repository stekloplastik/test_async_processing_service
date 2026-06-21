class DomainException(Exception):
    """Base domain exception"""

    pass


class IdempotencyConflictException(DomainException):
    """Raised when an idempotency key is reused with a different request payload"""

    pass


class PaymentNotFoundException(DomainException):
    """Raised when a requested payment does not exist"""

    pass
