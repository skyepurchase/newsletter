#!/bin/python3


import json
import logging
import mailer
from utils.constants import State
from utils.helpers import get_state, check_and_increment_issue, load_config
from utils.type_hints import MailerConfig


if __name__=='__main__':
    import os

    HOME = os.getenv("HOME")
    if HOME is None:
        print("Unable to find $HOME variable")
        exit(1)

    with open(os.path.join(HOME, ".secrets.json"), "r") as f:
        SECRETS = json.load(f)

    state = get_state()

    if not os.path.isdir(os.path.join(HOME, "newsletters")):
        print("Newsletter folder does not exist")
        exit(2)

    for newsletter in os.listdir(os.path.join(HOME, "newsletters")):
        success, msg = check_and_increment_issue(os.path.join(HOME, "newsletters", newsletter))

        if not success:
            print(f"Failed to increment the issue for {newsletter}: {msg}")
            exit(3)

        success, config = load_config(os.path.join(HOME, "newsletters", newsletter), logging.getLogger(__name__))

        if not success:
            print(f"Unable to load config for {newsletter}")
            continue

        mail_config = MailerConfig(
            isQuestion=False,
            isAnswer=False,
            isSend=False,
            isManual=False,
            password=SECRETS["MAIL_PASS"],
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

    print("Done")
    exit(0)
