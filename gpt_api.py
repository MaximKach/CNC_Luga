import logging
import os
import aiohttp
import asyncio
import traceback
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Изменяем уровень на DEBUG для более подробных логов
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("gpt_api.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение ключей из переменных окружения
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# Проверяем, что ключи загружены
if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
    logger.critical("❌ Ошибка: Не удалось загрузить YANDEX_API_KEY или YANDEX_FOLDER_ID из переменных окружения")
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
    logger.debug(f"Отправка запроса к API Яндекс GPT, длина промпта: {len(prompt)} символов")
    logger.debug(f"Промпт: {prompt[:500]}...")  # Логируем первые 500 символов промпта
    
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
            logger.debug("Создана сессия aiohttp")
            async with session.post(YANDEX_GPT_URL, json=data, headers=headers, timeout=30) as response:
                logger.debug(f"Получен ответ от API, статус: {response.status}")
                if response.status == 200:
                    response_json = await response.json()
                    logger.debug(f"Получен JSON ответ: {response_json}")
                    if "result" in response_json and "alternatives" in response_json["result"]:
                        answer = response_json["result"]["alternatives"][0]["text"]
                        logger.info(f"Получен ответ от API Яндекс GPT, длина ответа: {len(answer)} символов")
                        logger.debug(f"Ответ: {answer[:500]}...")  # Логируем первые 500 символов ответа
                        return answer
                    else:
                        error_msg = f"Некорректный ответ от API: {response_json}"
                        logger.error(error_msg)
                        return "Ошибка обработки запроса. Проверь настройки API."
                else:
                    error_text = await response.text()
                    error_msg = f"Ошибка при запросе к API Яндекс GPT: {response.status} - {error_text}"
                    logger.error(error_msg)
                    return f"Ошибка при запросе к API: {response.status}"
    except asyncio.TimeoutError:
        error_msg = "Таймаут при запросе к API Яндекс GPT"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return "Ошибка: запрос к API занял слишком много времени."
    except Exception as e:
        error_msg = f"Ошибка при запросе к API Яндекс GPT: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return f"Ошибка при выполнении запроса к API: {str(e)}"

async def yandex_gpt_request_async(prompt, callback):
    """
    Асинхронная функция для отправки запроса к API Яндекс GPT с callback.
    
    Args:
        prompt (str): Текст запроса для отправки в API
        callback (function): Функция обратного вызова, которая будет вызвана с результатом
    """
    try:
        logger.debug(f"Начало асинхронного запроса к API Яндекс GPT")
        result = await yandex_gpt_request(prompt)
        logger.debug(f"Вызов callback с результатом длиной {len(result) if result else 0} символов")
        await callback(result)
    except Exception as e:
        error_msg = f"Ошибка в асинхронном запросе к API Яндекс GPT: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        await callback(None)