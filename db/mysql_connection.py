import mysql.connector
from mysql.connector import Error
from config.settings import WANSOFT_DB_CONFIG, ZENPUT_DB_CONFIG


def get_wansoft_connection():
    """
    Returns a MySQL connection to the Wansoft database.
    """
    try:
        return mysql.connector.connect(**WANSOFT_DB_CONFIG)
    except Error as e:
        raise RuntimeError(f"Wansoft DB connection failed: {e}")


def get_zenput_connection():
    """
    Returns a MySQL connection to the Zenput database.
    """
    try:
        return mysql.connector.connect(**ZENPUT_DB_CONFIG)
    except Error as e:
        raise RuntimeError(f"Zenput DB connection failed: {e}")