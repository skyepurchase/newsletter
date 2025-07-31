import os
from datetime import datetime

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO


FORM_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
CONFIG_TIME_FORMAT = "%Y%m%d"


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
            try:
                creds.refresh(Request())
            except:
                print("Token failed, regenerating token")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build(*args, credentials=creds)


def get_form_data(form_id: str, cutoff: str):
    cutoff_date = datetime.strptime(
        cutoff,
        CONFIG_TIME_FORMAT
    )

    service = create_service('forms', 'v1')
    form = service.forms().get(formId=form_id).execute()
    answers = service.forms().responses().list(formId=form_id).execute()

    name_id = ""
    caption_id = ""
    photo_id = ""
    ids = []
    id_to_title = {}

    for question in form["items"]:
        question_id = question["questionItem"]["question"]["questionId"]
        id_to_title[question_id] = question["title"]

        if question["title"] == "Name":
            name_id = question_id
        elif question["title"] == "✍️ Caption":
            caption_id = question_id
        elif question["title"] != "Timestamp":
            ids.append(question_id)
            if question["title"] == "📸 Photo Wall":
                photo_id = question_id

    # Extract responses
    image_filepaths = {}
    title_ordered_responses = {}
    captions = {}

    for response in answers["responses"]:
        date = datetime.strptime(
            response['lastSubmittedTime'],
            FORM_TIME_FORMAT
        )
        if date < cutoff_date:
            continue

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

    return (
        title_ordered_responses,
        id_to_title,
        image_filepaths,
        photo_id,
        captions
    )


def get_questions(form_id: str, cutoff: str) -> list[str]:
    cutoff_date = datetime.strptime(
        cutoff,
        CONFIG_TIME_FORMAT
    )

    service = create_service('forms', 'v1')
    form = service.forms().get(formId=form_id).execute()
    question_request = service.forms().responses().list(formId=form_id).execute()

    name_id = ""
    text_id = ""

    id_to_title = {}
    for response_temp in form["items"]:
        curr_id = response_temp["questionItem"]["question"]["questionId"]
        id_to_title[curr_id] = response_temp["title"]

        if response_temp["title"] == "Name":
            name_id = curr_id
        elif response_temp["title"] == "Question":
            text_id = curr_id

    questions = []
    for response in question_request["responses"]:
        # Skip question sent before the recent call for questions
        date = datetime.strptime(
            response['lastSubmittedTime'],
            FORM_TIME_FORMAT
        )
        if date < cutoff_date:
            continue

        question = response["answers"]

        name = question[name_id]["textAnswers"]["answers"][0]["value"].rstrip()
        text = question[text_id]["textAnswers"]["answers"][0]["value"]
        questions.append(f"{name}: {text}")

    return questions


def update_form(form_id: str, questions: list[str]) -> None:
    # Get current form
    service = create_service('forms', 'v1')
    form = service.forms().get(formId=form_id).execute()

    # Delete old questions
    requests = []
    for i, question in enumerate(form['items']):
        # TODO: Don't hard code this
        if question['title'] not in [
            "Name",
            "🌤 One Good Thing",
            "💭 On Your Mind",
            "👀 Check It Out",
            "📸 Photo Wall",
            "✍️ Caption"
        ]:
            requests.append({
                "deleteItem": {
                    "location": { "index": i }
                }
            })
    # Delete such that indices don't get messed up
    requests.reverse()

    # Add new questions
    for i, question in enumerate(questions):
        # TODO: More flexible approach?
        request = {
            "createItem": {
                "item": {
                    "title": question,
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": { "index": i+1 }
            }
        }
        requests.append(request)

    requests.append({
        "updateFormInfo": {
            "info": {
                "description": "To be sent out soon ~still working on getting this fully dynamic~"
            },
            "updateMask": "description"
        }
    })

    update = {
        "includeFormInResponse": False,
        "requests": requests
    }

    service.forms().batchUpdate(
        formId=form_id, body=update
    ).execute()


def download_image(file_id: str) -> BytesIO:
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
