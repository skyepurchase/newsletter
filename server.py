import os
import shutil
from dotenv import load_dotenv
from datetime import datetime

from utils.constants import State
from utils.logger import renderer_logger as LOGGER
from utils.helpers import get_state, load_config
from utils.html import format_html, make_navbar
from utils.database import (
    get_questions,
    get_responses,
    insert_answer,
    insert_default_questions,
    insert_question,
)

from typing import DefaultDict, Optional
from utils.type_hints import NewsletterToken, NewsletterException


load_dotenv()


HOME = os.getenv("HOME")

DIR = os.path.dirname(__file__)
NOW = datetime.now()


def render_question_form(title: str, newsletter_id: int, issue: int) -> None:
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
    """
    LOGGER.info("Rendering question form")
    html = open(os.path.join(DIR, "templates/question_form.html")).read()
    submitted_questions = open(
        os.path.join(DIR, "templates/submitted_question.html")
    ).read()
    question = open(os.path.join(DIR, "templates/response.html")).read()

    submission_html = ""
    _, questions = get_questions(newsletter_id, issue)
    for submission in questions:
        _, name, text = submission

        values = {"NAME": name, "TEXT": text}

        submission_html += format_html(
            question[:],  # Copy string
            values,
            sanitize=True,
        )

    values = {
        "HEADER": open(os.path.join(DIR, "templates/header.html")).read(),
        "NAVBAR": make_navbar(issue, issue),
        "TITLE": f"{title} {issue}",
        "SUBMITTED": format_html(submitted_questions, {"RESPONSES": submission_html}),
    }

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render_answer_form(title: str, newsletter_id: int, issue: int) -> None:
    """
    Render the response form for the given newsletter.

    Parameters
    ----------
    title : str
        The title of the newsletter (prevents unnecessary database calls)
    newsletter_id : int
        The newsletter id
    issue : int
        The current issue number
    """
    LOGGER.info("Rendering answer form")
    html = open(os.path.join(DIR, "templates/answer.html")).read()
    user_question = open(os.path.join(DIR, "templates/user_question.html")).read()
    text_question = open(os.path.join(DIR, "templates/text_question.html")).read()
    img_question = open(os.path.join(DIR, "templates/image_question.html")).read()

    base_questions, user_questions = get_questions(newsletter_id, issue)

    question_html = ""
    for question in user_questions:
        q_id, q_creator, q_text = question
        values = {
            # People could be silly with this
            "ID": f"question_{q_id}",
            "NAME": q_creator,
            "QUESTION": q_text,
        }
        question_html += format_html(
            user_question[:],  # Copy string
            values,
            sanitize=True,
        )

    for question in base_questions:
        q_id, q_text, q_type = question
        values = {"ID": f"question_{q_id}", "QUESTION": q_text}

        if q_type == "text":
            question_html += format_html(
                text_question[:],  # Copy string
                values,
            )
        elif q_type == "image":
            values["IMG_ID"] = f"image_{q_id}"
            question_html += format_html(
                img_question[:],  # Copy string
                values,
            )
        else:
            raise NewsletterException(500, f"question type {q_type} unknown.")

    values = {
        "HEADER": open(os.path.join(DIR, "templates/header.html")).read(),
        "NAVBAR": make_navbar(issue, issue),
        "QUESTIONS": question_html,
        "TITLE": f"{title} {issue}",
    }

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render_newsletter(
    title: str, newsletter_id: int, issue: int, curr_issue: int
) -> None:
    """
    Render the given newsletter.

    Parameters
    ----------
    title : str
        The title of the newsletter (prevents unnecessary database calls)
    newsletter_id : int
        The newsletter id
    issue : int
        The issue number to render
    curr_issue : int
        The current issue according to the config files
    """
    LOGGER.info("Rendering published newsletter")
    html = open(os.path.join(DIR, "templates/newsletter.html")).read()
    text_response = open(os.path.join(DIR, "templates/response.html")).read()
    img_response = open(os.path.join(DIR, "templates/image_response.html")).read()
    question_board = open(os.path.join(DIR, "templates/question_board.html")).read()

    responses = get_responses(newsletter_id, issue)

    n_html = ""
    for question in responses:
        creator, q_text, q_responses = question
        q_values = {"CREATOR": creator, "QUESTION": q_text}
        q_html = ""
        for response in q_responses:
            name, text, img_path = response

            if img_path is None:
                q_html += format_html(
                    text_response, {"NAME": name, "TEXT": text}, sanitize=True
                )
            else:
                assert HOME is not None, "Failed to find home directory"

                filename = img_path.split("/")[-1]
                public_path = os.path.join(HOME, "public_html/images", filename)
                shutil.copy(img_path, public_path)
                q_html += format_html(
                    img_response,
                    {"NAME": name, "SRC": f"/images/{filename}", "CAPTION": text},
                    sanitize=True,
                )

        q_values["RESPONSES"] = q_html

        n_html += format_html(question_board, q_values)

    values = {
        "HEADER": open(os.path.join(DIR, "templates/header.html")).read(),
        "NAVBAR": make_navbar(issue, curr_issue),
        "TITLE": f"{title} {issue}",
        "NEWSLETTER": n_html,
    }

    print("Content-Type: text/html")
    print("Status: 200\n")

    print(format_html(html, values))


def render(
    token: NewsletterToken,
    issue: Optional[int],
) -> None:
    """
    Render the relevant form or page based on 'factors'.

    Parameters
    ----------
    token : NewsletterToken
        The dict of processed JSON web token
    issue : int
        The issue number to render
    """
    success, config = load_config(token.folder, LOGGER)
    if not success:
        raise NewsletterException(500, "Failed to load config")

    if issue is not None:
        if issue > config.issue or issue < 0:
            raise NewsletterException(
                404, f"Issue {issue} does not exist for {token.title}"
            )
        if issue < config.issue:
            LOGGER.debug(f"Rendering historical issue no. {issue}")
            # An old issue so just render it
            render_newsletter(token.title, token.id, issue, config.issue)
            return

    state = get_state()
    if state == State.Question:
        default_questions, _ = get_questions(token.id, config.issue)

        if len(default_questions) == 0:
            LOGGER.info("Inserting default questions")
            success, error = insert_default_questions(
                token.id, config.issue, config.defaults
            )

            if not success:
                LOGGER.warning(
                    f"Failed to add default questions:\n{error}\nWill attempt next time"
                )

        render_question_form(token.title, token.id, config.issue)
    elif state == State.Answer:
        render_answer_form(token.title, token.id, config.issue)
    else:
        render_newsletter(token.title, token.id, config.issue, config.issue)


def answer(parameters: dict):
    """
    Add a users answers to the database if they are authorised.

    Parameters
    ----------
    parameters : dict
        The dict of processed POST parameters
    """
    responses = DefaultDict(lambda: {"img": None, "text": None})
    name = ""

    for key, response in parameters.items():
        if key == "unlock":
            continue
        if key == "name":
            if response == "":
                raise NewsletterException(422, "No name provided")

            name = response
            continue

        parts = key.split("_")
        if len(parts) != 2:
            raise NewsletterException(
                400, "Form keys not in two parts. Do not mess with the post request!"
            )

        q_type = parts[0]
        q_id = parts[1]

        if q_type == "question":
            # Don't insert blank answers
            if len(response) > 0:
                responses[q_id]["text"] = response
        elif q_type == "image":
            LOGGER.info("Processing images upload")
            responses[q_id]["img"] = response["path"]
        else:
            raise NewsletterException(
                400,
                "Form keys are not in expected format. Do not mess with the post request!",
            )

    created, error = insert_answer(name, responses)
    if created:
        raise NewsletterException(201, "Thank you for submitting your answers :).")
    else:
        raise NewsletterException(500, error)


def question_submit(token: NewsletterToken, parameters: dict):
    """
    Add a users questions to the database if they are authorised.

    Parameters
    ----------
    token : NewsletterToken
        The dict of processed JSON web token
    parameters : dict
        The dict of processed POST parameters
    """
    success, config = load_config(token.folder, LOGGER)
    if not success:
        raise NewsletterException(500, "Failed to load config")

    name = parameters["name"]
    question = parameters["question"]

    if name == "" or question == "":
        raise NewsletterException(422, "No name or question provided")

    created, error = insert_question(token.id, config.issue, name, question)
    if created:
        raise NewsletterException(201, "Thank you for submitting your question :).")
    else:
        raise NewsletterException(500, error)
