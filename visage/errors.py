class VisageAPIError(Exception):
    """Base error for all Visage API errors."""
    def __init__(self, message: str, status_code: int, request_id: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id

class VisageAuthError(VisageAPIError):
    """Raised on 401 — missing or invalid API key."""
    def __init__(self, message: str = "Invalid or missing API key", request_id: str | None = None):
        super().__init__(message, 401, request_id)

class VisageLicenseNotFoundError(VisageAPIError):
    """Raised on 404 — license key not found."""
    def __init__(self, message: str = "License key not found", request_id: str | None = None):
        super().__init__(message, 404, request_id)
