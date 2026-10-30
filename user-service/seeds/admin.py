"""Creates the admin user from ADMIN_EMAIL / ADMIN_PASSWORD. Safe to run multiple times.

Usage: python -m seeds.admin
"""
import logging
import sys

from core.config.settings import settings
from core.database import SessionLocal
from core.security import BCRYPT_MAX_BYTES, hash_password
from models import User, UserRole
from repositories.user_repo import UserRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")
logger = logging.getLogger("seeds.admin")


def seed_admin() -> None:
    email = settings.ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD
    if not email or not password:
        logger.error("ADMIN_EMAIL and ADMIN_PASSWORD must be set")
        sys.exit(1)
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        logger.error("ADMIN_PASSWORD must be at most %d bytes", BCRYPT_MAX_BYTES)
        sys.exit(1)

    email = email.strip()
    with SessionLocal() as db:
        repo = UserRepository(db)
        if repo.get_by_email(email):
            logger.info("User %s already exists, skipping", email)
            return

        repo.create(
            User(
                email=email,
                password=hash_password(password),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
        )
        logger.info("Admin user %s created", email)


if __name__ == "__main__":
    seed_admin()
