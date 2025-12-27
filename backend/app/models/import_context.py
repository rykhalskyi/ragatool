from sqlite3 import Connection
from typing import List

from app.internal.message_hub import MessageHub
from app.internal.settings_manager import SettingsManager
from app.schemas.imports import Import
from app.schemas.setting import Setting


class ImportContext:
    dbConnection: Connection
    messageHub: MessageHub
    settings: SettingsManager
    parameters: Import

    def __init__(self, dbConnection: Connection, messageHub: MessageHub, parameters: Import):
        self.db = dbConnection
        self.messageHub = messageHub
        self.settings = SettingsManager(dbConnection)
        self.parameters = parameters
