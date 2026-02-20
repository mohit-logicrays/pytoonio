"""
ToonIO Constants Module.

Defines all constant values used across the ToonIO library including
delimiters, indent sizes, and TOON format literals.
"""

from enum import Enum


class Delimiter(Enum):
    """Supported delimiter types for TOON tabular format.

    Attributes:
        COMMA: Comma-separated values (default).
        TAB: Tab-separated values.
        PIPE: Pipe-separated values.
    """

    COMMA = "comma"
    TAB = "tab"
    PIPE = "pipe"


class IndentSize(Enum):
    """Supported indentation sizes for TOON output.

    Attributes:
        TWO: 2-space indentation (default).
        FOUR: 4-space indentation.
    """

    TWO = 2
    FOUR = 4


# --- Delimiter Character Mapping ---

DELIMITER_CHARS: dict[Delimiter, str] = {
    Delimiter.COMMA: ", ",
    Delimiter.TAB: "\t",
    Delimiter.PIPE: " | ",
}

# Bare delimiter chars used in list annotations: key[N]{h1,h2}: and data rows
BARE_DELIMITER_CHARS: dict[Delimiter, str] = {
    Delimiter.COMMA: ",",
    Delimiter.TAB: "\t",
    Delimiter.PIPE: "|",
}


# --- Default Configuration ---

DEFAULT_INDENT: int = IndentSize.TWO.value
DEFAULT_DELIMITER: Delimiter = Delimiter.COMMA

# --- TOON Format Literals ---

TOON_NULL: str = "null"
TOON_TRUE: str = "true"
TOON_FALSE: str = "false"

# --- Valid Delimiter String Aliases ---

DELIMITER_ALIASES: dict[str, Delimiter] = {
    "comma": Delimiter.COMMA,
    ",": Delimiter.COMMA,
    "tab": Delimiter.TAB,
    "\t": Delimiter.TAB,
    "pipe": Delimiter.PIPE,
    "|": Delimiter.PIPE,
}

# --- Valid Indent Sizes ---

VALID_INDENT_SIZES: set[int] = {indent.value for indent in IndentSize}
