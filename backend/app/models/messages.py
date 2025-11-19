from enum import Enum

class MessageType(Enum):
    LOG = 1
    INFO = 2
    LOCK = 3
    UNLOCK = 4