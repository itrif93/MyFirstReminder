# test.py
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import widget

class TestReminderWidget:
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.widget = reminder_widget.ReminderWidget("https://drive.google.com/uc?export=download&id=1YAOp8GZr1W3AIeN4VY3TwjG1SL22hCnb")
    
    @patch('reminder_widget.requests.get')
    def test_download_reminders_success(self, mock_get):
        """Тест успешной загрузки напоминаний с Google Drive"""
        # Настраиваем mock
        mock_response = Mock()
        mock_response.json.return_value = [{"day": 10, "message": "Тест"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.widget.download_reminders()
        
        assert result == [{"day": 10, "message": "Тест"}]
        mock_get.assert_called_once_with("https://drive.google.com/uc?export=download&id=1YAOp8GZr1W3AIeN4VY3TwjG1SL22hCnb", timeout=10)
    
    @patch('reminder_widget.requests.get')
    def test_download_reminders_network_error(self, mock_get):
        """Тест обработки ошибки сети"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        result = self.widget.download_reminders()
        
        assert result is None
    
    def test_parse_reminders_empty_data(self):
        """Тест парсинга пустых данных"""
        result = self.widget.parse_reminders(None)
        assert result == []
        
        result = self.widget.parse_reminders([])
        assert result == []
    
    def test_parse_reminders_no_matching_day(self):
        """Тест парсинга когда нет совпадений по дню"""
        test_data = [
            {"day": 15, "message": "Тест 1"},
            {"day": 20, "message": "Тест 2"}
        ]
        
        # Мокаем текущий день (предположим, что сегодня 10-е)
        with patch('reminder_widget.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 10
            mock_datetime.now.return_value = mock_now
            
            result = self.widget.parse_reminders(test_data)
        
        assert result == []
    
    def test_parse_reminders_matching_day(self):
        """Тест парсинга когда есть совпадения по дню"""
        test_data = [
            {"day": 10, "message": "Сегодняшнее напоминание"},
            {"day": 15, "message": "Будущее напоминание"},
            {"day": 10, "message": "Еще одно сегодняшнее"}
        ]
        
        # Мокаем текущий день (сегодня 10-е)
        with patch('reminder_widget.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 10
            mock_datetime.now.return_value = mock_now
            
            result = self.widget.parse_reminders(test_data)
        
        assert len(result) == 2
        assert "Сегодняшнее напоминание" in result
        assert "Еще одно сегодняшнее" in result
        assert "Будущее напоминание" not in result
    
    @patch('reminder_widget.notification.notify')
    def test_show_notification_success(self, mock_notify):
        """Тест успешного показа уведомления"""
        mock_notify.return_value = None
        
        result = self.widget.show_notification("Тестовое сообщение")
        
        assert result is True
        mock_notify.assert_called_once()
    
    @patch('reminder_widget.ReminderWidget.download_reminders')
    @patch('reminder_widget.ReminderWidget.show_notification')
    @patch('reminder_widget.time.sleep')
    def test_check_reminders_integration(self, mock_sleep, mock_show, mock_download):
        """Интеграционный тест всей цепочки проверки напоминаний"""
        # Настраиваем моки
        test_data = [
            {"day": 10, "message": "Напоминание 1"},
            {"day": 15, "message": "Напоминание 2"},
            {"day": 10, "message": "Напоминание 3"}
        ]
        mock_download.return_value = test_data
        mock_show.return_value = True
        
        # Мокаем текущую дату
        with patch('reminder_widget.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 10
            mock_datetime.now.return_value = mock_now
            
            result = self.widget.check_reminders()
        
        # Проверяем результаты
        assert len(result) == 2
        assert "Напоминание 1" in result
        assert "Напоминание 3" in result
        assert mock_show.call_count == 2