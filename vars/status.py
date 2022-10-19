from enum import Enum, auto

class Status(Enum):
    PUBLISHED = auto()
    DRAFT = auto()
    PRIVATE = auto()