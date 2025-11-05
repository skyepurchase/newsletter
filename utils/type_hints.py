from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class NewsletterConfig:
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

QuestionResponse = Tuple[str, str, str]
Response = Tuple[str, int, List[QuestionResponse]]
