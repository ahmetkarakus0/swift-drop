import re
from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field, StringConstraints

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _strip_phone_separators(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"[\s\-()]", "", value)
    return value


def _normalize_iban(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\s", "", value).upper()
    return value


def _check_iban_checksum(value: str) -> str:
    rearranged = value[4:] + value[:4]
    if int("".join(str(int(char, 36)) for char in rearranged)) % 97 != 1:
        raise ValueError("Invalid IBAN checksum")
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

Iban = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$"),
    BeforeValidator(_normalize_iban),
    AfterValidator(_check_iban_checksum),
    Field(examples=["GB82WEST12345698765432"]),
]
TaxNumber = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9A-Za-z]{5,20}$")
]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
PostalCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
