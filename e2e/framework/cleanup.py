import logging

from framework.db import Database

logger = logging.getLogger("e2e.cleanup")


def cleanup_test_data(user_db: Database, restaurant_db: Database, email_domain: str) -> None:
    """Removes everything created by the suite, identified by the test email domain.

    Restaurants live in another database without a foreign key to merchants, so they
    are removed first using the merchant ids. Categories and items cascade from
    restaurants; profiles and addresses cascade from users.
    """
    pattern = f"%@{email_domain}"
    merchant_ids = [
        row["id"]
        for row in user_db.fetch_all(
            """
            SELECT m.id FROM merchants m
            JOIN users u ON u.id = m.user_id
            WHERE u.email LIKE :pattern
            """,
            pattern=pattern,
        )
    ]

    restaurants = 0
    if merchant_ids:
        restaurants = restaurant_db.execute(
            "DELETE FROM restaurants WHERE merchant_id = ANY(:ids)", ids=merchant_ids
        )
    users = user_db.execute("DELETE FROM users WHERE email LIKE :pattern", pattern=pattern)
    logger.info("Cleanup removed %s users and %s restaurants", users, restaurants)
