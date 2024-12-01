import os, smtplib, ssl, base64, yaml, subprocess, tempfile

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from argparse import ArgumentParser

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

PORT = 465
EDITOR = os.environ.get('EDITOR', 'vim')


SCOPES = [
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/forms.body.readonly',
    'https://www.googleapis.com/auth/drive'
]

def create_service(*args):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build(*args, credentials=creds)


def download_image(file_id):
    service = create_service('drive', 'v3')
    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fd=fh, request=request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download Progress: {int(status.progress() * 100)}")

    fh.seek(0)
    return fh


def get_form_data(form_id):
    service = create_service('forms', 'v1')
    form = service.forms().get(formId=form_id).execute()
    responses = service.forms().responses().list(formId=form_id).execute()

    return form, responses


def convert_image(filepath: str) -> bytes:
    with open(filepath, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read())
        return encoded_string


def generate_newsletter(config):
    # Get the data in a nice format
    name_id = ""
    caption_id = ""
    photo_id = ""
    ids = []
    id_to_title = {}

    # Extract google id data
    form, answers = get_form_data(config["id"])
    for question in form["items"]:
        question_id = question["questionItem"]["question"]["questionId"]
        id_to_title[question_id] = question["title"]

        if question["title"] == "Name":
            name_id = question_id
        elif question["title"] == "✍️ Caption":
            caption_id = question_id
        elif question["title"] not in ["Timestamp", "❓Submit A Question"]:
            ids.append(question_id)
            if question["title"] == "📸 Photo Wall":
                photo_id = question_id

    # Extract responses
    image_filepaths = {}
    title_ordered_responses = {}
    captions = {}

    for response in answers["responses"]:
        answers = response["answers"]

        name = answers[name_id]["textAnswers"]["answers"][0]["value"]

        if photo_id in answers:
            image_filepaths[name] = answers[photo_id]["fileUploadAnswers"]["answers"][0]["fileId"]
        if caption_id in answers:
            captions[name] = answers[caption_id]["textAnswers"]["answers"][0]["value"]

        for key in ids:
            if key not in answers:
                continue

            if key == photo_id:
                value = ""
            else:
                value = answers[key]["textAnswers"]["answers"][0]["value"]

            if key not in title_ordered_responses:
                title_ordered_responses[key] = {name: value}
            else:
                title_ordered_responses[key][name] = value

    # Construct email
    email = f"""
<html><head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE-edge">
<meta name="viewpoint" content="width=device.width, initial-scale=1.0">
<title>{config["name"]}</title>
</head><body>\n"""
    email += f'<h1>{config["name"]} Issue {config["issue"]}</h1>\n'
    email += f'<p>{config["text"]}</p>\n'

    for key, responses in title_ordered_responses.items():
        title = id_to_title[key]
        email += f"<h1>{title}</h1>\n"
        for name, response in responses.items():
            email += f"<h2>{name}</h2>\n"

            if key == photo_id and name in image_filepaths:
                caption = ""
                if name in captions:
                    caption = captions[name]

                email += f'<img src="cid:{name.replace(" ", "")}" alt="{caption}" width="500px" />\n'
                email += f'<p>{caption}</p>\n'
            else:
                email += f"<p>{response}</p>\n"

    email += "</body><html>\n"

    return email, image_filepaths


def generate_email_request(config, request_type: str):
    email = f"""
<html><head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE-edge">
<meta name="viewpoint" content="width=device.width, initial-scale=1.0">
<title>{config["name"]}</title>
</head><body>\n"""
    email += f'<h1>Submit Your {request_type.title()} for Issue {config["issue"]}</h1>\n'
    email += f'<p>{config["text"]}</p><br/>\n'
    email += f'<a href="{config["link"][request_type]}">Submit your {request_type} here!</p>\n'
    email += "</body><html>\n"

    return email

def send_email(body, images, config):
    message = MIMEMultipart("alternative")
    message["Subject"] = f'{config["name"]} Issue {config["issue"]}'

    if (config["debug"]):
        message["To"] = config["email"]
    else:
        message["To"] = ', '.join(config["addresses"])

    message["From"] = config["email"]

    text = "If you are reading this, please contact me."

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(body, "html")

    message.attach(part1)
    message.attach(part2)

    for idx, filepath in images.items():
        image_bytes = download_image(filepath)
        msg_image = MIMEImage(image_bytes.read())

        msg_image.add_header('Content-ID', f'<{idx.replace(" ", "")}>')
        message.attach(msg_image)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", PORT, context=context) as server:
        server.login(config["email"], config["password"])
        if config["debug"]:
            server.sendmail(
                config["email"], config["email"], message.as_string()
            )
        else:
            server.sendmail(
                config["email"], config["addresses"], message.as_string()
            )

if __name__=='__main__':
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
            config["password"] = args.password
            config["debug"] = args.debug
        except yaml.YAMLError as e:
            print(e)
            quit()

    with tempfile.NamedTemporaryFile(suffix=".txt") as tf:
        # Open editor to write message
        if args.question:
            tf.write(b"Time to submit your questions!")
        elif args.answer:
            tf.write(b"Time to submit your responses!")
        else:
            tf.write(b"Hope you have all had a wonderful month!")

        tf.flush()
        subprocess.call([EDITOR, tf.name])

        # process message
        tf.seek(0)
        config["text"] = tf.read().decode("utf-8")
        os.remove(tf.name)

    with open(f'{config["folder"]}/emails.txt', "r") as addr_file:
        config["addresses"] = [addr.replace("\n", "") for addr in addr_file.readlines()]

    if args.question:
        email = generate_email_request(config, "question")
        images = {}
    elif args.answer:
        email = generate_email_request(config, "answer")
        images = {}
    else:
        email, images = generate_newsletter(config)

    send_email(email, images, config)
