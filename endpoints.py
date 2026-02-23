import os
from datetime import datetime

from utils.constants import State
from utils.logger import renderer_logger as LOGGER
from utils.helpers import get_state, load_config
from utils.database import (
    get_questions,
    insert_answer,
    insert_default_questions,
    insert_question,
)
from renderers import render_question_form, render_answer_form, render_newsletter

from typing import DefaultDict, Optional
from utils.type_hints import NewsletterToken, NewsletterException


DIR = os.path.dirname(__file__)
NOW = datetime.now()


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
