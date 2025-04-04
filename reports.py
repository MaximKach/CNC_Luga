import logging

REPORTS_FILE = "reports.txt"

# Сохраняем анонимное сообщение в файл
def save_report(user_id, message):
    try:
        with open(REPORTS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id}: {message}\n")
        logging.info(f"Сообщение от {user_id} сохранено")
    except Exception as e:
        logging.error(f"Ошибка при сохранении отчёта: {e}")
        raise