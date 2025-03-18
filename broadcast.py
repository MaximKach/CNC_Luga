import logging
from users import get_users

# Отправляем сообщение всем пользователям
def send_broadcast(bot, message_text):
    users = get_users()
    for user in users:
        try:
            bot.send_message(user, f"📢 Сообщение от администрации:\n\n{message_text}")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение пользователю {user}: {e}")