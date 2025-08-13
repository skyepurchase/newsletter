import os

from .utils.html import verify, format_html
from .utils.database import get_newsletters, get_questions


DIR = os.path.dirname(__file__)


def render(
    parameters: dict,
    HttpResponse # TODO: type hint this properly
) -> None:
    passcode = parameters["unlock"]
    if not isinstance(passcode, str):
        # Should only happen if people tamper with URL >:(
        raise HttpResponse(
            400,
            f"Expected 'unlock' to be of type `str` but received {type(passcode)}"
        )

    newsletters = get_newsletters()

    verified = False
    title = ""
    newsletter_id = -1
    for entry in newsletters:
        n_id, n_title, n_hash = entry
        assert isinstance(n_hash, bytes), "SQL returned a hash that was not in bytes."

        verified = verify(
            passcode,
            n_hash
        )
        if verified:
            title = n_title
            newsletter_id = n_id
            break

    if verified:
        # TODO: choose what content to show somehow
        with open(os.path.join(DIR, "templates/question_box.html")) as f:
            question_template = f.read()

        # TODO: dynamically choose the issue number as well
        questions = get_questions(newsletter_id, 11)
        question_html = ""
        for question in questions:
            q_id, q_creator, q_text = question
            values = {
                # People could be silly with this
                "ID": f"question_{q_id}",
                "NAME": q_creator,
                "QUESTION": q_text
            }
            question_html += format_html(
                question_template[:], # Copy string
                values
            )

        with open(os.path.join(DIR, "templates/answer.html")) as f:
            html = f.read()
            values = {
                "PASSCODE": passcode,
                "QUESTIONS": question_html,
                "TITLE": title
            }

            print("Content-Type: text/html")
            print("Status: 200\n")

            print(format_html(html, values))
    else:
        raise HttpResponse(401, "Nice try, but that is not the passcode! If you are meant to find something try typing it in again.")
