__all__ = [
    "RateLimitError",
    "PayloadTooLargeError",
    "AuthenticationError",
]


class RateLimitError(AssertionError):
    pass


class PayloadTooLargeError(AssertionError):
    pass


class AuthenticationError(AssertionError):
    pass
