import os, json, sys, logging

from utils.constants import LOG_TIME_FORMAT
from utils.email import generate_email_request, send_email
from utils.helpers import get_config_and_issue
from utils.type_hints import NewsletterConfig


EDITOR = os.environ.get('EDITOR', 'vim')

with open(f"/home/atp45/.secrets.json", "r") as f:
    SECRETS = json.loads(f.read())


logger = logging.getLogger("mailer")


def main(config: NewsletterConfig) -> NewsletterConfig:
    formatter = logging.Formatter(
        f'[%(asctime)s %(levelname)s] {config.name}: %(message)s',
        datefmt=LOG_TIME_FORMAT
    )
    handler = logging.FileHandler(f"{config.folder}/log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    if config.isQuestion:
        logger.info(f"Question request")
        config.text = "Time to submit your questions!"
    elif config.isAnswer:
        logger.info(f"Answer request")
        config.text = "Time to submit your responses!"
    elif config.isSend:
        logger.info("Publishing")
        config.text = "Hope you have all had a wonderful month!"
    else:
        logger.warning(f"Illegal config file submitted!")
        sys.exit(2)

    with open(f'{config.folder}/emails.txt', "r") as addr_file:
        config.addresses = [addr.replace("\n", "") for addr in addr_file.readlines()]

    email = generate_email_request(config)
    send_email(email, config)

    return config


if __name__=='__main__':
    from argparse import ArgumentParser

    args = ArgumentParser(prog="Newsletter make script")
    args.add_argument("-c", "--config_dir", required=True)
    args.add_argument("-d", "--debug", action="store_true")
    args.add_argument("-q", "--question", action="store_true")
    args.add_argument("-a", "--answer", action="store_true")
    args.add_argument("-m", "--manual", action="store_true")

    args = args.parse_args()

    success, config, issue = get_config_and_issue(args.config_dir)
    if not success:
        logger.critical(f"An error occurred loading {args.config_dir}")

    new_config = main(NewsletterConfig(
        isQuestion=args.question,
        isAnswer=args.answer,
        isSend=not(args.answer or args.question),
        isManual=args.manual,
        password=SECRETS["MAIL_PASS"],
        debug=args.debug,
        name=config["name"],
        email=config["email"],
        issue=issue,
        addresses=[config["email"]],
        folder=config["folder"],
        link=config["link"],
        text="",
    ))
