USERS_FILE = "users.txt"

# Сохраняем ID нового пользователя в файл
def save_user(user_id):
    user_id = str(user_id)
    try:
        with open(USERS_FILE, "r+") as f:
            users = f.read().splitlines()
            if user_id not in users:
                f.write(user_id + "\n")
    except FileNotFoundError:
        with open(USERS_FILE, "w") as f:
            f.write(user_id + "\n")

# Получаем список всех пользователей
def get_users():
    try:
        with open(USERS_FILE, "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []