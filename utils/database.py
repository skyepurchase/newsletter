import os
from dotenv import load_dotenv

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract
from mysql.connector.locales import errorcode
from mysql.connector.pooling import PooledMySQLConnection

from .type_hints import Response
from typing import Any, List, Optional, Tuple, Union


load_dotenv()


USER = os.getenv("USER")
DB_PASS = os.getenv("DB_PASS")
DATABASE = os.getenv("DATABASE")


def _process_insert_errors(code: int) -> str:
    if code == errorcode.ER_DUP_ENTRY:
        return "Attempted to insert entry that already exists."
    elif code == errorcode.ER_BAD_NULL_ERROR:
        return "Expected value but received null."
    elif code in [1136, 1054, errorcode.ER_DUP_FIELDNAME]:
        return "Unexpected columns or duplicated columns."
    else:
        return f"Unprocessed database error {code}."


def _get_connection() -> Tuple[
    Union[PooledMySQLConnection, MySQLConnectionAbstract],
    Union[MySQLCursorAbstract, Any],
]:
    """
    Get a connection and cursor to the newsletter database.

    Returns
    -------
    conn
        The connection to the database
    cursor
        The cursor in the database
    """
    assert USER is not None, "Failed to find database config"
    assert DB_PASS is not None, "Failed to find database config"
    assert DATABASE is not None, "Failed to find the database config"

    conn = mysql.connector.connect(
        host="localhost",
        user=USER,
        password=DB_PASS,
        database=DATABASE,
    )
    conn.autocommit = False
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


def get_questions(newsletter_id: int, issue: int) -> Tuple[list, list]:
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

    return default, submitted


def get_responses(newsletter_id: int, issue: int) -> List[Response]:
    """
    Returns
    -------
    results : list[creator, question, list[name, text, path]]
        The questions and their responses
    """
    conn, cursor = _get_connection()

    results = []

    user_q_id_query = """
    SELECT id, creator, text FROM questions
    WHERE newsletter_id=%s AND issue=%s AND NOT base;
    """

    default_q_id_query = """
    SELECT id, text FROM questions
    WHERE newsletter_id=%s AND issue=%s AND base;
    """

    response_query = """
    SELECT name, text, img_path
    FROM answers
    WHERE answers.question_id=%s
    """

    try:
        cursor.execute(user_q_id_query, (newsletter_id, issue))
        user_questions = cursor.fetchall()

        cursor.execute(default_q_id_query, (newsletter_id, issue))
        default_questions = cursor.fetchall()

        for question in user_questions:
            q_id, creator, question = question
            assert isinstance(q_id, int), (
                "Question id not integer"
            )  # This should be guaranteed

            cursor.execute(response_query, (q_id,))
            responses = cursor.fetchall()

            results.append((creator, question, responses))

        for question in default_questions:
            q_id, question = question
            assert isinstance(q_id, int), (
                "Question id not integer"
            )  # This should be guaranteed

            cursor.execute(response_query, (q_id,))
            responses = cursor.fetchall()

            results.append(("", question, responses))
    finally:
        cursor.close()
        conn.close()

    return results


def insert_answer(name: str, responses: dict) -> Tuple[bool, str]:
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
    error_text = ""
    try:
        for q_id, data in responses.items():
            # Skip duplicate entries
            # This is unsafe but avoids unauthorised data overwrite
            # It does not prevent malicious lock-out
            query = """
            INSERT IGNORE INTO answers (question_id, name, img_path, text)
            VALUES (%s, %s, %s, %s);
            """
            # ON DUPLICATE KEY UPDATE img_path=%s, text=%s;
            values = (
                q_id,
                name,
                data["img"],
                data["text"],
                # data['img'], data['text']
            )

            cursor.execute(query, values)

        conn.commit()
    except mysql.connector.IntegrityError as error:
        conn.rollback()
        success = False
        error_text = _process_insert_errors(error.errno)
    finally:
        cursor.close()
        conn.close()

    return success, error_text


def insert_question(
    newsletter_id: int,
    issue: int,
    name: str,
    question: str,
) -> Tuple[bool, str]:
    """
    Insert the question for a specific user.

    Parameters
    ----------
    newsletter_id : int
        The id of the target newsletter
    issue : int
        The newsletter issue the question belongs to
    name : str
        The name of the user
    question : str
        The question to be inserted
    """
    conn, cursor = _get_connection()

    success = True
    error_text = ""
    try:
        query = """
        INSERT INTO questions (newsletter_id, creator, text, issue)
        VALUES (%s, %s, %s, %s);
        """
        values = (newsletter_id, name, question, issue)

        cursor.execute(query, values)
        conn.commit()
    except mysql.connector.IntegrityError as error:
        conn.rollback()
        success = False
        error_text = _process_insert_errors(error.errno)
    finally:
        cursor.close()
        conn.close()

    return success, error_text


def insert_default_questions(
    newsletter_id: int, issue: int, questions: List[Tuple[str, str]]
) -> Tuple[bool, Optional[str]]:
    """
    Insert the provided text as default questions.

    Parameters
    ----------
    newsletter_id : int
        The id of the target newsletter
    issue : int
        The newsletter issue the question belongs to
    text : str
        The question text to be inserted
    form : str
        Whether the question is a text or image question
    """
    conn, cursor = _get_connection()

    success = True
    error_text = None
    try:
        query = """
        INSERT INTO questions (newsletter_id, creator, text, issue, base, type)
        VALUES (%s, %s, %s, %s, %s, %s);
        """

        for text, form in questions:
            values = (newsletter_id, "SYS", text, issue, True, form)
            cursor.execute(query, values)

        conn.commit()
    except mysql.connector.IntegrityError as error:
        conn.rollback()
        error_text = _process_insert_errors(error.errno)
        success = False
    finally:
        cursor.close()
        conn.close()

    return success, error_text


def create_newsletter(
    title: str, pass_hash: bytes, folder: str
) -> Tuple[bool, Optional[str]]:
    """
    Create a new newsletter entry

    Parameters
    ----------
    title : str
        The title of the newsletter
    pass_hash : bytes
        The hash of the newsletter passcode
    folder : str
        The folder where metadata and config is stored

    Returns
    -------
    success : bool
        Whether the newsletter was created successfully
    """
    conn, cursor = _get_connection()

    query = "INSERT INTO newsletters (title, passcode, folder) VALUES (%s, %s, %s);"
    values = (title, pass_hash, folder)

    success = True
    error_text = None
    try:
        cursor.execute(query, values)
        conn.commit()
    except mysql.connector.IntegrityError:
        conn.rollback()
        error_text = "Failed to create newsletter due to integrity error."
        success = False
    finally:
        cursor.close()
        conn.close()

    return success, error_text
