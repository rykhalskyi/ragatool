from sqlite3 import Connection
from typing import Optional, Dict
from app.crud import crud_setting
from app.schemas.setting import SettingsName, Setting, SettingCreate # Added SettingCreate

class SettingsManager:
    _cache: Dict[SettingsName, str]

    def __init__(self, db: Connection):
        self.db = db
        self._cache = {}
        self._load_settings()

    def _load_settings(self):
        settings_list = crud_setting.get_settings(self.db)
        for setting in settings_list:
            try:
                setting_name = SettingsName(setting.name)
                self._cache[setting_name] = setting.value
            except ValueError:
                print(f"Warning: Setting '{setting.name}' from DB does not have a corresponding SettingsName enum member.")

    def get_setting(self, name: SettingsName) -> Optional[str]:
        return self._cache.get(name)

    def set_setting(self, name: SettingsName, value: str):
        setting_create = SettingCreate(name=name.value, value=value)
        crud_setting.update_settings(self.db, [setting_create])
        self._cache[name] = value

    def check(self, name: SettingsName, value: str) -> bool:
        return self.get_setting(name) == value.lower() 
    
    def get_setting_int(self, name: SettingsName, default_value: int) -> int:
        try:
            setting = self.get_setting(name)
            if setting == None:
                return default_value
            
            return int(setting)
        except (ValueError, TypeError):
            return default_value

            
            
