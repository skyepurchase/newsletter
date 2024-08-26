import smtplib, ssl, csv, base64, yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from argparse import ArgumentParser

#from googleapiclient.discovery import build
#from googleapiclient.http import MediaIoBaseDownload
#from google_auth_oauthlib.flow import InstalledAppFlow
#from io import BytesIO

PORT = 465


#SCOPES = ['https://www.googleapis.com/auth/drive']

#def create_service():
#    flow = InstalledAppFlow.from_client_config('credentials.json', SCOPES)
#    creds = flow.run_local_server(port=0)
#    return build('drive', 'v3', credentials=creds)
#
#def download_file(service, file_id, file_name):
#    request = service.files().get_media(fileId=file_id)
#    fh = BytesIO()
#    downloader = MediaIoBaseDownload(fd=fh, request=request)
#
#    done = False
#    while not done:
#        status, done = downloader.next_chunk()
#        print(f"Download Progress: {int(status.progress() * 100)}")
#
#    fh.seek(0)
#    with open(file_name, 'wb') as f:
#        f.write(fh.read())
#        f.close()


def convert_image(filepath: str) -> bytes:
    with open(filepath, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read())
        return encoded_string


def generate_newsletter(config):
    # Get the data in a nice format
    image_filepaths = {}
    title_ordered_responses = {}
    captions = {}
    with open(f'{config["folder"]}/issue_{config["issue"]}.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row["Name"]
            for key, item in row.items():
                if key not in ["Name", "Email address", "Timestamp", "❓Submit A Question", "✍️ Caption"]:
                    value = item

                    if key in ["📸 Photo Wall"]:
#                        idx = item.split("id=")[-1]
#                        image_filepaths[idx] = f"{name}.jpg"
                        image_filepaths[name] = f'{config["folder"]}/photos_issue_{config["issue"]}/{name.lower()}.jpg'
                        value = ""

                    if key not in title_ordered_responses:
                        title_ordered_responses[key] = {name: value}
                    else:
                        title_ordered_responses[key][name] = value

                if key in ["✍️ Caption"]:
                    captions[name] = item


    email = f"""
<html><head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE-edge">
<meta name="viewpoint" content="width=device.width, initial-scale=1.0">
<title>{config["name"]}</title>
</head><body>\n"""
    email += f'<h1>{config["name"]} Issue {config["issue"]}</h1>\n'
    email += f'<p>{config["text"]}</p>\n'

    for title, responses in title_ordered_responses.items():
        email += f"<h1>{title}</h1>\n"
        for name, response in responses.items():
            email += f"<h2>{name}</h2>\n"

            if title in ["📸 Photo Wall"]:
                caption = captions[name]

                email += f'<img src="cid:{name}" alt="{caption}" width="500px" />'
                email += f'<p>{caption}</p>'
            else:
                email += f"<p>{response}</p>\n"

    email += "</body><html>\n"

    return email, image_filepaths


def generate_question_request(config):
    email = f"""
<html><head>
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE-edge">
<meta name="viewpoint" content="width=device.width, initial-scale=1.0">
<title>{config["name"]}</title>
</head><body>\n"""
    email += f'<h1>❓Submit A Question for Issue {config["issue"]}</h1>\n'
    email += f'<p>{config["text"]}</p><br/>\n'
    email += f'<a href="{config["link"]}">Submit your question here!</p>\n'
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
        with open(filepath, 'rb') as img_file:
            msg_image = MIMEImage(img_file.read())

        msg_image.add_header('Content-ID', f'<{idx}>')
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

    args = args.parse_args()

    with open(args.config) as config_file:
        try:
            config = yaml.safe_load(config_file)
            config["password"] = args.password
            config["debug"] = args.debug
        except yaml.YAMLError as e:
            print(e)
            quit()

    with open(f'{config["folder"]}/emails.txt', "r") as addr_file:
        config["addresses"] = [addr.replace("\n", "") for addr in addr_file.readlines()]

    if args.question:
        email = generate_question_request(config)
        images = {}
    else:
        email, images = generate_newsletter(config)

    send_email(email, images, config)
