import os
import logging

NEWS_FILE = "news.txt"

# Читаем новости из файла
def get_news():
    try:
        if not os.path.exists(NEWS_FILE):
            return "Новости отсутствуют."
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Ошибка при чтении новостей: {e}")
        return "Ошибка при загрузке новостей."

# Обновляем новости
def update_news(news_text):
    try:
        with open(NEWS_FILE, "w", encoding="utf-8") as f:
            f.write(news_text)
        logging.info("Новости успешно обновлены")
    except Exception as e:
        logging.error(f"Ошибка при обновлении новостей: {e}")
        raise