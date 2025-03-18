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
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 100},
        "messages": [{"role": "user", "text": prompt}]
    }

    response = requests.post(url, json=data, headers=headers)
    
    try:
        response_json = response.json()
        if "result" in response_json and "alternatives" in response_json["result"]:
            return response_json["result"]["alternatives"][0]["message"]["text"]
        else:
            logging.error(f"Некорректный ответ от API: {response_json}")
            return "Ошибка обработки запроса. Проверь настройки API."
    except Exception as e:
        logging.error(f"Ошибка обработки JSON: {e}")
        return "Ошибка при разборе ответа от API."