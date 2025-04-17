import logging
import telebot
import os
import sys
import traceback
from handlers import register_handlers
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Настраиваем логирование для отладки
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получаем токен из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Проверяем, что токен загружен
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не найден в переменных окружения")
    raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения")

# Создаём Flask-приложение
app = Flask(__name__)

# Создание приложения Telegram
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Подключаем все обработчики из handlers.py
register_handlers(application)

# Регистрация обработчиков
application.add_handler(CommandHandler("start", register_handlers.start))
application.add_handler(CommandHandler("help", register_handlers.help_command))
application.add_handler(CommandHandler("menu", register_handlers.menu))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_handlers.handle_message))

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Произошла ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )

application.add_error_handler(error_handler)

# Health check для Koyeb
@app.route('/')
async def health_check():
    logger.info("Получен запрос на проверку работоспособности")
    return "OK"

# Webhook-эндпоинт для Telegram
@app.route('/webhook', methods=['POST'])
async def webhook():
    logger.info("Получен webhook запрос")
    if request.method == "POST":
        try:
            update = Update.de_json(request.get_json(), application.bot)
            await application.process_update(update)
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Ошибка при обработке webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    return "OK"

# Эндпоинт для установки webhook
@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    try:
        webhook_url = request.args.get('url')
        if not webhook_url:
            return "URL не указан", 400
        
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook успешно установлен на {webhook_url}")
        return "Webhook установлен"
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return str(e), 500

if __name__ == "__main__":
    logger.info("Бот запущен...")
    try:
        app.run(host='0.0.0.0', port=8000)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)