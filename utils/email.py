import smtplib, ssl, base64

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

from form_utils import download_image, get_form_data
from type_hints import NewsletterConfig

from typing import Tuple


PORT = 465


def convert_image(filepath: str) -> bytes:
    with open(filepath, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read())
        return encoded_string


def generate_newsletter(config: NewsletterConfig) -> Tuple[str, dict]:
    ordered_responses, id_to_title, image_paths, photo_id, captions = get_form_data(
        config.answer.id,
        config.answer.cutoff,
        config.isManual
    )

    # Construct email
    email = f"""
<html><head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE-edge">
<meta name="viewpoint" content="width=device.width, initial-scale=1.0">
<title>{config.name}</title>
</head><body>\n"""
    email += f'<h1>{config.name} Issue {config.issue}</h1>\n'
    email += f'<p>{config.text}</p>\n'

    for key, responses in ordered_responses.items():
        title = id_to_title[key]
        email += f"<h1>{title}</h1>\n"
        for name, response in responses.items():
            email += f"<h2>{name}</h2>\n"

            if key == photo_id and name in image_paths:
                caption = ""
                if name in captions:
                    caption = captions[name]

                email += f'<img src="cid:{name.replace(" ", "")}" alt="{caption}" width="500px" />\n'
                email += f'<p>{caption}</p>\n'
            else:
                email += f"<p>{response}</p>\n"

    email += "</body><html>\n"

    return email, image_paths


def generate_email_request(
    config: NewsletterConfig,
    request_type: str,
    form_link: str
):
    email = f"""
<html><head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE-edge">
<meta name="viewpoint" content="width=device.width, initial-scale=1.0">
<title>{config.name}</title>
</head><body>\n"""
    email += f'<h1>Submit Your {request_type.title()} for Issue {config.issue}</h1>\n'
    email += f'<p>{config.text}</p>\n'
    email += f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; text-align: center; padding: 20px;">
        <a href={form_link} target="_blank" rel="noopener noreferrer" style="background-color: #6272a4; color: white; border: none; padding: 16px 32px; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; text-transform: none; letter-spacing: 0.5px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-decoration: none; display: inline-block; text-align: center;">Submit {request_type.capitalize()}s</a>
</div>
"""
    email += "</body><html>\n"

    return email

def send_email(body, images, config):
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

    for idx, filepath in images.items():
        image_bytes = download_image(filepath, config.isManual)
        msg_image = MIMEImage(image_bytes.read())

        msg_image.add_header('Content-ID', f'<{idx.replace(" ", "")}>')
        message.attach(msg_image)

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
