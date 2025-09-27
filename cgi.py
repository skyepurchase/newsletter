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
    insert_question
)

from typing import DefaultDict, Tuple

DIR = os.path.dirname(__file__)
NOW = datetime.now()


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
    passcode: str,
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
    passcode : str
        The user submitted passcode
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
        "PASSCODE": passcode,
        "TITLE": f"{title} {issue}",
        "SUBMITTED": format_html(
            submitted_questions, {
                "RESPONSES": submission_html
            }, sanitize=True
        )
    }

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render_answer_form(
    title: str,
    passcode: str,
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
        "PASSCODE": passcode,
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

    values = {
        "TITLE": f"{title} {issue}"
    }
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
    values["NEWSLETTER"] = n_html

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render(
    parameters: dict,
    HttpResponse # TODO: type hint this properly
) -> None:
    """
    Render the relevant form or page based on 'factors'.

    Parameters
    ----------
    parameters : dict
        The dict of processed POST parameters
    HttpResponse : Error
        The suitable error to throw HTTP Responses
    """
    passcode = parameters["unlock"]
    if not isinstance(passcode, str):
        # Should only happen if people tamper with URL >:(
        raise HttpResponse(
            400,
            f"Expected 'unlock' to be of type `str` but received {type(passcode)}"
        )

    verified, n_id, title, folder = authenticate(passcode)
    if verified:
        # Load config
        try:
            with open(
                os.path.join(DIR, folder, "config.yaml"), "r"
            ) as f:
                config = yaml.safe_load(f)
                issue = int(config["issue"])
        except yaml.YAMLError:
            logger.debug(traceback.format_exc())
            raise HttpResponse(503, "Error loading YAML configuration")

        # Hack a Sunday start
        week = NOW.isocalendar()[1]
        day = NOW.isocalendar()[2]
        if day == 7: week += 1

        logger.debug(f"Issue: {issue}, Config folder: {folder}, stage: {week % 4}")

        if week % 4 in [1,2]:
            render_question_form(
                title, passcode, n_id, issue, HttpResponse
            )
        elif week % 4 == 3:
            render_answer_form(
                title, passcode, n_id, issue, HttpResponse
            )
        else:
            render_newsletter(
                title, n_id, issue, HttpResponse
            )
    else:
        raise HttpResponse(401, "Nice try, but that is not the passcode! If you are meant to find something try typing it in again.")


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
    passcode = parameters["unlock"]
    if not isinstance(passcode, str):
        # Should only happen if people tamper with URL >:(
        raise HttpResponse(
            400,
            f"Expected 'unlock' to be of type `str` but received {type(passcode)}"
        )

    verified, _, _, _ = authenticate(passcode)
    if verified:
        responses = DefaultDict(
            lambda: {"img": None, "text": None}
        )
        name = ""

        for key, response in parameters.items():
            if key=="unlock": continue
            if key=="name": name=response; continue

            parts = key.split("_")
            if len(parts) != 2:
                raise HttpResponse(400, "Form keys are not in expected format. Do not mess with the post request!")

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
    else:
        raise HttpResponse(401, "How did you manage that? Don't tapper with things please.")


def question_submit(
    parameters: dict,
    HttpResponse
):
    """
    Add a users questions to the database if they are authorised.

    Parameters
    ----------
    parameters : dict
        The dict of processed POST parameters
    HttpResponse : Error
The suitable error to throw HTTP Responses
    """
    passcode = parameters["unlock"]
    if not isinstance(passcode, str):
        # Should only happen if people tamper with URL >:(
        raise HttpResponse(
            400,
            f"Expected 'unlock' to be of type `str` but received {type(passcode)}"
        )

    verified, n_id, _, folder = authenticate(passcode)
    if verified:
        # Load config
        try:
            with open(
                os.path.join(DIR, folder, "config.yaml"), "r"
            ) as f:
                config = yaml.safe_load(f)
                issue = config["issue"]
        except yaml.YAMLError:
            logger.debug(traceback.format_exc())
            raise HttpResponse(503, "Error loading YAML configuration")

        name = parameters["name"]
        question = parameters["question"]

        created, error = insert_question(
            n_id, issue, name, question
        )
        if created:
            raise HttpResponse(201, "Thank you for submitting you question :).")
        else:
            raise HttpResponse(500, error)
    else:
        raise HttpResponse(401, "How did you manage that? Don't tapper with things please.")
