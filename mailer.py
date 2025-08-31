import os, yaml, subprocess, tempfile, copy, sys, logging

from utils.constants import LOG_TIME_FORMAT
from utils.email import generate_email_request, send_email
from utils.type_hints import NewsletterConfig


EDITOR = os.environ.get('EDITOR', 'vim')


logger = logging.getLogger("mailer")


def main(config: NewsletterConfig) -> NewsletterConfig:
    formatter = logging.Formatter(
        f'[%(asctime)s %(levelname)s] {config.name}: %(message)s',
        datefmt=LOG_TIME_FORMAT
    )
    handler = logging.FileHandler(f"{config.folder}/log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if config.isQuestion:
        config.text = "Time to submit your questions!"
    elif config.isAnswer:
        config.text = "Time to submit your responses!"
    elif config.isSend:
        config.text = "Hope you have all had a wonderful month!"

    if config.isManual:
        with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
            # Open editor to write message
            tf.write(config.text.encode('utf-8'))
            tf.flush()
            subprocess.call([EDITOR, tf.name])

            # process message
            tf.seek(0)
            config.text = tf.read().decode("utf-8")
            os.remove(tf.name)

    with open(f'{config.folder}/emails.txt', "r") as addr_file:
        config.addresses = [addr.replace("\n", "") for addr in addr_file.readlines()]

    if config.isQuestion:
        logger.info(f"Question request")
        email = generate_email_request(config)
    elif config.isAnswer:
        logger.info(f"Answer request")
        email = generate_email_request(config)
    elif config.isSend:
        logger.info("Publishing")
        email = generate_email_request(config)
        config.issue += 1
    else:
        logger.warning(f"Illegal config file submitted!")
        sys.exit(2)

    send_email(email, config)
    return config


if __name__=='__main__':
    from argparse import ArgumentParser

    args = ArgumentParser(prog="Newsletter make script")
    args.add_argument("-p", "--password", required=True)
    args.add_argument("-c", "--config", required=True)
    args.add_argument("-d", "--debug", action="store_true")
    args.add_argument("-q", "--question", action="store_true")
    args.add_argument("-a", "--answer", action="store_true")
    args.add_argument("-m", "--manual", action="store_true")

    args = args.parse_args()

    with open(args.config) as config_file:
        try:
            config = yaml.safe_load(config_file)
            old_config = copy.deepcopy(config)
        except yaml.YAMLError as e:
            logger.debug("An error occurred opening the YAML configuration\n", e)
            sys.exit(1)

    new_config = main(NewsletterConfig(
        isQuestion=args.question,
        isAnswer=args.answer,
        isSend=not(args.answer or args.question),
        isManual=args.manual,
        password=args.password,
        debug=args.debug,
        name=config["name"],
        email=config["email"],
        issue=config["issue"],
        addresses=[config["email"]],
        folder=config["folder"],
        link=config["link"],
        text="",
    ))

    # Do not override config when debugging
    if not args.debug:
        with open(args.config, 'w') as f:
            # Update yaml file values
            old_config["issue"] = new_config.issue
            yaml.dump(old_config, f, default_flow_style=False)
