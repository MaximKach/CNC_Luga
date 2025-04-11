# CNC Luga Telegram Bot

Telegram-бот для помощи в мире ЧПУ. Бот помогает с режимами резания, программированием ЧПУ и предоставляет юридическую поддержку.

## Функциональность

- **Валера**: Помощник по ЧПУ, металлообработке и программированию
- **Юрист**: Юридическая помощь по вопросам больничных, отпусков и переработок
- **Анонимные сообщения**: Возможность анонимно сообщить о проблемах на работе
- **Новости**: Обновления из мира ЧПУ
- **Рассылка**: Отправка сообщений всем пользователям бота

## Требования

- Python 3.8+
- Ubuntu 22.04 (для деплоя на сервер)

## Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/your-username/cnc_luga_bot.git
   cd cnc_luga_bot
   ```

2. Создайте виртуальное окружение и активируйте его:
   ```
   python3 -m venv venv
   source venv/bin/activate  # для Linux/Mac
   # или
   venv\Scripts\activate  # для Windows
   ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

4. Создайте файл .env на основе .env.example:
   ```
   cp .env.example .env
   ```

5. Отредактируйте файл .env и добавьте ваши токены и ключи.

6. Запустите бота:
   ```
   python cnc_luga_bot.py
   ```

### Деплой на сервер FirstVDS (Ubuntu 22.04)

1. Подключитесь к вашему серверу:
   ```
   ssh user@your-server
   ```

2. Клонируйте репозиторий или скопируйте файлы на сервер:
   ```
   git clone https://github.com/your-username/cnc_luga_bot.git /opt/cnc_luga_bot
   # или
   scp -r /path/to/local/cnc_luga_bot/* user@your-server:/opt/cnc_luga_bot/
   ```

3. Сделайте скрипт деплоя исполняемым и запустите его:
   ```
   chmod +x /opt/cnc_luga_bot/deploy.sh
   sudo /opt/cnc_luga_bot/deploy.sh
   ```

4. Следуйте инструкциям, которые будут выведены после завершения деплоя.

## Настройка .env

Файл .env содержит конфиденциальные данные и не должен попадать в репозиторий. Создайте его на основе .env.example:

```
cp .env.example .env
```

Затем отредактируйте файл .env и добавьте ваши реальные значения:

- **TBOT_TOKEN**: Токен вашего Telegram-бота (получите у @BotFather)
- **YANDEX_API_KEY**: Ключ API Яндекс GPT (получите в консоли Яндекс Облака)
- **YANDEX_FOLDER_ID**: ID каталога Яндекс Облака

## Управление ботом на сервере

После деплоя бот будет запущен как systemd сервис. Вы можете управлять им с помощью следующих команд:

```
# Проверка статуса
systemctl status cnc-luga-bot

# Перезапуск бота
systemctl restart cnc-luga-bot

# Просмотр логов
journalctl -u cnc-luga-bot -f
```

## Настройка домена и SSL

1. Отредактируйте конфигурацию Nginx:
   ```
   sudo nano /etc/nginx/sites-available/cnc-luga-bot
   ```

2. Замените `your-domain.com` на ваш реальный домен.

3. Настройте SSL с помощью Certbot:
   ```
   sudo certbot --nginx -d your-domain.com
   ```

## Лицензия

MIT 