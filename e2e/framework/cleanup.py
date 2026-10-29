import logging

from framework.db import Database

logger = logging.getLogger("e2e.cleanup")


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


def cleanup_test_data(user_db: Database, restaurant_db: Database, prefix: str) -> None:
    """Connects to each database separately and deletes every row created with the test prefix."""
    cleanup_user_db(user_db, prefix)
    cleanup_restaurant_db(restaurant_db, prefix)
