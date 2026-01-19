import os
import json
import sys
import logging
import traceback

from utils.constants import LOG_TIME_FORMAT
from utils.email import generate_email_request, send_email
from utils.helpers import load_config
from utils.type_hints import MailerConfig


EDITOR = os.environ.get("EDITOR", "vim")

with open("/home/atp45/.secrets.json", "r") as f:
    SECRETS = json.loads(f.read())


LOGGER = logging.getLogger("mailer")
formatter = logging.Formatter(
    "[%(asctime)s %(levelname)s] GENERIC: %(message)s", datefmt=LOG_TIME_FORMAT
)
handler = logging.FileHandler("/home/atp45/logs/mailer")
handler.setFormatter(formatter)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.DEBUG)


def main(config: MailerConfig) -> MailerConfig:
    formatter = logging.Formatter(
        f"[%(asctime)s %(levelname)s] {config.name}: %(message)s",
        datefmt=LOG_TIME_FORMAT,
    )
    handler = logging.FileHandler("/home/atp45/logs/mailer")
    handler.setFormatter(formatter)

    for hdlr in LOGGER.handlers[:]:
        LOGGER.removeHandler(hdlr)
    LOGGER.addHandler(handler)

    if config.isQuestion:
        LOGGER.info("Question request")
        config.text = "Time to submit your questions!"
    elif config.isAnswer:
        LOGGER.info("Answer request")
        config.text = "Time to submit your responses!"
    elif config.isSend:
        LOGGER.info("Publishing")
        config.text = "Hope you have all had a wonderful month!"
    else:
        LOGGER.warning("Illegal config file submitted!")
        sys.exit(2)

    try:
        with open(f"{config.folder}/emails.txt", "r") as addr_file:
            config.addresses = [
                addr.replace("\n", "") for addr in addr_file.readlines()
            ]
    except OSError:
        LOGGER.critical("Failed to load target addresses")
        LOGGER.debug(traceback.format_exc())
        exit(1)

    email = generate_email_request(config)
    send_email(email, config)

    return config


if __name__ == "__main__":
    from argparse import ArgumentParser

    args = ArgumentParser(prog="Newsletter make script")
    args.add_argument("-c", "--config_dir", required=True)
    args.add_argument("-d", "--debug", action="store_true")
    args.add_argument("-q", "--question", action="store_true")
    args.add_argument("-a", "--answer", action="store_true")
    args.add_argument("-m", "--manual", action="store_true")

    args = args.parse_args()

    success, config = load_config(args.config_dir, LOGGER)
    if success:
        main(
            MailerConfig(
                isQuestion=args.question,
                isAnswer=args.answer,
                isSend=not (args.answer or args.question),
                isManual=args.manual,
                password=SECRETS["MAIL_PASS"],
                debug=args.debug,
                name=config.name,
                email=config.email,
                issue=config.issue,
                addresses=[config.email],
                folder=config.folder,
                link=config.link,
                text="",
            )
        )
    else:
        exit(1)
