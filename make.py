import smtplib, ssl, csv, base64
from getpass import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

#from googleapiclient.discovery import build
#from googleapiclient.http import MediaIoBaseDownload
#from google_auth_oauthlib.flow import InstalledAppFlow
#from io import BytesIO

PORT = 465
PASSWORD = getpass()
SENDER_EMAIL = input("Email: ")
NEWSLETTER = input("Newsletter name: ")
FOLDER = input("Newsletter folder: ")
ISSUE = input("Issue number: ")
PREAMBLE = input("Preamble: ")
#PHOTO_ID = input("photo id: ")


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


def generate_email():
    # Get the data in a nice format
    email_addresses = []
    image_filepaths = {}
    title_ordered_responses = {}
    captions = {}
    with open(f"{FOLDER}/issue_{ISSUE}.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email_addresses.append(row["Email address"])
            name = row["Name"]
            for key, item in row.items():
                if key not in ["Name", "Email address", "Timestamp", "❓Submit A Question", "✍️ Caption"]:
                    value = item

                    if key in ["📸 Photo Wall"]:
                        idx = item.split("id=")[-1]
                        image_filepaths[idx] = f"{name}.jpg"
                        value = idx

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
<title>{NEWSLETTER}</title>
</head><body>\n"""
    email += f"<h1>{NEWSLETTER} Issue {ISSUE}</h1>\n"
    email += f"<p>{PREAMBLE}</p>\n"

    for title, responses in title_ordered_responses.items():
        email += f"<h1>{title}</h1>\n"
        for name, response in responses.items():
            email += f"<h2>{name}</h2>\n"

            if title in ["📸 Photo Wall"]:
                caption = captions[name]

                email += f'<img src="cid:{response}" alt="{caption}" width="500" />'
                email += f'<p>{caption}</p>'
            else:
                email += f"<p>{response}</p>\n"

    email += "</body><html>\n"

    return email, email_addresses, image_filepaths


def send_email(body, addresses, images):
    message = MIMEMultipart("alternative")
    message["Subject"] = f"{NEWSLETTER} Issue {ISSUE}"
    message["From"] = SENDER_EMAIL
    message["To"] = SENDER_EMAIL
#    message["To"] = ', '.join(addresses)

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
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(
            SENDER_EMAIL, SENDER_EMAIL, message.as_string()
#            SENDER_EMAIL, addresses, message.as_string()
        )

email, addresses, images = generate_email()

# with open("test.html", "w") as out:
#     out.write(email)

send_email(email, addresses, images)
