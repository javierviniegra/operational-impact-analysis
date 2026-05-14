from dotenv import load_dotenv
import os

load_dotenv()


def _db_config(prefix: str) -> dict:
    return {
        "host": os.getenv(f"{prefix}_DB_HOST"),
        "port": int(os.getenv(f"{prefix}_DB_PORT", 3306)),
        "user": os.getenv(f"{prefix}_DB_USER"),
        "password": os.getenv(f"{prefix}_DB_PASSWORD"),
        "database": os.getenv(f"{prefix}_DB_NAME"),
    }


WANSOFT_DB_CONFIG = _db_config("WANSOFT")
ZENPUT_DB_CONFIG = _db_config("ZENPUT")