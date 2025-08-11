#!/usr/bin/python3

import os

from utils import verify, format_html
from http_lib import HttpResponse, params, wrap


DIR = os.path.dirname(__file__)

PARAMETERS = params()


def main() -> None:
    passcode = PARAMETERS["unlock"]
    if not isinstance(passcode, str):
        # Should only happen if people tamper with URL >:(
        raise HttpResponse(
            400,
            f"Expected 'unlock' to be of type `str` but received {type(passcode)}"
        )

    verified = verify(
        passcode,
        os.path.join(DIR, "newsletter.pass")
    )

    if verified:
        with open(os.path.join(DIR, "templates/newsletter/answer.html")) as f:
            html = f.read()
            values = {
                "PASSCODE": PARAMETERS["unlock"],
                "QUESTIONS": "",
                "TITLE": "The Glorious Test"
            }

            print("Content-Type: text/html")
            print("Status: 200\n")

            print(format_html(html, values))
    else:
        raise HttpResponse(401, "Nice try, but that is not the passcode! If you are meant to find something try typing it in again.")

wrap(main)
