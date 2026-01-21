"""Custom exceptions for devflow."""


class DevflowError(Exception):
    """Base exception for devflow errors."""

    pass


class ConfigError(DevflowError):
    """Configuration-related errors."""

    pass


class MigrationError(DevflowError):
    """Migration-related errors."""

    pass


class ProviderError(DevflowError):
    """External provider errors."""

    pass


class LockError(DevflowError):
    """Distributed lock errors."""

    pass


class AuthenticationError(DevflowError):
    """Authentication/authorization errors."""

    pass
