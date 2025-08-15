import json
import traceback
from datetime import datetime

import mysql.connector
from mysql.connector.errors import Error, IntegrityError

from typing import Optional, Tuple


now = datetime.now()
LOG_FILE = "/home/atp45/logs/mysql"
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
    conn.autocommit = False
    cursor = conn.cursor()
    open(LOG_FILE, "a").write(f"[INFO: {now.isoformat()}] Connection opened\n")

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
        open(LOG_FILE, "a").write(f"[INFO: {now.isoformat()}] Connection closed\n")

    return result


def get_questions(
    newsletter_id: int,
    issue: int
) -> Tuple[list, list]:
    """
    Get the questions for the specified newsletter and issue.
    This returns both the default and the user submitted questions.

    Parameters
    ----------
    newsletter_id : int
        The newsletter foreign key
    issue : int
        The issue number

    Returns
    -------
    default : list[q_id, text, type]
        The list of default questions and their type for that newsletter and issue.
    submitted : list[q_id, creator, text]
        The list of questions created for that newsletter and issue.
    """
    conn, cursor = _get_connection()

    default_query = """
    SELECT id, text, type
    FROM questions
    WHERE newsletter_id=%s AND issue=%s AND base;
    """
    user_query = """
    SELECT id, creator, text
    FROM questions
    WHERE newsletter_id=%s AND issue=%s AND NOT base;
    """
    values = (newsletter_id, issue)

    default = []
    submitted = []
    try:
        cursor.execute(user_query, values)
        submitted = cursor.fetchall()

        cursor.execute(default_query, values)
        default = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
        open(LOG_FILE, "a").write(f"[INFO: {now.isoformat()}] Connection closed\n")

    return default, submitted


def insert_answer(
    name: str,
    responses: dict
) -> Tuple[bool, Optional[str]]:
    """
    Insert the answers for a specific user.

    Parameters
    ----------
    name : str
        The name of the user
    responses : dict[question_id, (img, answer)]
        A dictionary of responses
    """
    conn, cursor = _get_connection()

    success = True
    error_text: Optional[str] = None
    try:
        for q_id, data in responses.items():
            # Override old responses with new ones
            query = """
            INSERT INTO answers (question_id, name, img_path, text)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE img_path=%s, text=%s;
            """
            values = (
                q_id, name,
                data['img'], data['text'],
                data['img'], data['text']
            )

            cursor.execute(query, values)

        conn.commit()
    except Error as error:
        open(LOG_FILE, "a").write(f"[WARN: {now.isoformat()}] Failed to submit answers, rollback: {traceback.format_exc()}\n")
        conn.rollback()
        success = False
        error_text = error.msg
    finally:
        cursor.close()
        conn.close()
        open(LOG_FILE, "a").write(f"[INFO: {now.isoformat()}] Connection closed\n")

    return success, error_text


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
        open(LOG_FILE, "a").write(f"[WARN: {now.isoformat()}] Failed to create newsletter due to integrity error\n")
        success = False
    finally:
        cursor.close()
        conn.close()
        open(LOG_FILE, "a").write(f"[INFO: {now.isoformat()}] Connection closed\n")

    return success
