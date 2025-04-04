import logging

USERS_FILE = "users.txt"

# Сохраняем ID нового пользователя в файл
def save_user(user_id):
    user_id = str(user_id)
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w") as f:
                f.write(user_id + "\n")
            logging.info(f"Создан файл {USERS_FILE}, добавлен пользователь {user_id}")
            return

        # Читаем существующих пользователей
        with open(USERS_FILE, "r+", encoding="utf-8") as f:
            users = f.read().splitlines()
            if user_id not in users:
                f.write(user_id + "\n")
                logging.info(f"Добавлен новый пользователь: {user_id}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя: {e}")
        raise

# Получаем список всех пользователей
def get_users():
    try:
        if not os.path.exists(USERS_FILE):
            return []
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except Exception as e:
        logging.error(f"Ошибка при чтении пользователей: {e}")
        return []