import logging
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
    level=logging.DEBUG,  # Изменяем уровень на DEBUG для более подробных логов
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получаем токен из переменных окружения
TELEGRAM_TOKEN = os.getenv("TBOT_TOKEN")

# Проверяем, что токен загружен
if not TELEGRAM_TOKEN:
    logger.critical("TBOT_TOKEN не найден в переменных окружения")
    raise ValueError("TBOT_TOKEN не найден в переменных окружения")

# Создаём Flask-приложение
app = Flask(__name__)

# Создание приложения Telegram
app_bot = None

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Произошла ошибка: {context.error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )

# Подключаем все обработчики из handlers.py
def init_bot():
    global app_bot
    if app_bot is not None:
        return
    
    app_bot = Application.builder().token(TELEGRAM_TOKEN).build()
    register_handlers(app_bot)
    
    # Регистрация обработчиков
    from handlers import start, help_command, menu, handle_message
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("menu", menu))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    app_bot.add_error_handler(error_handler)

# Инициализируем бота при запуске Flask-приложения
with app.app_context():
    init_bot()

# Эндпоинт для инициализации бота
@app.route('/init', methods=['GET'])
def init():
    init_bot()
    return "Bot initialized"

# Эндпоинт для проверки состояния бота
@app.route('/health', methods=['GET'])
def health():
    if app_bot is None:
        init_bot()
    return "Bot is running"

# Health check для Koyeb
@app.route('/')
async def health_check():
    logger.info("Получен запрос на проверку работоспособности")
    if app_bot is None:
        init_bot()
    return "OK"

# Webhook-эндпоинт для Telegram
@app.route('/webhook', methods=['POST'])
async def webhook():
    logger.info("Получен webhook запрос")
    if request.method == "POST":
        try:
            if app_bot is None:
                init_bot()
            update = Update.de_json(request.get_json(), app_bot.bot)
            await app_bot.process_update(update)
            return jsonify({"status": "ok"})
        except Exception as e:
            logger.error(f"Ошибка при обработке webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    return "OK"

# Эндпоинт для установки webhook
@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    try:
        if app_bot is None:
            init_bot()
        webhook_url = request.args.get('url')
        if not webhook_url:
            return "URL не указан", 400
        
        await app_bot.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook успешно установлен на {webhook_url}")
        return "Webhook установлен"
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return str(e), 500

if __name__ == "__main__":
    logger.info("Бот запущен...")
    try:
        init_bot()
        app.run(host='0.0.0.0', port=8000)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)