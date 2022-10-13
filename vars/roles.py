from enum import Enum
from enum import auto

class Roles(Enum):
    MEMBER = auto()
    ADMIN = auto()
    OWNER = auto()