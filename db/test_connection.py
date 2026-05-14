from db.mysql_connection import (
    get_wansoft_connection,
    get_zenput_connection,
)


def test_wansoft():
    conn = get_wansoft_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    conn.close()
    return result


def test_zenput():
    conn = get_zenput_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    conn.close()
    return result


if __name__ == "__main__":
    print("Wansoft:", test_wansoft())
    print("Zenput:", test_zenput())
