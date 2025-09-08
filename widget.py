# reminder_widget.py
import requests
from plyer import notification
import json
from datetime import datetime
import time
import schedule

class ReminderWidget:
    def __init__(self, direct_download_url):
        self.direct_download_url = direct_download_url
    
    def download_reminders(self):
        """Загружает JSON с напоминаниями из Google Drive"""
        try:
            print(f"Загружаю файл по ссылке: {self.direct_download_url}")
            response = requests.get(self.direct_download_url, timeout=10)
            response.raise_for_status()  # Проверяем ошибки HTTP
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при загрузке файла: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Ошибка при разборе JSON: {e}")
            print(f"Ответ сервера: {response.text[:200]}...")  # Покажем начало ответа для дебага
            return None
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке: {e}")
            return None
    
    def parse_reminders(self, reminders_data):
        """Парсит напоминания и возвращает те, которые актуальны на сегодня"""
        if not reminders_data:
            return []
        
        today_day = datetime.now().day
        today_reminders = []
        
        for reminder in reminders_data:
            if reminder.get('day') == today_day:
                today_reminders.append(reminder.get('message', ''))
        
        return today_reminders
    
    def show_notification(self, message):
        """Показывает уведомление"""
        try:
            notification.notify(
                title='Ваше ежедневное напоминание!',
                message=message,
                app_name='Мой Виджет Напоминаний',
                timeout=10
            )
            return True
        except Exception as e:
            print(f"Ошибка при показе уведомления: {e}")
            return False
    
    def check_reminders(self):
        """Основная функция проверки напоминаний"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверяю напоминания...")
        
        reminders_data = self.download_reminders()
        if reminders_data is None:
            print("Не удалось загрузить напоминания")
            return []
        
        today_reminders = self.parse_reminders(reminders_data)
        
        if today_reminders:
            print(f"Найдено напоминаний на сегодня: {len(today_reminders)}")
            for message in today_reminders:
                print(f"Показываю уведомление: {message}")
                self.show_notification(message)
                time.sleep(1)  # Пауза между уведомлениями
        else:
            print("На сегодня напоминаний нет")
        
        return today_reminders

def main():
    # Жестко зашитая прямая ссылка для скачивания с Google Disk
    DIRECT_DOWNLOAD_URL = "https://drive.google.com/uc?export=download&id=1YAOp8GZr1W3AIeN4VY3TwjG1SL22hCnb"
    CHECK_TIME = "09:30"
    
    widget = ReminderWidget(DIRECT_DOWNLOAD_URL)
    
    print(f"Виджет напоминаний запущен!")
    print(f"Проверка ежедневно в {CHECK_TIME}")
    print("Для остановки нажмите Ctrl+C\n")
    
    # Планируем выполнение
    schedule.every().day.at(CHECK_TIME).do(widget.check_reminders)
    
    # Проверка при запуске
    widget.check_reminders()
    
    # Бесконечный цикл
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nВиджет остановлен пользователем")

if __name__ == "__main__":
    main()