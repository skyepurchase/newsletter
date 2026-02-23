import os
import smtplib
import ssl

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from utils.html import format_html
from utils.type_hints import MailerConfig


PORT = 465
DIR = os.path.dirname(__file__)


def generate_email(config: MailerConfig):
    if config.isQuestion:
        request = "submit questions"
    elif config.isAnswer:
        request = "submit answers"
    else:
        request = "view"

    email_html = open(os.path.join(DIR, "../templates/email.html")).read()

    values = {
        "NAME": config.name.title(),
        "ISSUE": config.issue,
        "LINK": config.link,
        "TYPE": request,
    }

    return format_html(email_html, values)


def send_email(body: str, config: MailerConfig) -> bool:
    message = MIMEMultipart("alternative")
    message["Subject"] = f"{config.name} Issue {config.issue}"

    if config.debug:
        message["To"] = config.email
    else:
        message["To"] = ", ".join(config.addresses)

    message["From"] = config.email

    text = "If you are reading this, please contact me."

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(body, "html")

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", PORT, context=context) as server:
        try:
            server.login(config.email, config.password)
        except smtplib.SMTPAuthenticationError:
            return False

        if config.debug:
            server.sendmail(config.email, config.email, message.as_string())
        else:
            server.sendmail(config.email, config.addresses, message.as_string())

        return True
