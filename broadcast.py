import logging
import os
from users import get_users

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def send_broadcast(bot, message_text):
    """
    Асинхронная функция для отправки сообщения всем пользователям бота.
    
    Args:
        bot: Объект бота Telegram
        message_text (str): Текст сообщения для рассылки
    """
    users = get_users()
    success_count = 0
    fail_count = 0
    
    logger.info(f"Начало рассылки сообщения {len(users)} пользователям")
    
    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"📢 Сообщение от администрации:\n\n{message_text}"
            )
            success_count += 1
            logger.info(f"Сообщение успешно отправлено пользователю {user_id}")
        except Exception as e:
            fail_count += 1
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    
    logger.info(f"Рассылка завершена. Успешно: {success_count}, Ошибок: {fail_count}")
    return success_count, fail_count