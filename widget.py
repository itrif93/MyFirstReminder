import requests
from plyer import notification
import json
from datetime import datetime
import time
import schedule

# Конфигурация (поменяй эти значения на свои!)
URL_TO_JSON = "https://drive.google.com/uc?export=download&id=1YAOp8GZr1W3AIeN4VY3TwjG1SL22hCnb"  # <-- Вставь сюда свою ссылку!
CHECK_TIME = "09:30"  # Время ежедневной проверки (ЧЧ:ММ)

def check_reminders():
    """Основная функция: загружает файл, проверяет даты и показывает уведомления"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Загружаю файл с напоминаниями...")
        
        # Загружаем файл по сети
        response = requests.get(URL_TO_JSON)
        response.raise_for_status()  # Проверяем, нет ли ошибок HTTP (например, 404)
        
        # Парсим JSON
        reminders = response.json()
        
        # Получаем текущее число месяца
        today_day = datetime.now().day
        print(f"Сегодня {today_day}-е число. Ищу напоминания...")
        
        # Проходим по всем напоминаниям из файла
        for reminder in reminders:
            if reminder['day'] == today_day:
                message = reminder['message']
                print(f"Найдено напоминание: {message}")
                
                # Показываем уведомление с помощью plyer
                notification.notify(
                    title='Ваше ежедневное напоминание!',  # Заголовок уведомления
                    message=message,                       # Текст из файла
                    app_name='Мой Виджет Напоминаний',     # Название приложения
                    timeout=10,                            # Уведомление будет видно 10 секунд
                    # toast=True  # Раскомментировать для стиля "Toast" в Windows 10/11
                )
                # Делаем небольшую паузу между уведомлениями, если их несколько
                time.sleep(2)
                
        print("Проверка завершена.\n")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке файла из интернета: {e}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при разборе JSON. Проверь формат файла: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")

# Планируем задачу
def main():
    print(f"Виджет напоминаний запущен! Проверка ежедневно в {CHECK_TIME}")
    print("Для остановки нажми Ctrl+C\n")
    
    # Планируем выполнение функции check_reminders каждый день в заданное время
    schedule.every().day.at(CHECK_TIME).do(check_reminders)
    
    # Также выполняем проверку сразу при запуске (можно закомментировать, если не нужно)
    check_reminders()
    
    # Бесконечный цикл для работы планировщика
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем расписание каждую минуту

# Запускаем программу
if __name__ == "__main__":
    main()
