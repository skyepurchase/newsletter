from dataclasses import dataclass


@dataclass
class NewsletterConfig:
    isQuestion: bool
    isAnswer: bool
    isSend: bool
    isManual: bool

    name: str
    email: str
    issue: int
    addresses: list[str]
    folder: str
    text: str
    link: str

    password: str

    debug: bool = False
