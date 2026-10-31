import logging

import httpx
from fastapi import HTTPException, status

from schemas.catalog_schema import CatalogItem

logger = logging.getLogger(__name__)

ITEM_PATH = "/internal/items/{item_id}"


class CatalogService:
    """Looks up orderable menu items in restaurant-service."""

    def __init__(self, client: httpx.Client):
        self.client = client

    def get_item(self, item_id: int) -> CatalogItem:
        path = ITEM_PATH.format(item_id=item_id)
        try:
            response = self.client.get(path)
        except httpx.HTTPError:
            logger.exception("Could not reach restaurant-service")
            raise self._catalog_unavailable_error()

        if response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
        if response.is_error:
            logger.error("restaurant-service returned %s for %s", response.status_code, path)
            raise self._catalog_unavailable_error()

        try:
            return CatalogItem.model_validate(response.json())
        except ValueError:
            logger.exception("Unexpected response from restaurant-service %s", path)
            raise self._catalog_unavailable_error()

    @staticmethod
    def _catalog_unavailable_error() -> HTTPException:
        return HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Menu is temporarily unavailable"
        )
