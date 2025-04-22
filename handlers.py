import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from gpt_api import yandex_gpt_request, yandex_gpt_request_async
from news import get_news, update_news
from reports import save_report
from users import add_user
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Изменяем уровень на DEBUG для более подробных логов
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("handlers.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Константы для состояний пользователя
USER_STATE_NONE = "none"
USER_STATE_VALERA = "valera"
USER_STATE_LEGAL = "legal"
USER_STATE_REPORT = "report"
USER_STATE_UPDATE_NEWS = "update_news"
USER_STATE_BROADCAST = "broadcast"

# Словарь для хранения истории диалогов пользователей
user_contexts = {}

# Создаём главное меню с кнопками
def main_menu():
    keyboard = [
        ["📸 Валера"],
        ["🔴 Аноним"],
        ["📋 Меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Создаём меню команд
def commands_menu():
    keyboard = [
        ["/start", "/help"],
        ["/news", "/contact"],
        ["↩️ Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user(update.effective_chat.id)
    # Сбрасываем контекст пользователя при старте
    user_contexts[update.effective_chat.id] = {"role": USER_STATE_NONE, "history": []}
    logger.info(f"Пользователь {update.effective_chat.id} запустил бота")
    
    WELCOME_MESSAGE = (
        "Добро пожаловать в CNC Luga!\n\n"
        "Этот бот — ваш надёжный напарник в мире ЧПУ и трудовых вопросов. Валера — ваш строгий, но отзывчивый помощник: "
        "он разбирается в металлообработке, G-коде, наладке станков и знает законы как свой ящик с инструментами.\n\n"
        "Тут вы найдёте:\n"
        "🔧 *Техническая и юридическая помощь*:\n"
        "  - /valera — Задайте вопрос по ЧПУ, металлообработке, программированию или юридическим вопросам — Валера всё объяснит.\n"
        "  - /report — Анонимно сообщите о проблемах на работе.\n\n"
        "📰 *Сообщество и новости*:\n"
        "  - /news — Новости и обновления из мира ЧПУ.\n"
        "  - /contact — Контакты для связи с администрацией.\n\n"
        "Мы здесь, чтобы сделать вашу работу проще, а жизнь — увереннее. Валера рядом — вы не один!"
    )
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode='Markdown', reply_markup=main_menu())

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    HELP_MESSAGE = (
        "🤖 *CNC Luga Bot - Помощник в мире ЧПУ и трудовых вопросов*\n\n"
        "*Доступные команды:*\n"
        "/start - Запустить бота и показать главное меню\n"
        "/help - Показать эту справку\n"
        "/valera - Начать диалог с Валерой (техническая и юридическая помощь)\n"
        "/report - Отправить анонимное сообщение\n"
        "/news - Показать новости\n"
        "/contact - Контакты для связи\n\n"
        "*Как пользоваться ботом:*\n"
        "1. Выберите нужную функцию из меню\n"
        "2. Следуйте инструкциям бота\n"
        "3. В любой момент вы можете вернуться в главное меню, нажав кнопку '📋 Меню'"
    )
    await update.message.reply_text(HELP_MESSAGE, parse_mode='Markdown', reply_markup=main_menu())

# Обработчик кнопки "📋 Меню"
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите команду:", reply_markup=commands_menu())

# Обработчик кнопки "↩️ Назад"
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Главное меню:", reply_markup=main_menu())

# Обработчик кнопок меню
async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    logger.info(f"Пользователь {chat_id} нажал кнопку: {text}")
    
    # Сбрасываем контекст пользователя при выборе нового персонажа
    if text == "📸 Валера":
        user_contexts[chat_id] = {"role": USER_STATE_VALERA, "history": []}
        await valera_start(update, context)
    elif text == "🔴 Аноним":
        user_contexts[chat_id] = {"role": USER_STATE_REPORT, "history": []}
        await report_start(update, context)

# 📸 Валера — начало диалога
async def valera_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Пользователь {chat_id} запустил диалог с Валерой")
    
    # Сбрасываем контекст пользователя
    user_contexts[chat_id] = {"role": USER_STATE_VALERA, "history": []}
    await update.message.reply_text(
        "Введите название инструмента, вопрос по ЧПУ или отправьте фото чертежа для помощи с программированием:",
        reply_markup=ReplyKeyboardRemove()
    )

# Логика общения с Валерой
async def valera_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_message = update.message.text
    
    if user_id not in user_contexts:
        user_contexts[user_id] = {"role": USER_STATE_VALERA, "history": []}
    
    user_contexts[user_id]["history"].append({"role": "user", "content": user_message})
    
    system_prompt = """Ты — Валера, опытный наладчик ЧПУ и юрист в одном лице. Ты строгий, но отзывчивый помощник, который разбирается в металлообработке, G-коде, наладке станков и знает законы как свой ящик с инструментами.

Твои основные качества:
1. Техническая экспертиза:
   - Глубокое понимание ЧПУ, металлообработки и программирования
   - Опыт наладки станков и оптимизации процессов
   - Знание G-кода и CAM-систем

2. Юридическая грамотность:
   - Понимание трудового законодательства
   - Опыт в решении трудовых споров
   - Знание прав работников и работодателей

3. Стиль общения:
   - Строгий, но дружелюбный тон
   - Чёткие и понятные объяснения
   - Готовность помочь в любой ситуации

4. Приоритеты:
   - Безопасность работников
   - Качество продукции
   - Соблюдение трудовых прав

Отвечай кратко, по существу, с юмором и всегда готов помочь — будь то вопрос по наладке станка или по трудовому праву."""

    # Формируем промпт для Яндекс GPT
    prompt = f"{system_prompt}\n\n"
    for msg in user_contexts[user_id]["history"]:
        role = "Пользователь" if msg["role"] == "user" else "Валера"
        prompt += f"{role}: {msg['content']}\n"
    
    try:
        # Используем Яндекс GPT
        bot_response = await yandex_gpt_request(prompt)
        user_contexts[user_id]["history"].append({"role": "assistant", "content": bot_response})
        await update.message.reply_text(bot_response)
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")

# 🔴 Аноним — начало
async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Пользователь {chat_id} запустил диалог с Анонимом")
    
    # Сбрасываем контекст пользователя
    user_contexts[chat_id] = {"role": USER_STATE_REPORT, "history": []}
    await update.message.reply_text(
        "🔴 Опишите проблему анонимно:",
        reply_markup=ReplyKeyboardRemove()
    )

# Сохранение анонимного сообщения
async def report_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Проверяем, что пользователь находится в контексте Анонима
    if chat_id not in user_contexts or user_contexts[chat_id]["role"] != USER_STATE_REPORT:
        logger.warning(f"Пользователь {chat_id} пытается отправить анонимное сообщение, но находится в другом контексте")
        await update.message.reply_text(
            "Вы не находитесь в режиме анонимного сообщения. Используйте команду /report или кнопку меню.",
            reply_markup=main_menu()
        )
        return
        
    user_id = update.effective_user.id
    report_text = update.message.text.strip()
    logger.info(f"Пользователь {chat_id} отправил анонимное сообщение: {report_text[:50]}...")
    
    save_report(user_id, report_text)
    await update.message.reply_text(
        "✅ Ваше сообщение принято и передано анонимно.",
        reply_markup=main_menu()
    )
    
    # Сбрасываем контекст
    user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}

# 📰 Новости
async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Пользователь {chat_id} запросил новости")
    
    news_text = get_news()
    await update.message.reply_text(news_text, reply_markup=main_menu())

# ✏️ Редактирование новостей
async def update_news_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Пользователь {chat_id} запустил редактирование новостей")
    
    # Сбрасываем контекст пользователя
    user_contexts[chat_id] = {"role": USER_STATE_UPDATE_NEWS, "history": []}
    await update.message.reply_text(
        "Введите новый текст новостей:",
        reply_markup=ReplyKeyboardRemove()
    )

async def process_update_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Проверяем, что пользователь находится в контексте редактирования новостей
    if chat_id not in user_contexts or user_contexts[chat_id]["role"] != USER_STATE_UPDATE_NEWS:
        logger.warning(f"Пользователь {chat_id} пытается обновить новости, но находится в другом контексте")
        await update.message.reply_text(
            "Вы не находитесь в режиме редактирования новостей. Используйте команду /update_news.",
            reply_markup=main_menu()
        )
        return
        
    new_news = update.message.text.strip()
    logger.info(f"Пользователь {chat_id} обновил новости: {new_news[:50]}...")
    
    update_news(new_news)
    await update.message.reply_text(
        "✅ Новости успешно обновлены!",
        reply_markup=main_menu()
    )
    
    # Сбрасываем контекст
    user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}

# 📞 Контакты
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Пользователь {chat_id} запросил контакты")
    
    await update.message.reply_text(
        "📞 Связаться с нами можно по email: support@cncluga.com",
        reply_markup=main_menu()
    )

# Рассылка
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Пользователь {chat_id} запустил рассылку")
    
    # Сбрасываем контекст пользователя
    user_contexts[chat_id] = {"role": USER_STATE_BROADCAST, "history": []}
    await update.message.reply_text(
        "Введите сообщение для рассылки:",
        reply_markup=ReplyKeyboardRemove()
    )

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Проверяем, что пользователь находится в контексте рассылки
    if chat_id not in user_contexts or user_contexts[chat_id]["role"] != USER_STATE_BROADCAST:
        logger.warning(f"Пользователь {chat_id} пытается отправить рассылку, но находится в другом контексте")
        await update.message.reply_text(
            "Вы не находитесь в режиме рассылки. Используйте команду /broadcast.",
            reply_markup=main_menu()
        )
        return
        
    broadcast_text = update.message.text.strip()
    logger.info(f"Пользователь {chat_id} отправил рассылку: {broadcast_text[:50]}...")
    
    from broadcast import send_broadcast
    await send_broadcast(context.bot, broadcast_text)
    await update.message.reply_text(
        "✅ Сообщение отправлено всем пользователям.",
        reply_markup=main_menu()
    )
    
    # Сбрасываем контекст
    user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}

# Обработчик всех текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # Обработка кнопок меню
    if text == "📋 Меню":
        await menu(update, context)
    elif text == "↩️ Назад":
        await back_to_main_menu(update, context)
    elif text in ["📸 Валера", "🔴 Аноним"]:
        await handle_menu_buttons(update, context)
    # Обработка сообщений в зависимости от контекста
    elif chat_id in user_contexts:
        if user_contexts[chat_id]["role"] == USER_STATE_VALERA:
            await valera_ai(update, context)
        elif user_contexts[chat_id]["role"] == USER_STATE_REPORT:
            await report_response(update, context)
        elif user_contexts[chat_id]["role"] == USER_STATE_UPDATE_NEWS:
            await process_update_news(update, context)
        elif user_contexts[chat_id]["role"] == USER_STATE_BROADCAST:
            await process_broadcast(update, context)
    else:
        # Если пользователь не в каком-либо контексте, отправляем приветствие
        await start(update, context)

# Функция для регистрации всех обработчиков
def register_handlers(app_bot):
    # Команды
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("menu", menu))
    app_bot.add_handler(CommandHandler("valera", valera_start))
    app_bot.add_handler(CommandHandler("report", report_start))
    app_bot.add_handler(CommandHandler("news", news_handler))
    app_bot.add_handler(CommandHandler("update_news", update_news_start))
    app_bot.add_handler(CommandHandler("contact", contact_handler))
    app_bot.add_handler(CommandHandler("broadcast", broadcast_message))
    
    # Обработчик кнопки "Назад"
    app_bot.add_handler(MessageHandler(filters.Regex("^↩️ Назад$"), back_to_main_menu))
    
    # Обработчик текстовых сообщений
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))