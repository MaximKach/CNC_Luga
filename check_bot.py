#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки работоспособности Telegram-бота.
Запустите этот скрипт для проверки подключения к API Telegram и Яндекс GPT.
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_check.log"),
        logging.StreamHandler()
    ]
)

# Загрузка переменных окружения
load_dotenv()

# Получение токенов и ключей из переменных окружения
TOKEN = os.getenv("TBOT_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

def check_telegram_api():
    """
    Проверка подключения к API Telegram.
    
    Returns:
        bool: True, если подключение успешно, иначе False
    """
    if not TOKEN:
        logging.error("❌ Ошибка: Не удалось загрузить TBOT_TOKEN из переменных окружения")
        return False
    
    try:
        api_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(api_url)
        response_data = response.json()
        
        if response_data.get("ok"):
            bot_info = response_data.get("result", {})
            bot_name = bot_info.get("first_name", "Неизвестно")
            bot_username = bot_info.get("username", "Неизвестно")
            logging.info(f"✅ Подключение к API Telegram успешно. Бот: {bot_name} (@{bot_username})")
            return True
        else:
            logging.error(f"❌ Ошибка при подключении к API Telegram: {response_data.get('description')}")
            return False
    except Exception as e:
        logging.error(f"❌ Ошибка при подключении к API Telegram: {e}")
        return False

def check_yandex_api():
    """
    Проверка подключения к API Яндекс GPT.
    
    Returns:
        bool: True, если подключение успешно, иначе False
    """
    if not YANDEX_API_KEY or not FOLDER_ID:
        logging.error("❌ Ошибка: Не удалось загрузить YANDEX_API_KEY или YANDEX_FOLDER_ID из переменных окружения")
        return False
    
    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {"stream": False, "temperature": 0.8, "maxTokens": 100},
            "messages": [{"role": "user", "text": "Привет, это тестовый запрос."}]
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        
        if "result" in response_json and "alternatives" in response_json["result"]:
            logging.info("✅ Подключение к API Яндекс GPT успешно")
            return True
        else:
            logging.error(f"❌ Ошибка при подключении к API Яндекс GPT: {response_json}")
            return False
    except requests.Timeout:
        logging.error("❌ Таймаут при запросе к API Яндекс GPT")
        return False
    except requests.RequestException as e:
        logging.error(f"❌ Ошибка при запросе к API Яндекс GPT: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Ошибка при обработке ответа от API Яндекс GPT: {e}")
        return False

def check_files():
    """
    Проверка наличия необходимых файлов.
    
    Returns:
        bool: True, если все файлы существуют, иначе False
    """
    required_files = ["users.txt", "reports.txt", "news.txt"]
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logging.warning(f"⚠ Следующие файлы отсутствуют: {', '.join(missing_files)}")
        logging.info("Создаем отсутствующие файлы...")
        
        for file in missing_files:
            with open(file, "w") as f:
                f.write("")
            logging.info(f"✅ Файл {file} создан")
        
        return True
    else:
        logging.info("✅ Все необходимые файлы существуют")
        return True

if __name__ == "__main__":
    logging.info("🔍 Начинаем проверку работоспособности бота...")
    
    telegram_ok = check_telegram_api()
    yandex_ok = check_yandex_api()
    files_ok = check_files()
    
    if telegram_ok and yandex_ok and files_ok:
        logging.info("✅ Все проверки пройдены успешно. Бот готов к работе!")
        sys.exit(0)
    else:
        logging.error("❌ Некоторые проверки не пройдены. Пожалуйста, исправьте ошибки.")
        sys.exit(1) 