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
application = None

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Произошла ошибка: {context.error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )

# Подключаем все обработчики из handlers.py
async def init_bot():
    global application
    if application is not None:
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    register_handlers(application)
    
    # Регистрация обработчиков
    from handlers import start, help_command, menu, handle_message
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Инициализация и запуск приложения
    await application.initialize()
    await application.start()

# Инициализируем бота при запуске Flask-приложения
@app.before_first_request
async def before_first_request():
    await init_bot()

# Эндпоинт для инициализации бота
@app.route('/init', methods=['GET'])
async def init():
    await init_bot()
    return "Bot initialized"

# Эндпоинт для проверки состояния бота
@app.route('/health', methods=['GET'])
async def health():
    if application is None:
        await init_bot()
    return "Bot is running"

# Health check для проверки работоспособности
@app.route('/')
async def health_check():
    logger.info("Получен запрос на проверку работоспособности")
    if application is None:
        await init_bot()
    return "OK"

# Webhook-эндпоинт для Telegram с токеном бота в URL
@app.route('/8161940788:AAE2l_4-4ZEovz2ukD4NF1IeAmHe_9emUiQ', methods=['POST'])
async def webhook():
    logger.info("Получен webhook запрос")
    if request.method == "POST":
        try:
            if application is None:
                await init_bot()
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
        if application is None:
            await init_bot()
        webhook_url = "https://755d-109-172-30-15.ngrok-free.app/8161940788:AAE2l_4-4ZEovz2ukD4NF1IeAmHe_9emUiQ"
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