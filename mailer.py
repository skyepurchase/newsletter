import os
import sys
import traceback

from utils.logger import mailer_logger as LOGGER
from utils.email import generate_email, send_email
from utils.helpers import load_config
from utils.type_hints import MailerConfig


EDITOR = os.getenv("EDITOR", "vim")


def main(config: MailerConfig) -> None:
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
        LOGGER.critical("Illegal config file submitted!")
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

    email = generate_email(config)
    send_email(email, config)


if __name__ == "__main__":
    from argparse import ArgumentParser
    from dotenv import load_dotenv

    load_dotenv()

    MAIL_PASS = os.getenv("MAIL_PASS")
    assert MAIL_PASS is not None, "Failed to find email config"

    args = ArgumentParser(prog="Mailer agent for newsletter")
    args.add_argument("-c", "--config_dir", required=True)
    args.add_argument("-d", "--debug", action="store_true")
    args.add_argument("-q", "--question", action="store_true")
    args.add_argument("-a", "--answer", action="store_true")
    args.add_argument("-m", "--manual", action="store_true")

    args = args.parse_args()

    success, config = load_config(os.path.join("/home/atp45", args.config_dir), LOGGER)
    if success:
        main(
            MailerConfig(
                isQuestion=args.question,
                isAnswer=args.answer,
                isSend=not (args.answer or args.question),
                isManual=args.manual,
                password=MAIL_PASS,
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
