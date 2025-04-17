import logging
from telebot import types
from gpt_api import yandex_gpt_request, yandex_gpt_request_async
from news import get_news, update_news
from reports import save_report

def register_handlers(bot):
    # Словарь для хранения истории диалогов пользователей
    user_contexts = {}

    # Создаём главное меню с кнопками
    def main_menu():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # Обновляем кнопки меню, убираем "Антон" и оставляем только "Валера"
        markup.add(types.KeyboardButton("📸 Валера"))
        markup.add(types.KeyboardButton("⚖ Юрист"), types.KeyboardButton("🔴 Аноним"))
        return markup

    # Обработчик команды /start
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        from users import save_user
        save_user(message.chat.id)
        # Сбрасываем контекст пользователя при старте
        user_contexts[message.chat.id] = {"role": None, "history": []}
        logging.info(f"Пользователь {message.chat.id} запустил бота")
        
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
        bot.send_message(message.chat.id, WELCOME_MESSAGE, parse_mode='Markdown', reply_markup=main_menu())

    # Обработчик кнопок меню
    @bot.message_handler(func=lambda message: message.text in ["📸 Валера", "⚖ Юрист", "🔴 Аноним"])
    def handle_menu_buttons(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} нажал кнопку: {message.text}")
        
        # Сбрасываем контекст пользователя при выборе нового персонажа
        if message.text == "📸 Валера":
            user_contexts[chat_id] = {"role": "valera", "history": []}
            valera_start(message)
        elif message.text == "⚖ Юрист":
            user_contexts[chat_id] = {"role": "legal", "history": []}
            legal_start(message)
        elif message.text == "🔴 Аноним":
            user_contexts[chat_id] = {"role": "report", "history": []}
            report_start(message)

    # 📸 Валера — начало диалога
    @bot.message_handler(commands=['valera'])
    def valera_start(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} запустил диалог с Валерой")
        
        # Сбрасываем контекст пользователя
        user_contexts[chat_id] = {"role": "valera", "history": []}
        bot.send_message(chat_id, "Введите название инструмента, вопрос по ЧПУ или отправьте фото чертежа для помощи с программированием:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, valera_ai)

    # Логика общения с Валерой
    def valera_ai(message):
        chat_id = message.chat.id
        
        # Проверяем, что пользователь находится в контексте Валеры
        if chat_id not in user_contexts or user_contexts[chat_id]["role"] != "valera":
            logging.warning(f"Пользователь {chat_id} пытается общаться с Валерой, но находится в другом контексте")
            bot.send_message(chat_id, "Вы не находитесь в диалоге с Валерой. Используйте команду /valera или кнопку меню.", reply_markup=main_menu())
            return
            
        if message.text.startswith('/'):
            logging.info(f"Пользователь {chat_id} завершил диалог с Валерой, выбрав команду {message.text}")
            bot.send_message(chat_id, "Вы выбрали другую команду. Диалог с Валерой завершен.", reply_markup=main_menu())
            # Сбрасываем контекст
            user_contexts[chat_id] = {"role": None, "history": []}
            return
        
        user_question = message.text.strip()
        logging.info(f"Пользователь {chat_id} задал вопрос Валере: {user_question[:50]}...")
        user_contexts[chat_id]["history"].append(f"Ты: {user_question}")
        
        # Отправляем сообщение о том, что запрос обрабатывается
        processing_msg = bot.send_message(chat_id, "🤔 Валера думает над вашим вопросом...")
        
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
        def handle_valera_response(answer):
            try:
                # Удаляем сообщение о том, что запрос обрабатывается
                bot.delete_message(chat_id, processing_msg.message_id)
                
                if not answer or not answer.strip():
                    answer = "⚠ Не удалось получить данные. Попробуйте уточнить запрос."
                logging.info(f"Получен ответ от API Яндекс GPT для пользователя {chat_id}")
                bot.send_message(chat_id, f"🤖 Валера отвечает:\n\n{answer}")
                user_contexts[chat_id]["history"].append(f"Валера: {answer}")
                bot.register_next_step_handler(message, valera_ai)  # Продолжаем диалог
            except Exception as e:
                logging.error(f"Ошибка при обработке ответа от API для пользователя {chat_id}: {e}")
                bot.send_message(chat_id, "⚠ Ошибка Валеры: не удалось получить ответ. Попробуйте позже.", reply_markup=main_menu())
                # Сбрасываем контекст при ошибке
                user_contexts[chat_id] = {"role": None, "history": []}

        try:
            logging.info(f"Отправка запроса к API Яндекс GPT для пользователя {chat_id}")
            # Используем асинхронный запрос
            yandex_gpt_request_async(prompt, handle_valera_response)
        except Exception as e:
            logging.error(f"Ошибка Валеры для пользователя {chat_id}: {e}")
            bot.delete_message(chat_id, processing_msg.message_id)
            bot.send_message(chat_id, "⚠ Ошибка Валеры: не удалось получить ответ. Попробуйте позже.", reply_markup=main_menu())
            # Сбрасываем контекст при ошибке
            user_contexts[chat_id] = {"role": None, "history": []}

    # ⚖ Юрист — начало диалога
    @bot.message_handler(commands=['legal'])
    def legal_start(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} запустил диалог с Юристом")
        
        # Сбрасываем контекст пользователя
        user_contexts[chat_id] = {"role": "legal", "history": []}
        bot.send_message(chat_id, "Опишите Вашу ситуацию или задайте юридический вопрос:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, legal_ai)

    # Логика общения с Юристом
    def legal_ai(message):
        chat_id = message.chat.id
        
        # Проверяем, что пользователь находится в контексте Юриста
        if chat_id not in user_contexts or user_contexts[chat_id]["role"] != "legal":
            logging.warning(f"Пользователь {chat_id} пытается общаться с Юристом, но находится в другом контексте")
            bot.send_message(chat_id, "Вы не находитесь в диалоге с Юристом. Используйте команду /legal или кнопку меню.", reply_markup=main_menu())
            return
            
        if message.text.startswith('/'):
            logging.info(f"Пользователь {chat_id} завершил диалог с Юристом, выбрав команду {message.text}")
            bot.send_message(chat_id, "Вы выбрали другую команду. Диалог с Юристом завершен.", reply_markup=main_menu())
            # Сбрасываем контекст
            user_contexts[chat_id] = {"role": None, "history": []}
            return
            
        user_question = message.text.strip()
        logging.info(f"Пользователь {chat_id} задал вопрос Юристу: {user_question[:50]}...")
        user_contexts[chat_id]["history"].append(f"Ты: {user_question}")
        
        # Отправляем сообщение о том, что запрос обрабатывается
        processing_msg = bot.send_message(chat_id, "⚖ Юрист анализирует ваш вопрос...")
        
        prompt = (
            "Ты — лучший юридический консультант по законам РФ. Отвечай на вопросы пользователей четко и по существу, "
            "предоставляя шаги для решения их юридических проблем. Если вопрос неясен, задавай уточняющие вопросы. "
            "История диалога: " + "\n".join(user_contexts[chat_id]["history"]) + "\n" +
            f"Вот вопрос: {user_question}"
        )
        
        # Функция обратного вызова для обработки ответа от API
        def handle_legal_response(answer):
            try:
                # Удаляем сообщение о том, что запрос обрабатывается
                bot.delete_message(chat_id, processing_msg.message_id)
                
                if not answer or not answer.strip():
                    answer = "⚠ Не удалось получить данные. Попробуйте уточнить запрос."
                logging.info(f"Получен ответ от API Яндекс GPT для пользователя {chat_id}")
                bot.send_message(chat_id, f"⚖ Юрист отвечает:\n\n{answer}")
                user_contexts[chat_id]["history"].append(f"Юрист: {answer}")
                bot.register_next_step_handler(message, legal_ai)  # Продолжаем диалог
            except Exception as e:
                logging.error(f"Ошибка при обработке ответа от API для пользователя {chat_id}: {e}")
                bot.send_message(chat_id, "⚠ Ошибка Юриста: не удалось получить ответ. Попробуйте позже.", reply_markup=main_menu())
                # Сбрасываем контекст при ошибке
                user_contexts[chat_id] = {"role": None, "history": []}
        
        try:
            logging.info(f"Отправка запроса к API Яндекс GPT для пользователя {chat_id}")
            # Используем асинхронный запрос
            yandex_gpt_request_async(prompt, handle_legal_response)
        except Exception as e:
            logging.error(f"Ошибка Юриста для пользователя {chat_id}: {e}")
            bot.delete_message(chat_id, processing_msg.message_id)
            bot.send_message(chat_id, "⚠ Ошибка Юриста: не удалось получить ответ. Попробуйте позже.", reply_markup=main_menu())
            # Сбрасываем контекст при ошибке
            user_contexts[chat_id] = {"role": None, "history": []}

    # 🔴 Аноним — начало
    @bot.message_handler(commands=['report'])
    def report_start(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} запустил диалог с Анонимом")
        
        # Сбрасываем контекст пользователя
        user_contexts[chat_id] = {"role": "report", "history": []}
        bot.send_message(chat_id, "🔴 Опишите проблему анонимно:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, report_response)

    # Сохранение анонимного сообщения
    def report_response(message):
        chat_id = message.chat.id
        
        # Проверяем, что пользователь находится в контексте Анонима
        if chat_id not in user_contexts or user_contexts[chat_id]["role"] != "report":
            logging.warning(f"Пользователь {chat_id} пытается отправить анонимное сообщение, но находится в другом контексте")
            bot.send_message(chat_id, "Вы не находитесь в режиме анонимного сообщения. Используйте команду /report или кнопку меню.", reply_markup=main_menu())
            return
            
        user_id = message.from_user.id
        report_text = message.text.strip()
        logging.info(f"Пользователь {chat_id} отправил анонимное сообщение: {report_text[:50]}...")
        
        save_report(user_id, report_text)
        bot.send_message(chat_id, "✅ Ваше сообщение принято и передано анонимно.", reply_markup=main_menu())
        
        # Сбрасываем контекст
        user_contexts[chat_id] = {"role": None, "history": []}

    # 📰 Новости
    @bot.message_handler(commands=['news'])
    def news_handler(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} запросил новости")
        
        news_text = get_news()
        bot.send_message(chat_id, news_text, reply_markup=main_menu())

    # ✏️ Редактирование новостей
    @bot.message_handler(commands=['update_news'])
    def update_news_start(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} запустил редактирование новостей")
        
        # Сбрасываем контекст пользователя
        user_contexts[chat_id] = {"role": "update_news", "history": []}
        bot.send_message(chat_id, "Введите новый текст новостей:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_update_news)

    def process_update_news(message):
        chat_id = message.chat.id
        
        # Проверяем, что пользователь находится в контексте редактирования новостей
        if chat_id not in user_contexts or user_contexts[chat_id]["role"] != "update_news":
            logging.warning(f"Пользователь {chat_id} пытается обновить новости, но находится в другом контексте")
            bot.send_message(chat_id, "Вы не находитесь в режиме редактирования новостей. Используйте команду /update_news.", reply_markup=main_menu())
            return
            
        new_news = message.text.strip()
        logging.info(f"Пользователь {chat_id} обновил новости: {new_news[:50]}...")
        
        update_news(new_news)
        bot.send_message(chat_id, "✅ Новости успешно обновлены!", reply_markup=main_menu())
        
        # Сбрасываем контекст
        user_contexts[chat_id] = {"role": None, "history": []}

    # 📞 Контакты
    @bot.message_handler(commands=['contact'])
    def contact_handler(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} запросил контакты")
        
        bot.send_message(chat_id, "📞 Связаться с нами можно по email: support@cncluga.com", reply_markup=main_menu())

    # Рассылка
    @bot.message_handler(commands=['broadcast'])
    def broadcast_message(message):
        chat_id = message.chat.id
        logging.info(f"Пользователь {chat_id} запустил рассылку")
        
        # Сбрасываем контекст пользователя
        user_contexts[chat_id] = {"role": "broadcast", "history": []}
        bot.send_message(chat_id, "Введите сообщение для рассылки:", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_broadcast)

    def process_broadcast(message):
        chat_id = message.chat.id
        
        # Проверяем, что пользователь находится в контексте рассылки
        if chat_id not in user_contexts or user_contexts[chat_id]["role"] != "broadcast":
            logging.warning(f"Пользователь {chat_id} пытается отправить рассылку, но находится в другом контексте")
            bot.send_message(chat_id, "Вы не находитесь в режиме рассылки. Используйте команду /broadcast.", reply_markup=main_menu())
            return
            
        broadcast_text = message.text.strip()
        logging.info(f"Пользователь {chat_id} отправил рассылку: {broadcast_text[:50]}...")
        
        from broadcast import send_broadcast
        send_broadcast(bot, broadcast_text)
        bot.send_message(chat_id, "✅ Сообщение отправлено всем пользователям.", reply_markup=main_menu())
        
        # Сбрасываем контекст
        user_contexts[chat_id] = {"role": None, "history": []}