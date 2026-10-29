import re
from decimal import Decimal
from typing import Annotated, Any, ClassVar

from pydantic import BaseModel, BeforeValidator, Field, StringConstraints, model_validator


def _strip_phone_separators(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"[\s\-()]", "", value)
    return value


PhoneNumber = Annotated[
    str,
    # Constraints must precede BeforeValidator to appear in the OpenAPI schema;
    # BeforeValidator still runs first.
    StringConstraints(pattern=r"^\+?[0-9]{10,15}$"),
    BeforeValidator(_strip_phone_separators),
    Field(examples=["+10000000000"]),
]

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
PostalCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
Price = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2, examples=["129.90"])]


class PatchModel(BaseModel):
    """Partial update body. Omitted fields are left unchanged; explicit nulls are only
    accepted for fields listed in `nullable_fields`."""

    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _reject_nulls(self):
        for name in self.model_fields_set:
            if getattr(self, name) is None and name not in self.nullable_fields:
                raise ValueError(f"{name} cannot be null")
        return self

    def changes(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)
