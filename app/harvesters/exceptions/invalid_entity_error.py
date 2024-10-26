class InvalidEntityError(ValueError):
    """Exception raised when an invalid entity has been submitted."""

    def __init__(self, message: str) -> None:
        """Initialize the exception."""
        super().__init__(message)
