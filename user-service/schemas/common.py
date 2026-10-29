import re
from typing import Annotated, Any

from pydantic import BeforeValidator, Field, StringConstraints

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _strip_phone_separators(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"[\s\-()]", "", value)
    return value


Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, max_length=255, pattern=EMAIL_PATTERN),
]
NormalizedEmail = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True)]

PhoneNumber = Annotated[
    str,
    # Constraints must precede BeforeValidator to appear in the OpenAPI schema;
    # BeforeValidator still runs first.
    StringConstraints(pattern=r"^\+?[0-9]{10,15}$"),
    BeforeValidator(_strip_phone_separators),
    Field(examples=["+10000000000"]),
]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
PostalCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
