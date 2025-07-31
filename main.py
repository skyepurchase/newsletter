import os, yaml, subprocess, tempfile, copy
from datetime import datetime

from email_utils import (
    generate_newsletter,
    generate_email_request,
    send_email
)
from form_utils import (
    get_questions,
    update_form
)
from type_hints import FormConfig, NewsletterConfig


EDITOR = os.environ.get('EDITOR', 'vim')
CONFIG_TIME_FORMAT = "%Y%m%d"


def main(config: NewsletterConfig) -> NewsletterConfig:
    with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
        # Open editor to write message
        if config.question:
            tf.write(b"Time to submit your questions!")
        elif config.answer:
            tf.write(b"Time to submit your responses!")
        else:
            tf.write(b"Hope you have all had a wonderful month!")

        tf.flush()
        subprocess.call([EDITOR, tf.name])

        # process message
        tf.seek(0)
        config.text = tf.read().decode("utf-8")
        os.remove(tf.name)

    with open(f'{config.folder}/emails.txt', "r") as addr_file:
        config.addresses = [addr.replace("\n", "") for addr in addr_file.readlines()]

    if config.question:
        email = generate_email_request(
            config, "question",
            config.question.link
        )
        images = {}

        config.question.cutoff = datetime.strftime(
            datetime.now(), CONFIG_TIME_FORMAT
        )
    elif config.answer:
        questions = get_questions(
            config.question.id,
            config.question.cutoff
        )
        update_form(config.answer.id, questions)
        email = generate_email_request(
            config, "answer",
            config.answer.link
        )
        images = {}

        config.answer.cutoff = datetime.strftime(
            datetime.now(), CONFIG_TIME_FORMAT
        )
    else:
        email, images = generate_newsletter(config)
        config.issue += 1

    send_email(email, images, config)
    return config


if __name__=='__main__':
    from argparse import ArgumentParser

    args = ArgumentParser(prog="Newsletter make script")
    args.add_argument("-p", "--password", required=True)
    args.add_argument("-c", "--config", required=True)
    args.add_argument("-d", "--debug", action="store_true")
    args.add_argument("-q", "--question", action="store_true")
    args.add_argument("-a", "--answer", action="store_true")

    args = args.parse_args()

    with open(args.config) as config_file:
        try:
            config = yaml.safe_load(config_file)
            old_config = copy.deepcopy(config)
        except yaml.YAMLError as e:
            print(e)
            quit()

    question_config = FormConfig(**config["question"])
    answer_config = FormConfig(**config["answer"])

    new_config = main(NewsletterConfig(
        isQuestion=args.question,
        isAnswer=args.answer,
        isSend=not(args.answer or args.question),
        password=args.password,
        debug=args.debug,
        name=config["name"],
        email=config["email"],
        issue=config["issue"],
        addresses=[config["email"]],
        folder=config["folder"],
        question=question_config,
        answer=answer_config,
        text="",
    ))

    # Do not overrid config when debugging
    if not args.debug:
        with open(args.config, 'w') as f:
            # Update yaml file values
            old_config["issue"] = new_config.issue
            old_config["question"]["cutoff"] = new_config.question.cutoff
            old_config["answer"]["cutoff"] = new_config.answer.cutoff
            yaml.dump(old_config, f, default_flow_style=False)
