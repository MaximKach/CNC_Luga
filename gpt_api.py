import logging
import requests
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем ключи из переменных окружения
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# Проверяем, что ключи загружены
if not YANDEX_API_KEY or not FOLDER_ID:
    logger.error("❌ Ошибка: Не удалось загрузить YANDEX_API_KEY или YANDEX_FOLDER_ID из переменных окружения")
    raise ValueError("❌ Ошибка: Не удалось загрузить YANDEX_API_KEY или YANDEX_FOLDER_ID из переменных окружения")

# Создаем пул потоков для асинхронных запросов
executor = ThreadPoolExecutor(max_workers=5)

# Отправляем запрос к YandexGPT и получаем ответ
def yandex_gpt_request(prompt):
    """
    Отправляет запрос к API Яндекс GPT и возвращает ответ.
    
    Args:
        prompt (str): Текст запроса для отправки в API
        
    Returns:
        str: Ответ от API или сообщение об ошибке
    """
    start_time = time.time()
    logger.info(f"Начало запроса к API Яндекс GPT, длина промпта: {len(prompt)} символов")
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": "2000"},
        "messages": [{"role": "user", "text": prompt}]
    }

    try:
        # Используем таймаут 30 секунд для запроса
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()  # Проверяем, что запрос успешен
        
        # Логируем время выполнения запроса
        elapsed_time = time.time() - start_time
        logger.info(f"Запрос к API Яндекс GPT выполнен за {elapsed_time:.2f} секунд")
        
        response_json = response.json()
        if "result" in response_json and "alternatives" in response_json["result"]:
            answer = response_json["result"]["alternatives"][0]["text"]
            logger.info(f"Получен ответ от API Яндекс GPT, длина ответа: {len(answer)} символов")
            return answer
        else:
            logger.error(f"Некорректный ответ от API: {response_json}")
            return "Ошибка обработки запроса. Проверь настройки API."
    except requests.Timeout:
        logger.error("Таймаут при запросе к YandexGPT API")
        return "Ошибка: запрос к API занял слишком много времени."
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к YandexGPT API: {e}")
        return "Ошибка при выполнении запроса к API."
    except Exception as e:
        logger.error(f"Ошибка обработки JSON: {e}")
        return "Ошибка при разборе ответа от API."

# Асинхронная версия запроса к API
def yandex_gpt_request_async(prompt, callback):
    """
    Асинхронно отправляет запрос к API Яндекс GPT и вызывает callback с результатом.
    
    Args:
        prompt (str): Текст запроса для отправки в API
        callback (function): Функция обратного вызова, которая будет вызвана с результатом
    """
    def _async_request():
        try:
            result = yandex_gpt_request(prompt)
            callback(result)
        except Exception as e:
            logger.error(f"Ошибка в асинхронном запросе к API Яндекс GPT: {e}")
            callback(None)
    
    # Запускаем запрос в отдельном потоке
    executor.submit(_async_request)