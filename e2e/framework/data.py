"""Valid request payloads. Pass keyword overrides to build invalid or specific variants."""

import uuid
from typing import Any

from framework.config import get_settings


def unique_suffix() -> str:
    return uuid.uuid4().hex[:12]


def unique_name(label: str) -> str:
    """Cleanup only finds rows whose name starts with the test prefix, so build names with this."""
    return f"{get_settings().TEST_DATA_PREFIX} {label} {unique_suffix()}"


def unique_email(label: str = "user") -> str:
    settings = get_settings()
    return f"{settings.TEST_DATA_PREFIX}.{label}.{unique_suffix()}@{settings.TEST_EMAIL_DOMAIN}"


def address_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "title": "Home",
        "phone_number": "+905550000000",
        "country": "Turkey",
        "city": "Istanbul",
        "district": "Kadikoy",
        "neighborhood": "Moda",
        "postal_code": "34710",
        "address_line1": "E2E Street No: 1",
        "address_line2": None,
        **overrides,
    }


def customer_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "email": unique_email("customer"),
        "password": get_settings().DEFAULT_PASSWORD,
        "first_name": "E2E",
        "last_name": "Customer",
        "phone_number": "+905550000001",
        "address": address_payload(),
        **overrides,
    }


def courier_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "email": unique_email("courier"),
        "password": get_settings().DEFAULT_PASSWORD,
        "first_name": "E2E",
        "last_name": "Courier",
        "phone_number": "+905550000002",
        "vehicle_type": "motorcycle",
        "vehicle_plate": "34 E2E 01",
        "address": address_payload(),
        **overrides,
    }


def merchant_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "email": unique_email("merchant"),
        "password": get_settings().DEFAULT_PASSWORD,
        "business_name": unique_name("Business"),
        "phone_number": "+905550000003",
        "tax_number": "1234567890",
        "tax_office": "Kadikoy",
        "iban": "GB82WEST12345698765432",
        "address": address_payload(title="Store"),
        **overrides,
    }


def restaurant_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "name": unique_name("Restaurant"),
        "phone_number": "+905550000004",
        "country": "Turkey",
        "city": "Istanbul",
        "district": "Kadikoy",
        "neighborhood": "Moda",
        "postal_code": "34710",
        "address_line1": "E2E Street No: 2",
        "address_line2": None,
        "is_open": False,
        **overrides,
    }


def category_payload(**overrides: Any) -> dict[str, Any]:
    return {"name": unique_name("Category"), "is_active": True, **overrides}


def item_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "name": unique_name("Item"),
        "description": "Created by the e2e suite",
        "price": "99.90",
        "is_active": True,
        **overrides,
    }
