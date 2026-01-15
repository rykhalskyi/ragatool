import unittest
from unittest.mock import MagicMock, patch
from threading import Event
from app.models.url_import import UrlImport
from app.schemas.setting import SettingsName
from app.models.import_context import ImportContext

class TestUrlImport(unittest.TestCase):

    @patch('app.models.url_import.simple_crawler.simple_crawl')
    def test_import_data_with_valid_crawl_depth(self, mock_simple_crawl):
        # Arrange
        url_import = UrlImport()
        context = self._create_mock_context('2')
        cancel_event = Event()

        # Act
        async def run_test():
            await url_import.import_data('collection1', 'http://example.com', b'', context, cancel_event)
        
        import asyncio
        asyncio.run(run_test())

        # Assert
        mock_simple_crawl.assert_called_with('http://example.com', cancel_event, max_depth=2)

    @patch('app.models.url_import.simple_crawler.simple_crawl')
    def test_import_data_with_invalid_crawl_depth(self, mock_simple_crawl):
        # Arrange
        url_import = UrlImport()
        context = self._create_mock_context('invalid')
        cancel_event = Event()

        # Act
        async def run_test():
            await url_import.import_data('collection1', 'http://example.com', b'', context, cancel_event)
        
        import asyncio
        asyncio.run(run_test())

        # Assert
        mock_simple_crawl.assert_called_with('http://example.com', cancel_event, max_depth=1)

    @patch('app.models.url_import.simple_crawler.simple_crawl')
    def test_import_data_with_missing_crawl_depth(self, mock_simple_crawl):
        # Arrange
        url_import = UrlImport()
        context = self._create_mock_context(None)
        cancel_event = Event()

        # Act
        async def run_test():
            await url_import.import_data('collection1', 'http://example.com', b'', context, cancel_event)
        
        import asyncio
        asyncio.run(run_test())

        # Assert
        mock_simple_crawl.assert_called_with('http://example.com', cancel_event, max_depth=1)

    @patch('app.models.url_import.simple_crawler.simple_crawl')
    def test_step_1_with_valid_crawl_depth(self, mock_simple_crawl):
        # Arrange
        url_import = UrlImport()
        context = self._create_mock_context('3', two_step_import='True')
        cancel_event = Event()

        # Act
        async def run_test():
            await url_import.step_1('collection1', 'http://example.com', context, cancel_event)

        import asyncio
        asyncio.run(run_test())

        # Assert
        mock_simple_crawl.assert_called_with('http://example.com', cancel_event, max_depth=3)

    def _create_mock_context(self, crawl_depth_value, two_step_import='False'):
        mock_settings_manager = MagicMock()
        mock_settings_manager.get_setting.side_effect = lambda setting_name: crawl_depth_value if setting_name == SettingsName.CRAWL_DEPTH else two_step_import
        
        # Mock get_setting_int to convert crawl_depth_value to int
        def get_setting_int_side_effect(setting_name, default=1):
            if setting_name == SettingsName.CRAWL_DEPTH and crawl_depth_value is not None:
                try:
                    return int(crawl_depth_value)
                except (ValueError, TypeError):
                    return default
            return default
        
        mock_settings_manager.get_setting_int.side_effect = get_setting_int_side_effect
        
        mock_message_hub = MagicMock()
        
        context = MagicMock(spec=ImportContext)
        context.settings = mock_settings_manager
        context.messageHub = mock_message_hub
        context.parameters = MagicMock()
        
        return context

if __name__ == '__main__':
    unittest.main()
