import logging
import telebot
import os
from handlers import register_handlers
from flask import Flask, request

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

# Создаём Flask-приложение
app = Flask(__name__)

# Health check для Koyeb
@app.route('/')
def health_check():
    return "OK", 200

# Webhook-эндпоинт для Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Bad Request', 400

# Эндпоинт для установки webhook
@app.route('/set_webhook')
def set_webhook():
    webhook_url = f"https://идеологический-jerrie-ka4-d4b11a76.koyeb.app/{TOKEN}"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    if success:
        return f"Webhook set to {webhook_url}", 200
    else:
        return "Failed to set webhook", 500

if __name__ == "__main__":
    logging.info("Бот запущен...")