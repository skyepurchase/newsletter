import json, traceback, logging

import mysql.connector
from mysql.connector.errors import Error, IntegrityError, ProgrammingError

from typing import List, Optional, Tuple

from .type_hints import Response
from .constants import LOG_TIME_FORMAT


with open("/home/atp45/.secrets.json", "r") as f:
    SECRETS = json.loads(f.read())


formatter = logging.Formatter(
    '[%(asctime)s %(levelname)s] %(message)s',
    datefmt=LOG_TIME_FORMAT
)
logger = logging.getLogger(__name__)
handler = logging.FileHandler("/home/atp45/logs/mysql")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


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
    logger.info("Connection opened")

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
        logger.info("Connection closed")

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
    except ProgrammingError:
        logger.debug(traceback.format_exc())
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

    return default, submitted


def get_responses(
    newsletter_id: int,
    issue: int
) -> List[Response]:
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

            if not isinstance(q_id, int):
                logger.debug(f"Expected q_id to be int but receieved {type(q_id)}")
                raise TypeError(f"Expected q_id to be int but receieved {type(q_id)}")

            cursor.execute(response_query, (q_id,))
            responses = cursor.fetchall()

            results.append((creator, question, responses))

        for question in default_questions:
            q_id, question = question

            if not isinstance(q_id, int):
                logger.debug(f"Expected q_id to be int but receieved {type(q_id)}")
                raise TypeError(f"Expected q_id to be int but receieved {type(q_id)}")

            cursor.execute(response_query, (q_id,))
            responses = cursor.fetchall()

            results.append(("", question, responses))

    except TypeError:
        logger.error("Failed to retrieve responses due to type error: %s", traceback.format_exc())
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

    return results


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
            # Skip duplicate entries
            # This is unsafe but avoids unauthorised data overwrite
            # It does not prevent malicious lock-out
            query = """
            INSERT IGNORE INTO answers (question_id, name, img_path, text)
            VALUES (%s, %s, %s, %s);
            """
            # ON DUPLICATE KEY UPDATE img_path=%s, text=%s;
            values = (
                q_id, name,
                data['img'], data['text'],
                # data['img'], data['text']
            )

            cursor.execute(query, values)

        conn.commit()
    except Error as error:
        logger.error("Failed to submit answers, rollback: %s", traceback.format_exc())

        conn.rollback()
        success = False
        error_text = error.msg
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

    return success, error_text


def insert_question(
    newsletter_id: int,
    issue: int,
    name: str,
    question: str,
) -> Tuple[bool, Optional[str]]:
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
    error_text: Optional[str] = None
    try:
        query = """
        INSERT INTO questions (newsletter_id, creator, text, issue)
        VALUES (%s, %s, %s, %s);
        """
        values = (
            newsletter_id, name, question, issue
        )

        cursor.execute(query, values)
        conn.commit()
    except Error as error:
        logger.error("Failed to insert question, rollback: %s", traceback.format_exc())

        conn.rollback()
        success = False
        error_text = error.msg
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

    return success, error_text


def insert_default_questions(
    newsletter_id: int,
    issue: int,
    questions: List[Tuple[str, str]]
) -> bool:
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

    try:
        query = """
        INSERT INTO questions (newsletter_id, creator, text, issue, base, type)
        VALUES (%s, %s, %s, %s, %s, %s);
        """

        for text, form in questions:
            values = (
                newsletter_id, "SYS", text,
                issue, True, form
            )
            cursor.execute(query, values)

        conn.commit()
    except Error:
        logger.error("Failed to insert question, rollback: %s", traceback.format_exc())

        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

    return True


def create_newsletter(
    title: str,
    pass_hash: bytes,
    folder: str
) -> bool:
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
    try:
        cursor.execute(query, values)
        conn.commit()
    except IntegrityError:
        logger.error("Failed to create newsletter due to integrity error.")
        success = False
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")

    return success
