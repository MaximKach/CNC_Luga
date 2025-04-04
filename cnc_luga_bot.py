import logging
import telebot
from config import TOKEN
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

# Инициализируем бота с токеном из config.py
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