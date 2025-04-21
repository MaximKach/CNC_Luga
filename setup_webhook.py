#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для настройки webhook для Telegram-бота.
Запустите этот скрипт после деплоя бота на сервер.
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
        logging.FileHandler("webhook_setup.log"),
        logging.StreamHandler()
    ]
)

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота из переменных окружения
TOKEN = os.getenv("TBOT_TOKEN")
if not TOKEN:
    logging.error("❌ Ошибка: Не удалось загрузить TBOT_TOKEN из переменных окружения")
    sys.exit(1)

def setup_webhook(domain):
    """
    Настройка webhook для Telegram-бота.
    
    Args:
        domain (str): Домен, на котором размещен бот
    
    Returns:
        bool: True, если webhook успешно настроен, иначе False
    """
    webhook_url = f"https://{domain}/webhook"
    api_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    
    try:
        # Сначала удаляем существующий webhook
        delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        requests.get(delete_url)
        logging.info("Существующий webhook удален")
        
        # Устанавливаем новый webhook
        response = requests.post(api_url, json={"url": webhook_url})
        response_data = response.json()
        
        if response_data.get("ok"):
            logging.info(f"✅ Webhook успешно настроен на {webhook_url}")
            return True
        else:
            logging.error(f"❌ Ошибка при настройке webhook: {response_data.get('description')}")
            return False
    except Exception as e:
        logging.error(f"❌ Ошибка при настройке webhook: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python setup_webhook.py your-domain.com")
        sys.exit(1)
    
    domain = sys.argv[1]
    setup_webhook(domain) 