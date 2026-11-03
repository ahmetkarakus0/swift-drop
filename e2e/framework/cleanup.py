import logging

from framework.db import Database
from framework.restaurant_locations import RestaurantLocations

logger = logging.getLogger("e2e.cleanup")


def find_test_user_ids(user_db: Database, prefix: str) -> list[str]:
    rows = user_db.fetch_all("SELECT id FROM users WHERE starts_with(email, :prefix)", prefix=prefix)
    return [str(row["id"]) for row in rows]


def find_test_restaurant_ids(restaurant_db: Database, prefix: str) -> list[str]:
    rows = restaurant_db.fetch_all(
        "SELECT id FROM restaurants WHERE starts_with(name, :prefix)", prefix=prefix
    )
    return [str(row["id"]) for row in rows]


def cleanup_user_db(user_db: Database, prefix: str) -> None:
    """Profiles, addresses and merchants cascade from users."""
    users = user_db.execute("DELETE FROM users WHERE starts_with(email, :prefix)", prefix=prefix)
    logger.info("[user_db] cleanup removed %s users", users)


def cleanup_restaurant_db(restaurant_db: Database, prefix: str) -> None:
    """Categories and items cascade from restaurants; the later deletes catch test rows under other parents."""
    counts = {
        table: restaurant_db.execute(f"DELETE FROM {table} WHERE starts_with(name, :prefix)", prefix=prefix)
        for table in ("restaurants", "categories", "items")
    }
    logger.info("[restaurant_db] cleanup removed %s", counts)


def cleanup_restaurant_locations(restaurant_locations: RestaurantLocations, restaurant_ids: list[str]) -> None:
    removed = restaurant_locations.remove(restaurant_ids)
    logger.info("[redis] cleanup removed %s restaurant locations", removed)


def cleanup_order_db(order_db: Database, user_ids: list[str]) -> None:
    """order_db has no prefixed columns, so baskets and orders are matched by the test users' ids.
    Basket and order items cascade."""
    if not user_ids:
        return
    counts = {
        table: order_db.execute(f"DELETE FROM {table} WHERE user_id::text = ANY(:ids)", ids=user_ids)
        for table in ("baskets", "orders")
    }
    logger.info("[order_db] cleanup removed %s", counts)


def cleanup_test_data(
    user_db: Database,
    restaurant_db: Database,
    order_db: Database,
    restaurant_locations: RestaurantLocations,
    prefix: str,
) -> None:
    """Connects to each database separately and deletes every row created with the test prefix.
    order_db is cleaned first because its rows are found through the test users, and restaurant
    locations before restaurant_db because they are found through the test restaurants."""
    cleanup_order_db(order_db, find_test_user_ids(user_db, prefix))
    cleanup_user_db(user_db, prefix)
    cleanup_restaurant_locations(restaurant_locations, find_test_restaurant_ids(restaurant_db, prefix))
    cleanup_restaurant_db(restaurant_db, prefix)
