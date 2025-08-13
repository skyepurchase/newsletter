#!/usr/bin/python3

import os
import json

import mysql.connector

from utils import verify, format_html
from http_lib import HttpResponse, params, wrap


DIR = os.path.dirname(__file__)
PARAMETERS = params()

with open(".secrets.json", "r") as f:
    SECRETS = json.loads(f.read())


def main() -> None:
    passcode = PARAMETERS["unlock"]
    if not isinstance(passcode, str):
        # Should only happen if people tamper with URL >:(
        raise HttpResponse(
            400,
            f"Expected 'unlock' to be of type `str` but received {type(passcode)}"
        )

    db = mysql.connector.connect(
        host="localhost",
        user="atp45",
        password=SECRETS["DB_PASS"],
        database="atp45/newsletter"
    )
    cursor = db.cursor()
    sql = "SELECT * FROM newsletters;"
    cursor.execute(sql)
    result = cursor.fetchall()

    verified = False
    title = ""
    newsletter_id = -1
    for entry in result:
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
        with open(os.path.join(DIR, "templates/newsletter/answer.html")) as f:
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

wrap(main)
