import sqlite3
from typing import List
from app.schemas.setting import SettingCreate, Setting

def get_settings(db: sqlite3.Connection) -> List[Setting]:
    cursor = db.execute("SELECT name, value, description FROM settings")
    db.row_factory = sqlite3.Row
    settings_rows = cursor.fetchall()
    return [Setting(**row) for row in settings_rows]

def update_settings(db: sqlite3.Connection, settings: List[SettingCreate]):
    cursor = db.cursor()
    cursor.executemany(
        "UPDATE settings SET value = :value WHERE name = :name",
        [setting.model_dump() for setting in settings],
    )
    db.commit()

def create_setting(db: sqlite3.Connection, setting: SettingCreate):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO settings (name, value) VALUES (?, ?)",
        (setting.name, setting.value)
    )
    db.commit()
