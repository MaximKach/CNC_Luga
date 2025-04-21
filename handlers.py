import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from gpt_api import yandex_gpt_request, yandex_gpt_request_async
from news import get_news, update_news
from reports import save_report
from users import save_user
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
        ["⚖ Юрист", "🔴 Аноним"],
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
    save_user(update.effective_chat.id)
    # Сбрасываем контекст пользователя при старте
    user_contexts[update.effective_chat.id] = {"role": USER_STATE_NONE, "history": []}
    logger.info(f"Пользователь {update.effective_chat.id} запустил бота")
    
    WELCOME_MESSAGE = (
        "Добро пожаловать в CNC Luga!\n\n"
        "Этот бот — ваш помощник в мире ЧПУ. Мы не только помогаем писать G-код по фото деталей и отвечаем на технические вопросы с помощью ИИ, "
        "но и стоим на страже ваших прав.\n\n"
        "Тут вы найдёте:\n"
        "🔧 *Техническая помощь*:\n"
        "  - /valera — Введите название инструмента или вопрос по ЧПУ, и Валера подберёт режимы резания и поможет с программированием.\n\n"
        "⚖ *Юридическая поддержка*:\n"
        "  - /legal — Юридическая помощь по вопросам больничных, отпусков и переработок.\n"
        "  - /report — Анонимно сообщите о проблемах на работе.\n\n"
        "📰 *Сообщество и новости*:\n"
        "  - /news — Новости и обновления из мира ЧПУ.\n"
        "  - /contact — Контакты для связи с администрацией.\n\n"
        "Мы здесь, чтобы сделать вашу работу проще, а жизнь — лучше. Вместе мы сильнее!"
    )
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode='Markdown', reply_markup=main_menu())

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    HELP_MESSAGE = (
        "🤖 *CNC Luga Bot - Помощник в мире ЧПУ*\n\n"
        "*Доступные команды:*\n"
        "/start - Запустить бота и показать главное меню\n"
        "/help - Показать эту справку\n"
        "/valera - Начать диалог с Валерой (техническая помощь)\n"
        "/legal - Начать диалог с Юристом (юридическая помощь)\n"
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
    elif text == "⚖ Юрист":
        user_contexts[chat_id] = {"role": USER_STATE_LEGAL, "history": []}
        await legal_start(update, context)
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
    chat_id = update.effective_chat.id
    
    # Проверяем, что пользователь находится в контексте Валеры
    if chat_id not in user_contexts or user_contexts[chat_id]["role"] != USER_STATE_VALERA:
        logger.warning(f"Пользователь {chat_id} пытается общаться с Валерой, но находится в другом контексте")
        await update.message.reply_text(
            "Вы не находитесь в диалоге с Валерой. Используйте команду /valera или кнопку меню.",
            reply_markup=main_menu()
        )
        return
        
    if update.message.text and update.message.text.startswith('/'):
        logger.info(f"Пользователь {chat_id} завершил диалог с Валерой, выбрав команду {update.message.text}")
        await update.message.reply_text(
            "Вы выбрали другую команду. Диалог с Валерой завершен.",
            reply_markup=main_menu()
        )
        # Сбрасываем контекст
        user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}
        return
    
    user_question = update.message.text.strip() if update.message.text else "Фото чертежа"
    logger.info(f"Пользователь {chat_id} задал вопрос Валере: {user_question[:50]}...")
    user_contexts[chat_id]["history"].append(f"Ты: {user_question}")
    
    # Отправляем сообщение о том, что запрос обрабатывается
    processing_msg = await update.message.reply_text("🤔 Валера думает над вашим вопросом...")
    
    # Обновленный промпт для Валеры
    prompt = (
        "Ты — опытный технолог, наладчик ЧПУ и программист, который не терпит глупости, но готов помочь, "
        "отвечая строго, саркастично и с юмором. Если вопрос неполный или неясный, уточняй детали. "
        "Отвечай на вопросы по темам ЧПУ, металлообработки, инструментов, наладки станка и программирования. "
        "Старайся ответить кратко, но предельно понятно. "
        "Если спрашивают про режимы резания – указывай скорость (Vc), подачу (F), глубину резания (Ap), обороты (RPM) и СОЖ. "
        "Если вопрос про выбор инструмента, наладку, фаску, радиус или шероховатость (например, Ra10) — объясняй, когда и зачем что применять. "
        "Если вопрос связан с программированием ЧПУ или G-кодом, предоставь подробное объяснение и примеры кода. "
        "В конце каждого ответа добавляй ОДНУ мотивирующую фразу в твоём стиле — саркастичную, но доброжелательную. "
        "Фраза должна быть уникальной, в духе опытного наладчика, который подкалывает, но хочет помочь. "
        "Примеры: 'Ну вот, уже лучше, но думай головой!', 'Ты, конечно, кадр... но я помогу!', 'Если опять тупишь — перечитай ещё раз!', но ты должен придумывать НОВЫЕ фразы каждый раз."
        "\n\n"
        "История диалога: " + "\n".join(user_contexts[chat_id]["history"]) + "\n" +
        f"Вот вопрос: {user_question}"
    )

    # Функция обратного вызова для обработки ответа от API
    async def handle_valera_response(answer):
        try:
            # Удаляем сообщение о том, что запрос обрабатывается
            await context.bot.delete_message(chat_id, processing_msg.message_id)
            
            if not answer or not answer.strip():
                answer = "⚠ Не удалось получить данные. Попробуйте уточнить запрос."
            logger.info(f"Получен ответ от API Яндекс GPT для пользователя {chat_id}")
            await update.message.reply_text(f"🤖 Валера отвечает:\n\n{answer}")
            user_contexts[chat_id]["history"].append(f"Валера: {answer}")
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа от API для пользователя {chat_id}: {e}")
            await update.message.reply_text(
                "⚠ Ошибка Валеры: не удалось получить ответ. Попробуйте позже.",
                reply_markup=main_menu()
            )
            # Сбрасываем контекст при ошибке
            user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}

    try:
        logger.info(f"Отправка запроса к API Яндекс GPT для пользователя {chat_id}")
        # Используем асинхронный запрос
        await yandex_gpt_request_async(prompt, handle_valera_response)
    except Exception as e:
        logger.error(f"Ошибка Валеры для пользователя {chat_id}: {e}")
        await context.bot.delete_message(chat_id, processing_msg.message_id)
        await update.message.reply_text(
            "⚠ Ошибка Валеры: не удалось получить ответ. Попробуйте позже.",
            reply_markup=main_menu()
        )
        # Сбрасываем контекст при ошибке
        user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}

# ⚖ Юрист — начало диалога
async def legal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"Пользователь {chat_id} запустил диалог с Юристом")
    
    # Сбрасываем контекст пользователя
    user_contexts[chat_id] = {"role": USER_STATE_LEGAL, "history": []}
    await update.message.reply_text(
        "Опишите Вашу ситуацию или задайте юридический вопрос:",
        reply_markup=ReplyKeyboardRemove()
    )

# Логика общения с Юристом
async def legal_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Проверяем, что пользователь находится в контексте Юриста
    if chat_id not in user_contexts or user_contexts[chat_id]["role"] != USER_STATE_LEGAL:
        logger.warning(f"Пользователь {chat_id} пытается общаться с Юристом, но находится в другом контексте")
        await update.message.reply_text(
            "Вы не находитесь в диалоге с Юристом. Используйте команду /legal или кнопку меню.",
            reply_markup=main_menu()
        )
        return
        
    if update.message.text and update.message.text.startswith('/'):
        logger.info(f"Пользователь {chat_id} завершил диалог с Юристом, выбрав команду {update.message.text}")
        await update.message.reply_text(
            "Вы выбрали другую команду. Диалог с Юристом завершен.",
            reply_markup=main_menu()
        )
        # Сбрасываем контекст
        user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}
        return
        
    user_question = update.message.text.strip()
    logger.info(f"Пользователь {chat_id} задал вопрос Юристу: {user_question[:50]}...")
    user_contexts[chat_id]["history"].append(f"Ты: {user_question}")
    
    # Отправляем сообщение о том, что запрос обрабатывается
    processing_msg = await update.message.reply_text("⚖ Юрист анализирует ваш вопрос...")
    
    prompt = (
        "Ты — профессиональный юрист, специализирующийся на защите прав работников в России. "
        "Твоя задача — не просто ответить на вопрос, а **защитить пользователя**, поддержать его морально, показать выход и дать чёткий план действий. "
        "Если в вопросе не хватает информации — **обязательно уточни ключевые моменты**, чтобы ответ был максимально точным. "
        "Отвечай просто, доступно, без запугивания и лишних юридических терминов. Помни: человек обращается, потому что чувствует себя беззащитным. "
        "Дай понять, что он уже не один — теперь у него есть грамотная поддержка. "
        "Если вопрос касается давления на работе, угроз, увольнения, жалоб или прав — дай советы, куда обратиться, как это сделать безопасно, какие документы подготовить и с чего начать. "
        "Объясни человеку, что его можно защитить. Ответ должен включать:\n"
        "- Эмоциональную поддержку (в духе: «вы не один», «мы поможем», «есть способ»)\n"
        "- Уточняющие вопросы, если что-то непонятно\n"
        "- Чёткий пошаговый план: с чего начать, куда идти, что сделать\n"
        "- Примеры, если нужно\n"
        "- Никакой воды — только реальная помощь\n"
        "История диалога:\n" + "\n".join(user_contexts[chat_id]["history"]) + "\n" +
        f"Вопрос пользователя: {user_question}"
    )
    
    # Функция обратного вызова для обработки ответа от API
    async def handle_legal_response(answer):
        try:
            # Удаляем сообщение о том, что запрос обрабатывается
            await context.bot.delete_message(chat_id, processing_msg.message_id)
            
            if not answer or not answer.strip():
                answer = "⚠ Не удалось получить данные. Попробуйте уточнить запрос."
            logger.info(f"Получен ответ от API Яндекс GPT для пользователя {chat_id}")
            await update.message.reply_text(f"⚖ Юрист отвечает:\n\n{answer}")
            user_contexts[chat_id]["history"].append(f"Юрист: {answer}")
        except Exception as e:
            logger.error(f"Ошибка при обработке ответа от API для пользователя {chat_id}: {e}")
            await update.message.reply_text(
                "⚠ Ошибка Юриста: не удалось получить ответ. Попробуйте позже.",
                reply_markup=main_menu()
            )
            # Сбрасываем контекст при ошибке
            user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}
    
    try:
        logger.info(f"Отправка запроса к API Яндекс GPT для пользователя {chat_id}")
        # Используем асинхронный запрос
        await yandex_gpt_request_async(prompt, handle_legal_response)
    except Exception as e:
        logger.error(f"Ошибка Юриста для пользователя {chat_id}: {e}")
        await context.bot.delete_message(chat_id, processing_msg.message_id)
        await update.message.reply_text(
            "⚠ Ошибка Юриста: не удалось получить ответ. Попробуйте позже.",
            reply_markup=main_menu()
        )
        # Сбрасываем контекст при ошибке
        user_contexts[chat_id] = {"role": USER_STATE_NONE, "history": []}

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
    elif text in ["📸 Валера", "⚖ Юрист", "🔴 Аноним"]:
        await handle_menu_buttons(update, context)
    # Обработка сообщений в зависимости от контекста
    elif chat_id in user_contexts:
        if user_contexts[chat_id]["role"] == USER_STATE_VALERA:
            await valera_ai(update, context)
        elif user_contexts[chat_id]["role"] == USER_STATE_LEGAL:
            await legal_ai(update, context)
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
    app_bot.add_handler(CommandHandler("legal", legal_start))
    app_bot.add_handler(CommandHandler("report", report_start))
    app_bot.add_handler(CommandHandler("news", news_handler))
    app_bot.add_handler(CommandHandler("update_news", update_news_start))
    app_bot.add_handler(CommandHandler("contact", contact_handler))
    app_bot.add_handler(CommandHandler("broadcast", broadcast_message))
    
    # Обработчик кнопки "Назад"
    app_bot.add_handler(MessageHandler(filters.Regex("^↩️ Назад$"), back_to_main_menu))
    
    # Обработчик текстовых сообщений
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))