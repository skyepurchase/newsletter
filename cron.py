#!/bin/python3


import os
import logging
import mailer
from utils.constants import State
from utils.helpers import get_state, check_and_increment_issue, load_config
from utils.type_hints import MailerConfig


def main(home: str, password: str):
    state = get_state()

    if not os.path.isdir(os.path.join(home, "newsletters")):
        print("Newsletter folder does not exist")
        exit(2)

    for newsletter in os.listdir(os.path.join(home, "newsletters")):
        success, msg = check_and_increment_issue(
            os.path.join(home, "newsletters", newsletter)
        )

        if not success:
            print(f"Failed to increment the issue for {newsletter}: {msg}")
            exit(3)

        success, config = load_config(
            os.path.join(home, "newsletters", newsletter), logging.getLogger(__name__)
        )

        if not success:
            print(f"Unable to load config for {newsletter}")
            continue

        mail_config = MailerConfig(
            isQuestion=False,
            isAnswer=False,
            isSend=False,
            isManual=False,
            password=password,
            debug=False,
            name=config.name,
            email=config.email,
            issue=config.issue,
            addresses=[config.email],
            folder=config.folder,
            link=config.link,
            text="",
        )

        msg = ""
        if state == State.Question:
            mail_config.isQuestion = True
            msg = "question request"
        elif state == State.Answer:
            mail_config.isAnswer = True
            msg = "answer request"
        else:
            mail_config.isSend = True
            msg = "publishing"

        mailer.main(mail_config)

        print(f"{newsletter} {msg} successful")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    HOME = os.getenv("HOME")
    MAIL_PASS = os.getenv("MAIL_PASS")

    if HOME is None:
        print("Unable to find $HOME variable")
        exit(1)

    if MAIL_PASS is None:
        print("Unable to find $MAIL_PASS variable")
        exit(1)

    main(HOME, MAIL_PASS)

    print("Done")
    exit(0)
