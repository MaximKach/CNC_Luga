import logging
import telebot
import os
from handlers import register_handlers
from flask import Flask
import threading

# Настраиваем логирование для отладки
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
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

# Создаём Flask-приложение для health check
app = Flask(__name__)

@app.route('/')
def health_check():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8000)

# Запускаем бота
if __name__ == "__main__":
    logging.info("Бот запущен...")
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    try:
        bot.polling(none_stop=True)  # Запускаем бота в режиме постоянного опроса
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")