import logging
import telebot
import os  # Добавляем модуль os для работы с переменными окружения
from handlers import register_handlers

# Настраиваем логирование для отладки
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),  # Логи будут записываться в файл bot.log
        logging.StreamHandler()  # И выводиться в консоль
    ]
)

# Получаем токен из переменных окружения
TOKEN = os.getenv("TBOT_TOKEN")

# Проверяем, что токен загружен
if not TOKEN:
    logging.error("❌ Ошибка: Не удалось загрузить TBOT_TOKEN из переменных окружения")
    raise ValueError("❌ Ошибка: Не удалось загрузить TBOT_TOKEN из переменных окружения")

# Инициализируем бота с токеном
bot = telebot.TeleBot(TOKEN)

# Подключаем все обработчики из handlers.py
register_handlers(bot)

# Запускаем бота
if __name__ == "__main__":
    logging.info("Бот запущен...")
    try:
        bot.polling(none_stop=True)  # Запускаем бота в режиме постоянного опроса
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")