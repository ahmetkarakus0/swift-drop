from typing import Annotated

from pydantic import Field, StringConstraints

DeliveryAddress = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]
Quantity = Annotated[int, Field(ge=1, le=99)]
