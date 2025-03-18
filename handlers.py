import logging
from telebot import types
from gpt_api import yandex_gpt_request
from news import get_news, update_news
from reports import save_report

def register_handlers(bot):
    # Словарь для хранения истории диалогов пользователей
    user_contexts = {}

    # Создаём главное меню с кнопками
    def main_menu():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔧 Антон"), types.KeyboardButton("📸 Валера"))
        markup.add(types.KeyboardButton("⚖ Юрист"), types.KeyboardButton("🔴 Аноним"))
        return markup

    # Обработчик команды /start
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        from users import save_user
        save_user(message.chat.id)
        WELCOME_MESSAGE = (
            "Добро пожаловать в CNC Luga!\n\n"
            "Этот бот — ваш помощник в мире ЧПУ. Мы не только помогаем писать G-код по фото деталей и отвечаем на технические вопросы с помощью ИИ, "
            "но и стоим на страже ваших прав.\n\n"
            "Тут вы найдёте:\n"
            "🔧 *Техническая помощь*:\n"
            "  - /anton — Введите название инструмента, и Антон подберёт режимы резания.\n"
            "  - /valera — Отправьте фото чертежа и Валера напишет программу.\n\n"
            "⚖ *Юридическая поддержка*:\n"
            "  - /legal — Юридическая помощь по вопросам больничных, отпусков и переработок.\n"
            "  - /report — Анонимно сообщите о проблемах на работе.\n\n"
            "📰 *Сообщество и новости*:\n"
            "  - /news — Новости и обновления из мира ЧПУ.\n"
            "  - /contact — Контакты для связи с администрацией.\n\n"
            "Мы здесь, чтобы сделать вашу работу проще, а жизнь — лучше. Вместе мы сильнее!"
        )
        bot.send_message(message.chat.id, WELCOME_MESSAGE, parse_mode='Markdown', reply_markup=main_menu())

    # Обработчик кнопок меню
    @bot.message_handler(func=lambda message: message.text in ["🔧 Антон", "📸 Валера", "⚖ Юрист", "🔴 Аноним"])
    def handle_menu_buttons(message):
        if message.text == "🔧 Антон":
            anton_start(message)
        elif message.text == "📸 Валера":
            valera_start(message)
        elif message.text == "⚖ Юрист":
            legal_start(message)
        elif message.text == "🔴 Аноним":
            report_start(message)

    # 🔧 Антон — начало диалога
    @bot.message_handler(commands=['anton'])
    def anton_start(message):
        user_contexts[message.chat.id] = {"role": "anton", "history": []}
        bot.send_message(message.chat.id, "Введите название инструмента или вопрос по ЧПУ и металлообработке:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, anton_ai)

    # Логика общения с Антоном
    def anton_ai(message):
        if message.text.startswith('/'):
            bot.send_message(message.chat.id, "Вы выбрали другую команду. Диалог с Антоном завершен.", reply_markup=main_menu())
            return
        chat_id = message.chat.id
        user_question = message.text.strip()
        user_contexts[chat_id]["history"].append(f"Ты: {user_question}")
        # Новый промпт для Антона с генерацией мотивационных фраз
        prompt = (
            "Ты — опытный технолог и наладчик ЧПУ, который не терпит глупости, но готов помочь, "
            "отвечая строго, саркастично и с юмором. Если вопрос неполный или неясный, уточняй детали. "
            "Отвечай только по темам ЧПУ, металлообработки, инструментов и наладки станка. "
            "Если спрашивают про режимы резания – указывай скорость (Vc), подачу (F), глубину резания (Ap), обороты (RPM) и СОЖ. "
            "Если вопрос про выбор инструмента, наладку, фаску, радиус или шероховатость (например, Ra10) — объясняй, когда и зачем что применять. "
            "В конце каждого ответа добавляй разные мотивационные фразы, например: 'Ладно, давай в темпе вальса, и не забывай учиться!' или что-то в этом духе"
            "История диалога: " + "\n".join(user_contexts[chat_id]["history"]) + "\n" +
            f"Вот вопрос: {user_question}"
        )
        try:
            answer = yandex_gpt_request(prompt)
            if not answer or not answer.strip():
                answer = "⚠ Не удалось получить данные. Попробуйте уточнить запрос."
            bot.send_message(chat_id, f"🛠 Антон отвечает:\n\n{answer}")
            user_contexts[chat_id]["history"].append(f"Антон: {answer}")
            bot.register_next_step_handler(message, anton_ai)  # Продолжаем диалог
        except Exception as e:
            logging.error(f"Ошибка Антона: {e}")
            bot.send_message(chat_id, "⚠ Ошибка Антона: не удалось получить ответ. Попробуйте позже.", reply_markup=main_menu())

    # 📸 Валера
    @bot.message_handler(commands=['valera'])
    def valera_start(message):
        bot.send_message(message.chat.id, "🤖 Валера в процессе разработки. В будущем он сможет анализировать чертежи и помогать с G-кодом!", reply_markup=main_menu())

    # ⚖ Юрист — начало диалога
    @bot.message_handler(commands=['legal'])
    def legal_start(message):
        user_contexts[message.chat.id] = {"role": "legal", "history": []}
        bot.send_message(message.chat.id, "Опишите Вашу ситуацию или задайте юридический вопрос:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, legal_ai)

    # Логика общения с Юристом
    def legal_ai(message):
        if message.text.startswith('/'):
            bot.send_message(message.chat.id, "Вы выбрали другую команду. Диалог с Юристом завершен.", reply_markup=main_menu())
            return
        chat_id = message.chat.id
        user_question = message.text.strip()
        user_contexts[chat_id]["history"].append(f"Ты: {user_question}")
        prompt = (
            "Ты — лучший юридический консультант по законам РФ. Отвечай на вопросы пользователей четко и по существу, "
            "предоставляя шаги для решения их юридических проблем. Если вопрос неясен, задавай уточняющие вопросы. "
            "История диалога: " + "\n".join(user_contexts[chat_id]["history"]) + "\n" +
            f"Вот вопрос: {user_question}"
        )
        try:
            answer = yandex_gpt_request(prompt)
            if not answer or not answer.strip():
                answer = "⚠ Не удалось получить данные. Попробуйте уточнить запрос."
            bot.send_message(chat_id, f"⚖ Юрист отвечает:\n\n{answer}")
            user_contexts[chat_id]["history"].append(f"Юрист: {answer}")
            bot.register_next_step_handler(message, legal_ai)  # Продолжаем диалог
        except Exception as e:
            logging.error(f"Ошибка Юриста: {e}")
            bot.send_message(chat_id, "⚠ Ошибка Юриста: не удалось получить ответ. Попробуйте позже.", reply_markup=main_menu())

    # 🔴 Аноним — начало
    @bot.message_handler(commands=['report'])
    def report_start(message):
        bot.send_message(message.chat.id, "🔴 Опишите проблему анонимно:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, report_response)

    # Сохранение анонимного сообщения
    def report_response(message):
        user_id = message.from_user.id
        report_text = message.text.strip()
        save_report(user_id, report_text)
        bot.send_message(message.chat.id, "✅ Ваше сообщение принято и передано анонимно.", reply_markup=main_menu())

    # 📰 Новости
    @bot.message_handler(commands=['news'])
    def news_handler(message):
        news_text = get_news()
        bot.send_message(message.chat.id, news_text, reply_markup=main_menu())

    # ✏️ Редактирование новостей
    @bot.message_handler(commands=['update_news'])
    def update_news_start(message):
        bot.send_message(message.chat.id, "Введите новый текст новостей:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_update_news)

    def process_update_news(message):
        new_news = message.text.strip()
        update_news(new_news)
        bot.send_message(message.chat.id, "✅ Новости успешно обновлены!", reply_markup=main_menu())

    # 📞 Контакты
    @bot.message_handler(commands=['contact'])
    def contact_handler(message):
        bot.send_message(message.chat.id, "📞 Связаться с нами можно по email: support@cncluga.com", reply_markup=main_menu())

    # Рассылка
    @bot.message_handler(commands=['broadcast'])
    def broadcast_message(message):
        bot.send_message(message.chat.id, "Введите сообщение для рассылки:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_broadcast)

    def process_broadcast(message):
        from broadcast import send_broadcast
        send_broadcast(bot, message.text)
        bot.send_message(message.chat.id, "✅ Сообщение отправлено всем пользователям.", reply_markup=main_menu())