import json

import mysql.connector
from mysql.connector.errors import IntegrityError


with open(".secrets.json", "r") as f:
    SECRETS = json.loads(f.read())


def _get_connection():
    """
    Get a connection and cursor to the newsletter database.

    Returns
    -------
    conn
        The connection to the database
    cursor
        The cursor in the database
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="atp45",
        password=SECRETS["DB_PASS"],
        database="atp45/newsletter"
    )
    cursor = conn.cursor()

    return conn, cursor


def get_newsletters() -> list:
    """
    Get all the current newsletters.

    Returns
    -------
    Results : list
        A list of tuples (id, title, pass_hash) for each newsletter.
    """
    conn, cursor = _get_connection()

    query = "SELECT * FROM newsletters;"
    result = []
    try:
        cursor.execute(query)
        result = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return result


def create_newsletter(title: str, pass_hash: bytes) -> bool:
    """
    Create a new newsletter entry

    Parameters
    ----------
    title : str
        The title of the newsletter
    pass_hash : bytes
        The hash of the newsletter passcode

    Returns
    -------
    success : bool
        Whether the newsletter was created successfully
    """
    conn, cursor = _get_connection()

    query = "INSERT INTO newsletters (title, passcode) VALUES (%s, %s);"
    values = (title, pass_hash)
    success = True
    try:
        cursor.execute(query, values)
        conn.commit()
    except IntegrityError:
        success = False
    finally:
        cursor.close()
        conn.close()

    return success
