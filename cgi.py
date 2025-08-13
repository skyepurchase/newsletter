import os

from .utils.html import verify, format_html
from .utils.database import get_newsletters


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
        with open(os.path.join(DIR, "templates/answer.html")) as f:
            html = f.read()
            values = {
                "PASSCODE": passcode,
                "QUESTIONS": "",
                "TITLE": title
            }

            print("Content-Type: text/html")
            print("Status: 200\n")

            print(format_html(html, values))
    else:
        raise HttpResponse(401, "Nice try, but that is not the passcode! If you are meant to find something try typing it in again.")
