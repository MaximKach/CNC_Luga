#!/bin/bash

# Скрипт для автоматического деплоя Telegram-бота на сервер FirstVDS (Ubuntu 22.04)
# Автор: Claude
# Дата: 2024

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Начинаем деплой Telegram-бота на сервер...${NC}"

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Этот скрипт должен быть запущен с правами суперпользователя (sudo)${NC}"
  exit 1
fi

# Обновление системы
echo -e "${YELLOW}Обновление системы...${NC}"
apt update && apt upgrade -y

# Установка необходимых пакетов
echo -e "${YELLOW}Установка необходимых пакетов...${NC}"
apt install -y python3 python3-pip python3-venv git supervisor nginx

# Создание директории для бота
echo -e "${YELLOW}Создание директории для бота...${NC}"
mkdir -p /opt/cnc_luga_bot
cd /opt/cnc_luga_bot

# Копирование файлов проекта (предполагается, что файлы уже скопированы в /opt/cnc_luga_bot)
# Если файлы еще не скопированы, раскомментируйте и настройте следующие строки:
# echo -e "${YELLOW}Копирование файлов проекта...${NC}"
# git clone https://github.com/your-username/cnc_luga_bot.git /opt/cnc_luga_bot
# или
# scp -r /path/to/local/cnc_luga_bot/* user@your-server:/opt/cnc_luga_bot/

# Создание виртуального окружения
echo -e "${YELLOW}Создание виртуального окружения...${NC}"
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
echo -e "${YELLOW}Установка зависимостей...${NC}"
pip install -r requirements.txt

# Создание файла .env, если он не существует
if [ ! -f /opt/cnc_luga_bot/.env ]; then
  echo -e "${YELLOW}Создание файла .env...${NC}"
  echo "# Конфигурация Telegram-бота" > /opt/cnc_luga_bot/.env
  echo "TBOT_TOKEN=your_telegram_bot_token" >> /opt/cnc_luga_bot/.env
  echo "YANDEX_API_KEY=your_yandex_api_key" >> /opt/cnc_luga_bot/.env
  echo "YANDEX_FOLDER_ID=your_yandex_folder_id" >> /opt/cnc_luga_bot/.env
  echo -e "${RED}ВНИМАНИЕ: Необходимо отредактировать файл .env и добавить реальные значения токенов!${NC}"
fi

# Создание файлов для хранения данных, если они не существуют
touch /opt/cnc_luga_bot/users.txt
touch /opt/cnc_luga_bot/reports.txt
touch /opt/cnc_luga_bot/news.txt

# Настройка прав доступа
echo -e "${YELLOW}Настройка прав доступа...${NC}"
chown -R www-data:www-data /opt/cnc_luga_bot
chmod -R 755 /opt/cnc_luga_bot

# Создание systemd сервиса
echo -e "${YELLOW}Создание systemd сервиса...${NC}"
cat > /etc/systemd/system/cnc-luga-bot.service << EOF
[Unit]
Description=CNC Luga Telegram Bot
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/cnc_luga_bot
ExecStart=/opt/cnc_luga_bot/venv/bin/gunicorn --bind 0.0.0.0:8000 cnc_luga_bot:app
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=cnc-luga-bot

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и запуск сервиса
echo -e "${YELLOW}Перезагрузка systemd и запуск сервиса...${NC}"
systemctl daemon-reload
systemctl enable cnc-luga-bot
systemctl start cnc-luga-bot

# Настройка Nginx
echo -e "${YELLOW}Настройка Nginx...${NC}"
cat > /etc/nginx/sites-available/cnc-luga-bot << EOF
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Активация конфигурации Nginx
ln -sf /etc/nginx/sites-available/cnc-luga-bot /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Настройка SSL с Let's Encrypt (опционально)
echo -e "${YELLOW}Установка Certbot для SSL...${NC}"
apt install -y certbot python3-certbot-nginx

echo -e "${GREEN}Деплой завершен!${NC}"
echo -e "${YELLOW}Не забудьте:${NC}"
echo -e "1. Отредактировать файл .env и добавить реальные значения токенов"
echo -e "2. Настроить домен в конфигурации Nginx (/etc/nginx/sites-available/cnc-luga-bot)"
echo -e "3. Настроить SSL с помощью Certbot: ${GREEN}certbot --nginx -d your-domain.com${NC}"
echo -e "4. Проверить статус бота: ${GREEN}systemctl status cnc-luga-bot${NC}"
echo -e "5. Проверить логи бота: ${GREEN}journalctl -u cnc-luga-bot -f${NC}" 