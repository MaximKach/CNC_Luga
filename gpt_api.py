import logging
import os
import aiohttp
import asyncio
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение ключей из переменных окружения
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# Проверяем, что ключи загружены
if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
    logger.error("❌ Ошибка: Не удалось загрузить YANDEX_API_KEY или YANDEX_FOLDER_ID из переменных окружения")
    raise ValueError("❌ Ошибка: Не удалось загрузить YANDEX_API_KEY или YANDEX_FOLDER_ID из переменных окружения")

# URL для запросов к API Яндекс GPT
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

async def yandex_gpt_request(prompt):
    """
    Асинхронная функция для отправки запроса к API Яндекс GPT.
    
    Args:
        prompt (str): Текст запроса для отправки в API
        
    Returns:
        str: Ответ от API или сообщение об ошибке
    """
    logger.info(f"Отправка запроса к API Яндекс GPT, длина промпта: {len(prompt)} символов")
    
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(YANDEX_GPT_URL, json=data, headers=headers, timeout=30) as response:
                if response.status == 200:
                    response_json = await response.json()
                    if "result" in response_json and "alternatives" in response_json["result"]:
                        answer = response_json["result"]["alternatives"][0]["text"]
                        logger.info(f"Получен ответ от API Яндекс GPT, длина ответа: {len(answer)} символов")
                        return answer
                    else:
                        logger.error(f"Некорректный ответ от API: {response_json}")
                        return "Ошибка обработки запроса. Проверь настройки API."
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка при запросе к API Яндекс GPT: {response.status} - {error_text}")
                    return f"Ошибка при запросе к API: {response.status}"
    except asyncio.TimeoutError:
        logger.error("Таймаут при запросе к API Яндекс GPT")
        return "Ошибка: запрос к API занял слишком много времени."
    except Exception as e:
        logger.error(f"Ошибка при запросе к API Яндекс GPT: {e}")
        return f"Ошибка при выполнении запроса к API: {str(e)}"

async def yandex_gpt_request_async(prompt, callback):
    """
    Асинхронная функция для отправки запроса к API Яндекс GPT с callback.
    
    Args:
        prompt (str): Текст запроса для отправки в API
        callback (function): Функция обратного вызова, которая будет вызвана с результатом
    """
    try:
        result = await yandex_gpt_request(prompt)
        await callback(result)
    except Exception as e:
        logger.error(f"Ошибка в асинхронном запросе к API Яндекс GPT: {e}")
        await callback(None)