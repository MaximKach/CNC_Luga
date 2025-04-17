import logging
import os
import json
from typing import List, Dict, Optional
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        return {}
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке пользователей: {e}")
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
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователей: {e}")

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