# 🚀 Руководство по развертыванию NFT Gift Shop

## Содержание
1. [Локальная разработка](#локальная-разработка)
2. [Развертывание на VPS](#развертывание-на-vps)
3. [Docker развертывание](#docker-развертывание)
4. [Настройка Telegram Bot](#настройка-telegram-bot)
5. [Настройка SSL](#настройка-ssl)
6. [Мониторинг и обслуживание](#мониторинг-и-обслуживание)

---

## Локальная разработка

### Требования
- Python 3.9+
- pip
- git

### Установка

```bash
# Клонирование проекта
git clone <repository-url>
cd nft_gifts

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env файл

# Добавление демо-данных
python add_demo_gifts.py

# Запуск
python main.py
```

Приложение будет доступно на: http://localhost:8000

---

## Развертывание на VPS

### 1. Подготовка сервера (Ubuntu 22.04)

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install python3.10 python3.10-venv python3-pip nginx git -y

# Создание пользователя для приложения
sudo useradd -m -s /bin/bash nftgifts
sudo su - nftgifts
```

### 2. Установка приложения

```bash
# Клонирование проекта
cd /home/nftgifts
git clone <repository-url> nft_gifts
cd nft_gifts

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка .env
nano .env
```

Измените следующие параметры в `.env`:

```env
TELEGRAM_BOT_TOKEN=8494126901:AAE0fbTFsQosqG1YpoGjx9SkIM41PzB64RQ
ADMIN_IP=80.64.26.253  # Ваш реальный IP
ADMIN_PASSWORD=strong_password_here
HOST=127.0.0.1
PORT=8000
```

### 3. Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/nft-gifts.service
```

Содержимое файла:

```ini
[Unit]
Description=NFT Gift Shop Application
After=network.target

[Service]
Type=simple
User=nftgifts
Group=nftgifts
WorkingDirectory=/home/nftgifts/nft_gifts
Environment="PATH=/home/nftgifts/nft_gifts/venv/bin"
ExecStart=/home/nftgifts/nft_gifts/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nft-gifts
sudo systemctl start nft-gifts
sudo systemctl status nft-gifts
```

### 4. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/nft-gifts
```

Содержимое:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Ограничение доступа к админке по IP
    location /admin {
        allow 80.64.26.253;
        deny all;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Кэширование статики
    location /static {
        alias /home/nftgifts/nft_gifts/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Активация конфигурации:

```bash
sudo ln -s /etc/nginx/sites-available/nft-gifts /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Docker развертывание

### Dockerfile

Создайте `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание директорий
RUN mkdir -p static/css templates

# Экспорт порта
EXPOSE 8000

# Запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ADMIN_IP=${ADMIN_IP}
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    volumes:
      - ./nft_gifts.db:/app/nft_gifts.db
      - ./static:/app/static
      - ./templates:/app/templates
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

### Запуск с Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

---

## Настройка Telegram Bot

### 1. Создание бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и создайте бота
4. Скопируйте токен

### 2. Настройка команд бота

Отправьте `/setcommands` в BotFather и добавьте:

```
start - Главное меню
gifts - Каталог подарков
my - Мои подарки
help - Помощь
```

### 3. Настройка webhook (опционально)

Для продакшена рекомендуется использовать webhook вместо polling:

```python
# В telegram_bot.py
async def set_webhook(app: Application):
    await app.bot.set_webhook(
        url=f"https://yourdomain.com/webhook/{TELEGRAM_BOT_TOKEN}",
        drop_pending_updates=True
    )

# В main.py
@app.post(f"/webhook/{settings.TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, nft_bot.application.bot)
    await nft_bot.application.process_update(update)
    return {"ok": True}
```

---

## Настройка SSL

### Использование Certbot (Let's Encrypt)

```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение сертификата
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

Certbot автоматически настроит nginx для HTTPS.

### Ручная настройка SSL

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... остальная конфигурация
}

# Редирект с HTTP на HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Мониторинг и обслуживание

### 1. Логирование

Просмотр логов приложения:

```bash
# systemd логи
sudo journalctl -u nft-gifts -f

# Nginx логи
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Мониторинг ресурсов

```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Сетевые подключения
netstat -tulpn | grep :8000
```

### 3. Backup базы данных

```bash
# Ежедневный backup
sudo crontab -e

# Добавьте строку:
0 2 * * * cp /home/nftgifts/nft_gifts/nft_gifts.db /backups/nft_gifts_$(date +\%Y\%m\%d).db
```

### 4. Обновление приложения

```bash
cd /home/nftgifts/nft_gifts
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart nft-gifts
```

### 5. Мониторинг с помощью скриптов

Создайте скрипт мониторинга:

```bash
#!/bin/bash
# check_health.sh

curl -f http://localhost:8000/ > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Service is down, restarting..."
    sudo systemctl restart nft-gifts
    # Отправить уведомление
fi
```

Добавьте в crontab:

```bash
*/5 * * * * /home/nftgifts/check_health.sh
```

---

## Переход с SQLite на PostgreSQL (рекомендуется для продакшена)

### 1. Установка PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib -y
```

### 2. Создание базы данных

```bash
sudo -u postgres psql
CREATE DATABASE nft_gifts;
CREATE USER nftgifts_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE nft_gifts TO nftgifts_user;
\q
```

### 3. Обновление requirements.txt

```txt
# Добавьте:
asyncpg
psycopg2-binary
```

### 4. Изменение .env

```env
DATABASE_URL=postgresql+asyncpg://nftgifts_user:strong_password@localhost/nft_gifts
```

### 5. Миграция данных

```bash
# Экспорт из SQLite
sqlite3 nft_gifts.db .dump > dump.sql

# Импорт в PostgreSQL (потребуется адаптация SQL)
psql -U nftgifts_user -d nft_gifts -f dump.sql
```

---

## Устранение неполадок

### Проблема: Бот не отвечает

**Решение:**
```bash
# Проверьте логи
sudo journalctl -u nft-gifts -n 50

# Проверьте токен
echo $TELEGRAM_BOT_TOKEN

# Перезапустите сервис
sudo systemctl restart nft-gifts
```

### Проблема: Не работает админ-панель

**Решение:**
1. Проверьте IP в логах nginx
2. Убедитесь, что IP в .env совпадает
3. Проверьте X-Forwarded-For в nginx

### Проблема: Высокая нагрузка на CPU

**Решение:**
```bash
# Увеличьте количество workers
# В systemd service файле:
ExecStart=... --workers 8

# Оптимизируйте запросы к БД
# Добавьте индексы в database.py
```

---

## Контрольный список развертывания

- [ ] Сервер настроен и обновлен
- [ ] Python и зависимости установлены
- [ ] Приложение склонировано и настроено
- [ ] .env файл заполнен корректными данными
- [ ] База данных инициализирована
- [ ] Systemd сервис создан и запущен
- [ ] Nginx настроен и работает
- [ ] SSL сертификат установлен
- [ ] Telegram бот протестирован
- [ ] Админ-панель доступна
- [ ] Backup настроен
- [ ] Мониторинг включен
- [ ] Firewall настроен (ufw/iptables)
- [ ] Логирование работает

---

**Удачного развертывания! 🚀**

По вопросам: создайте Issue в репозитории
