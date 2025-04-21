import logging
import os
import json
import traceback
from typing import List, Dict, Optional
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Изменяем уровень на DEBUG для более подробных логов
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("users.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

USERS_FILE = 'users.json'

def load_users() -> Dict:
    """
    Загружает список пользователей из файла.
    
    Returns:
        Dict: Словарь с данными пользователей
    """
    if not os.path.exists(USERS_FILE):
        logger.debug(f"Файл {USERS_FILE} не существует, возвращаем пустой словарь")
        return {}
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            logger.debug(f"Загружено {len(users)} пользователей из файла")
            return users
    except Exception as e:
        logger.error(f"Ошибка при загрузке пользователей: {e}")
        logger.error(traceback.format_exc())
        return {}

def save_users(users: Dict) -> None:
    """
    Сохраняет список пользователей в файл.
    
    Args:
        users (Dict): Словарь с данными пользователей
    """
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
            logger.debug(f"Сохранено {len(users)} пользователей в файл")
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователей: {e}")
        logger.error(traceback.format_exc())

def get_users() -> List[int]:
    """
    Возвращает список ID всех пользователей.
    
    Returns:
        List[int]: Список ID пользователей
    """
    users = load_users()
    return list(users.keys())

async def add_user(user_id: int, username: Optional[str] = None) -> None:
    """
    Добавляет нового пользователя в список.
    
    Args:
        user_id (int): ID пользователя
        username (Optional[str]): Имя пользователя
    """
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            'username': username,
            'added_at': str(datetime.now())
        }
        save_users(users)
        logger.info(f"Добавлен новый пользователь: {user_id} (username: {username})")

async def remove_user(user_id: int) -> bool:
    """
    Удаляет пользователя из списка.
    
    Args:
        user_id (int): ID пользователя
    
    Returns:
        bool: True если пользователь был удален, False если не найден
    """
    users = load_users()
    if str(user_id) in users:
        del users[str(user_id)]
        save_users(users)
        logger.info(f"Удален пользователь: {user_id}")
        return True
    return False

async def get_user_info(user_id: int) -> Optional[Dict]:
    """
    Возвращает информацию о пользователе.
    
    Args:
        user_id (int): ID пользователя
    
    Returns:
        Optional[Dict]: Информация о пользователе или None если не найден
    """
    users = load_users()
    return users.get(str(user_id))