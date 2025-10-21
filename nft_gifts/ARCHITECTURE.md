# 🏗️ Архитектура NFT Gift Shop

## Обзор системы

NFT Gift Shop - это полноценная web-приложение с интеграцией Telegram Bot для покупки и передачи NFT подарков.

```
┌─────────────────────────────────────────────────────────────────┐
│                         NFT GIFT SHOP                            │
│                      Архитектура системы                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Клиенты    │         │   Telegram   │         │    Админ     │
│              │         │     Users    │         │   (IP only)  │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │ HTTP                   │ Telegram API           │ HTTPS
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Frontend   │    │  Telegram    │    │    Admin     │      │
│  │   Routes     │    │     Bot      │    │    Panel     │      │
│  │  (Jinja2)    │    │  (aiogram)   │    │  (IP Check)  │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                            │                                    │
│                     ┌──────▼───────┐                            │
│                     │   Business   │                            │
│                     │    Logic     │                            │
│                     └──────┬───────┘                            │
│                            │                                    │
│                     ┌──────▼───────┐                            │
│                     │  SQLAlchemy  │                            │
│                     │     ORM      │                            │
│                     └──────┬───────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
                      ┌──────▼───────┐
                      │   SQLite     │
                      │   Database   │
                      └──────────────┘
```

## Компоненты системы

### 1. Frontend Layer (Веб-интерфейс)

**Технологии:**
- FastAPI (ASGI фреймворк)
- Jinja2 (шаблонизатор)
- HTML5 + CSS3
- Responsive Design

**Маршруты:**
- `/` - Главная страница с каталогом
- `/gift/{id}` - Детальная страница подарка
- `/api/gifts` - JSON API для получения подарков

**Шаблоны:**
```
templates/
├── base.html              # Базовый шаблон
├── index.html             # Главная страница
├── gift_detail.html       # Детали подарка
└── 404.html, etc.         # Страницы ошибок
```

### 2. Telegram Bot Layer

**Технологии:**
- python-telegram-bot 21.9
- Async/await architecture
- InlineKeyboard навигация

**Функционал:**
```python
NFTGiftBot
├── start_command()           # /start - приветствие
├── view_gifts_callback()     # Просмотр каталога
├── show_gift()               # Показ конкретного подарка
├── buy_gift()                # Покупка NFT
├── send_gift_callback()      # Начало отправки
├── process_gift_sending()    # Передача подарка
└── my_gifts_callback()       # Мои подарки
```

**Состояния бота:**
- Навигация по каталогу
- Процесс покупки
- Отправка подарка (ожидание получателя)
- Просмотр коллекции

### 3. Admin Panel Layer

**Технологии:**
- IP-based аутентификация
- Cookie-based сессии
- CRUD операции

**Безопасность:**
```python
# Двухуровневая защита
1. check_admin_ip()         # Проверка IP адреса
2. verify_admin_session()   # Проверка сессии
```

**Функционал:**
- Dashboard с статистикой
- Управление NFT подарками (CRUD)
- Просмотр пользователей
- История покупок и передач

**Маршруты:**
```
/admin/login         # Вход
/admin/dashboard     # Панель управления
/admin/gifts         # Список подарков
/admin/gifts/add     # Добавить
/admin/gifts/edit    # Редактировать
/admin/gifts/delete  # Удалить
/admin/users         # Пользователи
/admin/purchases     # История
```

### 4. Database Layer

**Технология:** SQLite + SQLAlchemy (Async)

**Модели данных:**

```python
NFTGift (nft_gifts)
├── id: Integer (PK)
├── title: String
├── description: Text
├── gif_url: String
├── file_id: String (Telegram)
├── price: Float
├── is_active: Boolean
├── created_at: DateTime
└── updated_at: DateTime

User (users)
├── id: Integer (PK)
├── telegram_id: Integer (Unique)
├── username: String
├── first_name: String
├── last_name: String
└── created_at: DateTime

NFTPurchase (nft_purchases)
├── id: Integer (PK)
├── user_id: Integer (FK)
├── nft_gift_id: Integer (FK)
├── recipient_telegram_id: Integer (FK)
├── status: String (pending/completed/sent)
├── transaction_hash: String
├── created_at: DateTime
└── sent_at: DateTime
```

**Связи:**
```
User 1──∞ NFTPurchase
NFTGift 1──∞ NFTPurchase
User 1──∞ ReceivedGifts (через recipient_telegram_id)
```

## Потоки данных

### 1. Покупка NFT подарка

```
User открывает бота
    │
    ├── /start
    │
    ├── "Просмотреть подарки"
    │
    ├── Бот получает список из БД
    │   SELECT * FROM nft_gifts WHERE is_active=True
    │
    ├── Показывает GIF + описание
    │
    ├── User нажимает "Купить"
    │
    ├── Создается NFTPurchase
    │   INSERT INTO nft_purchases (...)
    │
    ├── Генерируется transaction_hash
    │   SHA256(user_id + gift_id + timestamp)
    │
    └── Подтверждение покупки
```

### 2. Передача подарка

```
User выбирает подарок для отправки
    │
    ├── "Отправить подарок"
    │
    ├── Бот запрашивает получателя
    │   "Перешлите сообщение от получателя"
    │
    ├── User пересылает сообщение
    │
    ├── Бот извлекает telegram_id получателя
    │
    ├── Обновляет NFTPurchase
    │   UPDATE nft_purchases SET
    │   recipient_telegram_id = ?,
    │   status = 'sent',
    │   sent_at = NOW()
    │
    ├── Отправляет GIF получателю
    │   bot.send_animation(recipient_id, ...)
    │
    └── Подтверждение отправки
```

### 3. Работа админ-панели

```
Admin открывает /admin/login
    │
    ├── Проверка IP адреса
    │   if client_ip != ADMIN_IP: FORBIDDEN
    │
    ├── Ввод логина/пароля
    │
    ├── Создание сессии
    │   session_token = SHA256(username:password)
    │   Set-Cookie: admin_session=token
    │
    ├── /admin/dashboard
    │
    ├── Любой запрос проходит через:
    │   1. check_admin_ip()
    │   2. verify_admin_session()
    │
    └── Доступ к функционалу
```

## Безопасность

### 1. Аутентификация

```python
# IP-based контроль доступа
ADMIN_IP = "80.64.26.253"

def check_admin_ip(request):
    client_ip = request.client.host
    return client_ip == ADMIN_IP or client_ip == "127.0.0.1"
```

### 2. Сессии

```python
# Cookie-based сессии
session_token = hashlib.sha256(
    f"{username}:{password}".encode()
).hexdigest()

response.set_cookie(
    key="admin_session",
    value=session_token,
    httponly=True  # Защита от XSS
)
```

### 3. SQL Injection защита

```python
# Использование ORM вместо raw SQL
result = await db.execute(
    select(NFTGift).where(NFTGift.id == gift_id)
)
# Параметры автоматически экранируются
```

### 4. Валидация данных

```python
# Pydantic модели
class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    ADMIN_IP: str
    # Автоматическая валидация типов
```

## Масштабируемость

### Текущая архитектура (MVP)
- SQLite (до 100,000 записей)
- Async I/O (высокая производительность)
- In-memory сессии

### Для продакшена (рекомендации)

```
1. База данных:
   SQLite → PostgreSQL / MySQL
   - Поддержка concurrent writes
   - Лучшая производительность
   - Надежность

2. Сессии:
   Memory → Redis
   - Persistence
   - Distributed sessions
   - Caching

3. Файлы:
   Local → S3 / CDN
   - Масштабируемость
   - Быстрая доставка
   - Backup

4. Приложение:
   Single → Multiple instances
   - Load balancer (nginx)
   - Horizontal scaling
   - High availability
```

## Развертывание

### Development

```bash
python main.py
# Uvicorn с hot reload
```

### Production

```bash
# Systemd service
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Nginx reverse proxy
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

# SSL/TLS
certbot --nginx -d yourdomain.com
```

## Мониторинг и логирование

```python
# Рекомендуется добавить:

1. Logging:
   import logging
   logging.basicConfig(level=logging.INFO)
   
2. Metrics:
   - Количество пользователей
   - Количество покупок
   - Активность бота
   
3. Error tracking:
   - Sentry integration
   - Error notifications
```

## API Documentation

FastAPI автоматически генерирует документацию:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Расширения (Future)

Возможные улучшения:

1. **Payment Integration**
   - TON Wallet
   - Crypto payments
   - Real blockchain

2. **Advanced Features**
   - NFT Marketplace
   - Auction system
   - Rarity system
   - Collections

3. **Social Features**
   - Friends system
   - Gift history
   - Achievements
   - Leaderboards

4. **Analytics**
   - User behavior
   - Popular gifts
   - Revenue tracking

## Зависимости

```
Core:
├── fastapi          # Web framework
├── uvicorn          # ASGI server
├── sqlalchemy       # ORM
└── python-telegram-bot  # Telegram API

Templates & Static:
├── jinja2           # Template engine
├── aiofiles         # Async file operations
└── python-multipart # Form handling

Config & Utils:
├── pydantic         # Validation
├── python-dotenv    # Environment
└── aiosqlite        # Async SQLite
```

---

**Документация актуальна на**: 2024-10-21
**Версия проекта**: 1.0.0
