# tests/test.py
import sys
import os
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import requests

# Добавляем родительскую директорию в путь поиска модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from widget import ReminderWidget

class TestReminderWidget:
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.widget = ReminderWidget("https://drive.google.com/uc?export=download&id=1YAOp8GZr1W3AIeN4VY3TwjG1SL22hCnb")
    
    @patch('widget.requests.get')
    def test_download_reminders_with_retry_success(self, mock_get):
        """Тест успешной загрузки напоминаний с Google Drive"""
        # Настраиваем mock
        mock_response = Mock()
        mock_response.json.return_value = [{"day": 10, "message": "Тест"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Мокаем wait_for_internet чтобы сразу возвращать True
        with patch.object(self.widget, 'wait_for_internet', return_value=True):
            result = self.widget.download_reminders_with_retry()
        
        assert result == [{"day": 10, "message": "Тест"}]
        mock_get.assert_called_once_with("https://drive.google.com/uc?export=download&id=1YAOp8GZr1W3AIeN4VY3TwjG1SL22hCnb", timeout=15)
    
    @patch('widget.requests.get')
    def test_download_reminders_with_retry_network_error(self, mock_get):
        """Тест обработки ошибки сети"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        # Мокаем wait_for_internet чтобы сразу возвращать True
        with patch.object(self.widget, 'wait_for_internet', return_value=True):
            result = self.widget.download_reminders_with_retry()
        
        assert result is None
    
    @patch('widget.requests.get')
    def test_download_reminders_with_retry_no_internet(self, mock_get):
        """Тест когда интернет недоступен"""
        # Мокаем wait_for_internet чтобы возвращать False (интернет недоступен)
        with patch.object(self.widget, 'wait_for_internet', return_value=False):
            result = self.widget.download_reminders_with_retry()
        
        assert result is None
        mock_get.assert_not_called()  # Запрос не должен выполняться
    
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
        with patch('widget.datetime') as mock_datetime:
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
        with patch('widget.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 10
            mock_datetime.now.return_value = mock_now
            
            result = self.widget.parse_reminders(test_data)
        
        assert len(result) == 2
        assert "Сегодняшнее напоминание" in result
        assert "Еще одно сегодняшнее" in result
        assert "Будущее напоминание" not in result
    
    @patch('widget.notification.notify')
    def test_show_notification_success(self, mock_notify):
        """Тест успешного показа уведомления"""
        mock_notify.return_value = None
        
        result = self.widget.show_notification("Тестовое сообщение")
        
        assert result is True
        mock_notify.assert_called_once()
    
    @patch('widget.ReminderWidget.download_reminders_with_retry')
    @patch('widget.ReminderWidget.show_notification')
    def test_check_reminders_and_exit_with_reminders(self, mock_show, mock_download):
        """Тест проверки напоминаний когда они есть"""
        # Настраиваем моки
        test_data = [
            {"day": 10, "message": "Напоминание 1"},
            {"day": 10, "message": "Напоминание 2"}
        ]
        mock_download.return_value = test_data
        mock_show.return_value = True
        
        # Мокаем текущую дату
        with patch('widget.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 10
            mock_datetime.now.return_value = mock_now
            
            result = self.widget.check_reminders_and_exit()
        
        # Проверяем результаты
        assert result is True  # Должен вернуть True для закрытия
        assert mock_show.call_count == 2  # Должны показать 2 уведомления
    
    @patch('widget.ReminderWidget.download_reminders_with_retry')
    def test_check_reminders_and_exit_no_reminders(self, mock_download):
        """Тест проверки напоминаний когда их нет"""
        # Настраиваем моки
        test_data = [
            {"day": 15, "message": "Напоминание 1"},
            {"day": 20, "message": "Напоминание 2"}
        ]
        mock_download.return_value = test_data
        
        # Мокаем текущую дату
        with patch('widget.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.day = 10  # Сегодня 10-е, а напоминания на 15-е и 20-е
            mock_datetime.now.return_value = mock_now
            
            result = self.widget.check_reminders_and_exit()
        
        # Проверяем результаты
        assert result is True  # Должен вернуть True для закрытия
    
    @patch('widget.ReminderWidget.download_reminders_with_retry')
    def test_check_reminders_and_exit_download_failed(self, mock_download):
        """Тест проверки напоминаний когда загрузка не удалась"""
        mock_download.return_value = None  # Загрузка не удалась
        
        result = self.widget.check_reminders_and_exit()
        
        # Проверяем результаты
        assert result is False  # Должен вернуть False при ошибке

    @patch('widget.requests.get')
    def test_is_internet_available_success(self, mock_get):
        """Тест успешной проверки интернета"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.widget.is_internet_available()
        
        assert result is True
        mock_get.assert_called_once_with("https://www.google.com", timeout=10)
    
    @patch('widget.requests.get')
    def test_is_internet_available_failure(self, mock_get):
        """Тест неуспешной проверки интернета"""
        mock_get.side_effect = requests.exceptions.ConnectionError("No internet")
        
        result = self.widget.is_internet_available()
        
        assert result is False
    
    @patch('widget.ReminderWidget.is_internet_available')
    def test_wait_for_internet_immediate_success(self, mock_internet):
        """Тест ожидания интернета когда он сразу доступен"""
        mock_internet.return_value = True  # Интернет сразу доступен
        
        result = self.widget.wait_for_internet()
        
        assert result is True
        mock_internet.assert_called_once()
    
    @patch('widget.ReminderWidget.is_internet_available')
    @patch('widget.time.sleep')
    def test_wait_for_internet_after_retry(self, mock_sleep, mock_internet):
        """Тест ожидания интернета с несколькими попытками"""
        # Первые две проверки - нет интернета, третья - есть
        mock_internet.side_effect = [False, False, True]
        
        result = self.widget.wait_for_internet()
        
        assert result is True
        assert mock_internet.call_count == 3
        assert mock_sleep.call_count == 2  # Два раза ждем между проверками

def test_run_once_exits_normally():
    """Тест что run_once завершает работу"""
    widget = ReminderWidget("https://test.url")
    
    # Мокаем check_reminders_and_exit чтобы возвращать True (нормальное завершение)
    with patch.object(widget, 'check_reminders_and_exit', return_value=True):
        with patch('widget.sys.exit') as mock_exit:
            widget.run_once()
    
    mock_exit.assert_called_once_with(0)

def test_run_once_exits_with_error():
    """Тест что run_once завершается с ошибкой"""
    widget = ReminderWidget("https://test.url")
    
    # Мокаем check_reminders_and_exit чтобы возвращать False (ошибка)
    with patch.object(widget, 'check_reminders_and_exit', return_value=False):
        with patch('widget.sys.exit') as mock_exit:
            widget.run_once()
    
    mock_exit.assert_called_once_with(1)