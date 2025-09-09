# widget.py
import requests
from plyer import notification
import json
from datetime import datetime
import time
import schedule

class ReminderWidget:
    def __init__(self, direct_download_url):
        self.direct_download_url = direct_download_url
        self.internet_check_delay = 60  # Ждем 1 минуту между проверками интернета
        self.internet_check_timeout = 10  # Таймаут проверки интернета в секундах
        self.download_timeout = 15  # Таймаут загрузки файла в секундах
    
    def is_internet_available(self):
        """Проверяет доступность интернета"""
        try:
            # Пробуем подключиться к надежному сайту
            response = requests.get(
                "https://www.google.com", 
                timeout=self.internet_check_timeout
            )
            return response.status_code == 200
        except (requests.exceptions.RequestException,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError):
            return False
        except Exception as e:
            print(f"Неожиданная ошибка при проверке интернета: {e}")
            return False
    
    def wait_for_internet(self):
        """Ожидает доступности интернета"""
        print("Ожидание подключения к интернету...")
        
        while True:
            if self.is_internet_available():
                print("Интернет доступен!")
                return True
            
            print(f"Интернет недоступен. Повторная проверка через {self.internet_check_delay} секунд...")
            time.sleep(self.internet_check_delay)
            
            # Проверяем, не нужно ли выйти из бесконечного цикла
            # (например, по сигналу завершения программы)
            # В реальном приложении можно добавить флаг для остановки
    
    def download_reminders_with_retry(self):
        """Загружает JSON с напоминаниями после проверки интернета"""
        # Сначала ждем интернет
        if not self.wait_for_internet():
            print("Не удалось дождаться интернета")
            return None
        
        # Когда интернет есть, пытаемся скачать файл
        try:
            print("Загружаю файл с напоминаниями...")
            response = requests.get(
                self.direct_download_url, 
                timeout=self.download_timeout
            )
            response.raise_for_status()
            
            print("Файл успешно загружен!")
            return response.json()
            
        except requests.exceptions.Timeout:
            print("Таймаут при загрузке файла. Интернет может быть медленным.")
            return None
        except requests.exceptions.ConnectionError:
            print("Ошибка подключения. Интернет мог пропасть во время загрузки.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при загрузке файла: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Ошибка формата JSON: {e}")
            return None
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке: {e}")
            return None
    
    def download_reminders(self):
        """Основной метод загрузки (для обратной совместимости)"""
        return self.download_reminders_with_retry()
    
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
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Запуск проверки напоминаний...")
        
        reminders_data = self.download_reminders_with_retry()
        if reminders_data is None:
            print("Не удалось загрузить напоминания")
            return []
        
        today_reminders = self.parse_reminders(reminders_data)
        
        if today_reminders:
            print(f"Найдено напоминаний на сегодня: {len(today_reminders)}")
            for message in today_reminders:
                print(f"Показываю уведомление: {message}")
                self.show_notification(message)
                time.sleep(1)
        else:
            print("На сегодня напоминаний нет")
        
        return today_reminders

def main():
    # Жестко зашитая прямая ссылка для скачивания с Google Disk
    DIRECT_DOWNLOAD_URL = "https://drive.google.com/uc?export=download&id=1YAOp8GZr1W3AIeN4VY3TwjG1SL22hCnb"
    CHECK_TIME = "09:00"
    
    widget = ReminderWidget(DIRECT_DOWNLOAD_URL)
    
    print(f"Виджет напоминаний запущен!")
    print(f"Задержка между проверками интернета: {widget.internet_check_delay} секунд")
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