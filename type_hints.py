from dataclasses import dataclass


@dataclass
class FormConfig:
    id: str
    cutoff: str
    link: str


@dataclass
class NewsletterConfig:
    isQuestion: bool
    isAnswer: bool
    isSend: bool

    name: str
    email: str
    issue: int
    addresses: list[str]
    folder: str
    text: str

    question: FormConfig
    answer: FormConfig

    password: str

    debug: bool = False
