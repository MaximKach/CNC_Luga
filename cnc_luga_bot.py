import logging
import telebot
from config import TOKEN
from handlers import register_handlers

# Настраиваем логирование для отладки
logging.basicConfig(level=logging.INFO)

# Инициализируем бота с токеном из config.py
bot = telebot.TeleBot(TOKEN)

# Подключаем все обработчики из handlers.py
register_handlers(bot)

# Запускаем бота
if __name__ == "__main__":
    bot.polling(none_stop=True)