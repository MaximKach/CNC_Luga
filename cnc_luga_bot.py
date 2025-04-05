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
    logging.info("Получен запрос на health check")
    return "OK", 200

# Webhook-эндпоинт для Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    logging.info("Получен webhook-запрос от Telegram")
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        logging.info(f"Получены данные: {json_string}")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        logging.info("Обновления обработаны")
        return 'OK', 200
    else:
        logging.warning("Неправильный тип контента")
        return 'Bad Request', 400

# Эндпоинт для установки webhook
@app.route('/set_webhook')
def set_webhook():
    webhook_url = f"https://ideological-jerrie-ka4-d4b11a76.koyeb.app/{TOKEN}"
    logging.info(f"Установка webhook на {webhook_url}")
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    if success:
        logging.info("Webhook успешно установлен")
        return f"Webhook set to {webhook_url}", 200
    else:
        logging.error("Не удалось установить webhook")
        return "Failed to set webhook", 500

if __name__ == "__main__":
    logging.info("Бот запущен...")
    app.run(host='0.0.0.0', port=8000)