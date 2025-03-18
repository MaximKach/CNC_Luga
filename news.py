import os

NEWS_FILE = "news.txt"

# Читаем новости из файла
def get_news():
    if not os.path.exists(NEWS_FILE):
        return "Новости отсутствуют."
    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        return f.read()

# Обновляем новости
def update_news(news_text):
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        f.write(news_text)