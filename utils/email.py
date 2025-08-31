import smtplib, ssl

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .type_hints import NewsletterConfig


PORT = 465


def generate_email_request(config: NewsletterConfig):
    request = (
        "submit questions" if config.isQuestion
        else "submit answers" if config.isAnswer
        else "view"
    )

    email = f"""
<html><head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE-edge">
<meta name="viewpoint" content="width=device.width, initial-scale=1.0">
<title>{config.name}</title>
</head><body>\n"""

    if config.isSend:
        email += f'<h1>{config.name.title()} Issue {config.issue}</h1>\n'
    else:
        email += f'<h1>{request.title()} for Issue {config.issue}</h1>\n'

    email += f'<p>{config.text}</p>\n'
    email += f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; text-align: center; padding: 20px;">
        <a href={config.link} target="_blank" rel="noopener noreferrer" style="background-color: #6272a4; color: white; border: none; padding: 16px 32px; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; text-transform: none; letter-spacing: 0.5px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-decoration: none; display: inline-block; text-align: center;">{request.title()}</a>
</div>
"""
    email += "</body><html>\n"

    return email

def send_email(body, config):
    message = MIMEMultipart("alternative")
    message["Subject"] = f'{config.name} Issue {config.issue}'

    if (config.debug):
        message["To"] = config.email
    else:
        message["To"] = ', '.join(config.addresses)

    message["From"] = config.email

    text = "If you are reading this, please contact me."

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(body, "html")

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", PORT, context=context) as server:
        server.login(config.email, config.password)
        if config.debug:
            server.sendmail(
                config.email, config.email, message.as_string()
            )
        else:
            server.sendmail(
                config.email, config.addresses, message.as_string()
            )
