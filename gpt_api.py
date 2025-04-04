import logging
import requests
from config import YANDEX_API_KEY, FOLDER_ID

# Отправляем запрос к YandexGPT и получаем ответ
def yandex_gpt_request(prompt):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
        "completionOptions": {"stream": False, "temperature": 0.8, "maxTokens": 1000},
        "messages": [{"role": "user", "text": prompt}]
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)  # Добавляем таймаут 30 секунд
        response.raise_for_status()  # Проверяем, что запрос успешен
        response_json = response.json()
        if "result" in response_json and "alternatives" in response_json["result"]:
            return response_json["result"]["alternatives"][0]["message"]["text"]
        else:
            logging.error(f"Некорректный ответ от API: {response_json}")
            return "Ошибка обработки запроса. Проверь настройки API."
    except requests.Timeout:
        logging.error("Таймаут при запросе к YandexGPT API")
        return "Ошибка: запрос к API занял слишком много времени."
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе к YandexGPT API: {e}")
        return "Ошибка при выполнении запроса к API."
    except Exception as e:
        logging.error(f"Ошибка обработки JSON: {e}")
        return "Ошибка при разборе ответа от API."