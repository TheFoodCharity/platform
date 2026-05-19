class VerificationError(Exception):
    """Base class for verification code errors."""


class VerificationExpired(VerificationError):
    """The code exists but its TTL has passed."""


class VerificationLocked(VerificationError):
    """All attempts have been exhausted; the code is no longer usable."""


class VerificationInvalid(VerificationError):
    """No active code exists for this user, or the supplied code is wrong."""
