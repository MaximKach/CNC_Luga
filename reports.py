REPORTS_FILE = "reports.txt"

# Сохраняем анонимное сообщение в файл
def save_report(user_id, message):
    with open(REPORTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id}: {message}\n")