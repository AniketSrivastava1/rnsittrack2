class DevReadyError(Exception):
    """Base category for all DevReady CLI errors."""
    pass

class DaemonError(DevReadyError):
    """Communication issues with the Architect daemon."""
    pass

class DaemonNotRunningError(DaemonError):
    """Daemon is not reachable locally."""
    def __init__(self, message="Cannot connect to DevReady daemon. Start it with: devready daemon start"):
        super().__init__(message)

class DaemonTimeoutError(DaemonError):
    """Request to daemon timed out."""
    pass

class DaemonResponseError(DaemonError):
    """Daemon returned an error status code."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Daemon returned {status_code}: {message}")

class ConfigError(DevReadyError):
    """Configuration related issues."""
    pass

class ValidationError(DevReadyError):
    """Data validation issues."""
    pass
