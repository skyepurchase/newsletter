import os, shutil, logging, traceback

from datetime import datetime

import yaml

from .utils.constants import LOG_TIME_FORMAT
from .utils.html import verify, format_html
from .utils.database import (
    get_newsletters,
    get_questions,
    get_responses,
    insert_answer,
    insert_default_questions,
    insert_question
)

from typing import DefaultDict, Optional, Tuple

DIR = os.path.dirname(__file__)
NOW = datetime.now()

HEADER = open(
    os.path.join(DIR, "templates/header.html")).read()
NAVBAR = open(
    os.path.join(DIR, "templates/navbar.html")).read()


formatter = logging.Formatter(
    '[%(asctime)s %(levelname)s] %(message)s',
    datefmt=LOG_TIME_FORMAT
)
logger = logging.getLogger(__name__)
handler = logging.FileHandler("/home/atp45/logs/newsletter")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def authenticate(
    passcode: str
) -> Tuple[bool, int, str, str]:
    """
    Check whether a user is verified and then return the relevant newsletter details.

    Parameters
    ----------
    passcode : str
        The passcode to test

    Returns
    -------
    verified : bool
        Whether the user is verified
    newsletter_id : int
        The id of the authenticated newsletter
    title : str
        The title of the authenticated newsletter
    folder : str
        The folder storing metadata for the newsletter
    """
    newsletters = get_newsletters()

    for entry in newsletters:
        n_id, n_title, n_hash, n_folder = entry
        assert isinstance(n_hash, bytes), "SQL returned a hash that was not in bytes."

        if verify(passcode, n_hash):
            return True, n_id, n_title, n_folder

    return False, -1, "", ""


def render_question_form(
    title: str,
    newsletter_id: int,
    issue: int,
    HttpResponse
) -> None:
    """
    Render the question submission form for the given newsletter.

    Parameters
    ----------
    title : str
        The title of the newsletter (prevents unnecessary database calls)
    newsletter_id : int
        The newsletter ID
    issue : int
        The current issue number
    HttpResponse
        An Exception object to throw which is handled by the HTTP server
    """
    logger.info("Rendering question form")
    html = open(os.path.join(
        DIR, "templates/question_form.html"
    )).read()
    submitted_questions = open(os.path.join(
        DIR, "templates/submitted_question.html"
    )).read()
    question = open(os.path.join(
        DIR, "templates/response.html"
    )).read()

    submission_html = ""
    _, questions = get_questions(newsletter_id, issue)
    for submission in questions:
        _, name, text = submission

        values = {
            "NAME": name,
            "TEXT": text
        }

        submission_html += format_html(
            question[:], # Copy string
            values,
            sanitize=True
        )

    values = {
        "HEADER": HEADER,
        "NAVBAR": NAVBAR,
        "TITLE": f"{title} {issue}",
        "SUBMITTED": format_html(
            submitted_questions, {
                "RESPONSES": submission_html
            }
        )
    }

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render_answer_form(
    title: str,
    newsletter_id: int,
    issue: int,
    HttpResponse
) -> None:
    """
    Render the response form for the given newsletter.

    Parameters
    ----------
    title : str
        The title of the newsletter (prevents unnecessary database calls)
    passcode : str
        The user submitted passcode
    newsletter_id : int
        The newsletter id
    issue : int
        The current issue number
    HttpResponse
        An Exception object to throw which is handled by the HTTP server
    """
    logger.info("Rendering answer form")
    html = open(os.path.join(
        DIR, "templates/answer.html"
    )).read()
    user_question = open(os.path.join(
        DIR,
        "templates/user_question.html"
    )).read()
    text_question = open(os.path.join(
        DIR,
        "templates/text_question.html"
    )).read()
    img_question = open(os.path.join(
        DIR,
        "templates/image_question.html"
    )).read()

    base_questions, user_questions = get_questions(newsletter_id, issue)

    question_html = ""
    for question in user_questions:
        q_id, q_creator, q_text = question
        values = {
            # People could be silly with this
            "ID": f"question_{q_id}",
            "NAME": q_creator,
            "QUESTION": q_text
        }
        question_html += format_html(
            user_question[:], # Copy string
            values,
            sanitize=True
        )

    for question in base_questions:
        q_id, q_text, q_type = question
        values = {
            "ID": f"question_{q_id}",
            "QUESTION": q_text
        }

        if q_type=="text":
            question_html += format_html(
                text_question[:], # Copy string
                values
            )
        elif q_type=="image":
            values["IMG_ID"] = f"image_{q_id}"
            question_html += format_html(
                img_question[:], # Copy string
                values
            )
        else:
            raise HttpResponse(500, f"question type {q_type} unknown.")

    values = {
        "HEADER": HEADER,
        "NAVBAR": NAVBAR,
        "QUESTIONS": question_html,
        "TITLE": f"{title} {issue}"
    }

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render_newsletter(
    title: str,
    newsletter_id: int,
    issue: int,
    HttpResponse
) -> None:
    """
    Render the given newsletter.

    Parameters
    ----------
    title : str
        The title of the newsletter (prevents unnecessary database calls)
    newsletter_id : int
        The newsletter id
    HttpResponse
        An Exception object to throw which is handled by the HTTP server
    """
    logger.info("Rendering published newsletter")
    html = open(os.path.join(
        DIR, "templates/newsletter.html"
    )).read()
    text_response = open(os.path.join(
        DIR, "templates/response.html"
    )).read()
    img_response = open(os.path.join(
       DIR, "templates/image_response.html"
    )).read()
    question_board = open(os.path.join(
        DIR, "templates/question_board.html"
    )).read()

    responses = get_responses(newsletter_id, issue)

    n_html = ""
    for question in responses:
        creator, q_text, q_responses = question
        q_values = {
            "CREATOR": creator,
            "QUESTION": q_text
        }
        q_html = ""
        for response in q_responses:
            name, text, img_path = response

            if img_path is None:
                q_html += format_html(
                    text_response,
                    {
                        "NAME": name,
                        "TEXT": text
                    },
                    sanitize=True
                )
            else:
                filename = img_path.split("/")[-1]
                public_path = os.path.join(
                    "/home/atp45/public_html/images",
                    filename
                )
                shutil.copy(img_path, public_path)
                q_html += format_html(
                    img_response,
                    {
                        "NAME": name,
                        "SRC": f"/images/{filename}",
                        "CAPTION": text
                    }
                )

        q_values["RESPONSES"] = q_html

        n_html += format_html(
            question_board, q_values
        )
    values = {
        "HEADER": HEADER,
        "NAVBAR": NAVBAR,
        "TITLE": f"{title} {issue}",
        "NEWSLETTER": n_html
    }

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render(
    token: dict,
    issue: Optional[int],
    HttpResponse # TODO: type hint this properly
) -> None:
    """
    Render the relevant form or page based on 'factors'.

    Parameters
    ----------
    token : dict
        The dict of processed JSON web token
    issue : int
        The issue number to render
    HttpResponse : Error
        The suitable error to throw HTTP Responses
    """
    config_file = open(
        os.path.join(
            "/home/atp45",
            token["newsletter_folder"],
            "config.yaml"
        ), "r"
    )
    try:
        config = yaml.safe_load(config_file)
    except yaml.YAMLError:
        logger.debug(traceback.format_exc())
        raise HttpResponse(500, "Error loading YAML configuration")
    finally:
        config_file.close()

    issue_file = open(
        os.path.join(
            "/home/atp45",
            token["newsletter_folder"],
            "issue"
        ), "r"
    )
    try:
        curr_issue = int(issue_file.read())
    except ValueError:
        logger.debug(traceback.format_exc())
        raise HttpResponse(500, "Error loading issue file")
    finally:
        issue_file.close()

    if issue:
        if issue > curr_issue:
            raise HttpResponse(404, f"Issue {issue} does not exist for {token['newsletter_title']}")
        if issue < curr_issue:
            logger.debug(f"Rendering historical issue no. {issue}")
            # An old issue so just render it
            render_newsletter(
                token["newsletter_title"],
                token["newsletter_id"],
                issue,
                HttpResponse
            )
            return

    # Hack a Sunday start
    week = NOW.isocalendar()[1]
    day = NOW.isocalendar()[2]
    if day == 7: week += 1

    logger.debug(f"Issue: {curr_issue}, Config folder: {token['newsletter_folder']}, stage: {week % 4}")

    if week % 4 in [1,2]:
        default_questions, _ = get_questions(
            token['newsletter_id'], curr_issue
        )

        if len(default_questions) == 0:
            logger.info("Inserting default questions")
            success = insert_default_questions(
                token['newsletter_id'],
                curr_issue, config["defaults"]
            )

            if not success:
                logger.warning("Failed to add default questions. Will attempt next time")

        render_question_form(
            token['newsletter_title'],
            token['newsletter_id'],
            curr_issue, HttpResponse
        )
    elif week % 4 == 3:
        render_answer_form(
            token['newsletter_title'],
            token['newsletter_id'],
            curr_issue, HttpResponse
        )
    else:
        render_newsletter(
            token['newsletter_title'],
            token['newsletter_id'],
            curr_issue, HttpResponse
        )


def answer(
    parameters: dict,
    HttpResponse
):
    """
    Add a users answers to the database if they are authorised.

    Parameters
    ----------
    parameters : dict
        The dict of processed POST parameters
    HttpResponse : Error
The suitable error to throw HTTP Responses
    """
    responses = DefaultDict(
        lambda: {"img": None, "text": None}
    )
    name = ""

    for key, response in parameters.items():
        if key == "unlock": continue
        if key == "name":
            if response == "":
                raise HttpResponse(422, "No name provided")

            name=response
            continue

        parts = key.split("_")
        if len(parts) != 2:
            raise HttpResponse(400, "Form keys not in two parts. Do not mess with the post request!")

        q_type = parts[0]
        q_id = parts[1]

        if q_type=="question":
            # Don't insert blank answers
            if len(response) > 0:
                responses[q_id]["text"] = response
        elif q_type=="image":
            logger.info("Processing images upload")
            responses[q_id]["img"] = response['path']
        else:
            raise HttpResponse(400, "Form keys are not in expected format. Do not mess with the post request!")

    created, error = insert_answer(name, responses)
    if created:
        raise HttpResponse(201, "Thank you for submitting you answers :).")
    else:
        raise HttpResponse(500, error)


def question_submit(
    token: dict,
    parameters: dict,
    HttpResponse
):
    """
    Add a users questions to the database if they are authorised.

    Parameters
    ----------
    token : dict
        The dict of processed JSON web token
    parameters : dict
        The dict of processed POST parameters
    HttpResponse : Error
The suitable error to throw HTTP Responses
    """
    # Load config
    try:
        with open(
            os.path.join("/home/atp45", token["newsletter_folder"], "config.yaml"), "r"
        ) as f:
            config = yaml.safe_load(f)
            issue = config["issue"]
    except yaml.YAMLError:
        logger.debug(traceback.format_exc())
        raise HttpResponse(500, "Error loading YAML configuration")

    name = parameters["name"]
    question = parameters["question"]

    if name == "" or question == "":
        raise HttpResponse(422, "No name or question provided")

    created, error = insert_question(
        token["newsletter_id"], issue, name, question
    )
    if created:
        raise HttpResponse(201, "Thank you for submitting you question :).")
    else:
        raise HttpResponse(500, error)
