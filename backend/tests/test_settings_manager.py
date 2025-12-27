import unittest
from unittest.mock import MagicMock, patch
from app.internal.settings_manager import SettingsManager
from app.schemas.setting import SettingsName, Setting, SettingCreate
import app.crud.crud_setting as crud_setting_module
from enum import Enum

class TestSettingsManager(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self._initial_settings = [
            Setting(name=SettingsName.TWO_STEP_IMPORT.value, value="True", description=""),
            Setting(name="OtherSetting", value="SomeValue", description=""), # Example of another setting
        ]
        
        # Patch crud_setting functions
        self.get_settings_patch = patch('app.crud.crud_setting.get_settings', return_value=self._initial_settings)
        self.mock_get_settings = self.get_settings_patch.start()

        self.update_settings_patch = patch('app.crud.crud_setting.update_settings')
        self.mock_update_settings = self.update_settings_patch.start()

        self.settings_manager = SettingsManager(self.mock_db)

    def tearDown(self):
        self.get_settings_patch.stop()
        self.update_settings_patch.stop()

    def test_init_loads_settings(self):
        self.mock_get_settings.assert_called_once_with(self.mock_db)
        self.assertEqual(self.settings_manager._cache[SettingsName.TWO_STEP_IMPORT], "True")
        # Ensure that settings not in the enum are handled (skipped with a warning in current implementation)
        # Check that "OtherSetting" is not a key in the cache
        self.assertFalse(any(key for key in self.settings_manager._cache.keys() if key.value == "OtherSetting"))


    def test_get_setting_existing(self):
        value = self.settings_manager.get_setting(SettingsName.TWO_STEP_IMPORT)
        self.assertEqual(value, "True")

    def test_get_setting_non_existing(self):
        # Use the test-only enum member which is not in the initial mock data
        value = self.settings_manager.get_setting(SettingsName.FOR_TEST_ONLY)
        self.assertIsNone(value)


    def test_set_setting_updates_existing(self):
        new_value = "False"
        self.settings_manager.set_setting(SettingsName.TWO_STEP_IMPORT, new_value)
        
        self.mock_update_settings.assert_called_once_with(
            self.mock_db, 
            [SettingCreate(name=SettingsName.TWO_STEP_IMPORT.value, value=new_value)]
        )
        self.assertEqual(self.settings_manager._cache[SettingsName.TWO_STEP_IMPORT], new_value)

    def test_set_setting_new_setting(self):
        new_name = SettingsName.FOR_TEST_ONLY
        new_value = "New Value Content"
        
        self.settings_manager.set_setting(new_name, new_value)
        
        self.mock_update_settings.assert_called_once_with(
            self.mock_db,
            [SettingCreate(name=new_name.value, value=new_value)]
        )
        self.assertEqual(self.settings_manager._cache[new_name], new_value)
