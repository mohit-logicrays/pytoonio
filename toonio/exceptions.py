"""
ToonIO Exceptions Module.

Defines the custom exception hierarchy for the ToonIO library.
All exceptions inherit from the base ToonIOError.
"""


class ToonIOError(Exception):
    """Base exception for all ToonIO errors.

    Attributes:
        message: Human-readable error description.
    """

    def __init__(self, message: str = "An error occurred in ToonIO") -> None:
        self.message: str = message
        super().__init__(self.message)


class ToonEncodeError(ToonIOError):
    """Raised when encoding data to TOON format fails.

    Example:
        Unsupported data types or circular references.
    """

    def __init__(self, message: str = "Failed to encode data to TOON format") -> None:
        super().__init__(message)


class ToonDecodeError(ToonIOError):
    """Raised when decoding/parsing a TOON string fails.

    Example:
        Malformed TOON input, unexpected indentation, or invalid literals.
    """

    def __init__(self, message: str = "Failed to decode TOON data") -> None:
        super().__init__(message)


class ToonInvalidDelimiterError(ToonIOError):
    """Raised when an unsupported delimiter is specified.

    Attributes:
        delimiter: The invalid delimiter value that was provided.
    """

    def __init__(self, delimiter: str) -> None:
        self.delimiter: str = delimiter
        super().__init__(
            f"Invalid delimiter: '{delimiter}'. "
            f"Supported values: 'comma', 'tab', 'pipe'."
        )


class ToonInvalidIndentError(ToonIOError):
    """Raised when an unsupported indent size is specified.

    Attributes:
        indent: The invalid indent value that was provided.
    """

    def __init__(self, indent: int) -> None:
        self.indent: int = indent
        super().__init__(
            f"Invalid indent size: {indent}. "
            f"Supported values: 2, 4."
        )
