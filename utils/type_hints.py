from pydantic.dataclasses import dataclass
from typing import List, Tuple


@dataclass
class NewsletterConfig:
    name: str
    email: str
    folder: str
    link: str
    issue: int
    defaults: List[Tuple[str, str]]


EmptyConfig = NewsletterConfig("", "", "", "", -1, [])


@dataclass
class MailerConfig:
    isQuestion: bool
    isAnswer: bool
    isSend: bool
    isManual: bool

    name: str
    email: str
    issue: int
    addresses: List[str]
    folder: str
    text: str
    link: str

    password: str

    debug: bool = False


@dataclass
class NewsletterToken:
    title: str
    folder: str
    id: int


QuestionResponse = Tuple[str, str, str]
Response = Tuple[str, int, List[QuestionResponse]]
