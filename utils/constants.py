from enum import Enum


LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class State(Enum):
    Question = 0
    Answer = 1
    Publish = 2
