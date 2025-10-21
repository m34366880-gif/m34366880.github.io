# NFT Gifts Store (FastAPI)

Простое приложение магазина NFT-подарков с интеграцией Telegram Bot API, админ-панелью (IP + Basic Auth), шаблонами и статикой.

## Запуск

1) Создайте виртуальное окружение и установите зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Установите переменные окружения при необходимости:

```bash
export BOT_TOKEN="8494126901:AAE0fbTFsQosqG1YpoGjx9SkIM41PzB64RQ"
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin123
export ADMIN_ALLOWED_IP=80.64.26.253
```

3) Запустите сервер:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4) Откройте:
- Главная: http://localhost:8000/
- Админ: http://localhost:8000/admin (доступ только с IP 80.64.26.253 и Basic Auth)
- Telegram GIFs: http://localhost:8000/admin/telegram

## Примечания
- Для предпросмотра анимаций из Telegram отправьте вашему боту в диалог анимацию (GIF/animation). Страница `/admin/telegram` подтянет их через `getUpdates`. Если у бота настроен webhook, `getUpdates` вернёт пустой список.
- Отправка подарка осуществляется методом `sendAnimation` в Telegram: укажите целевой `chat_id` (или `@username` для каналов/групп). Пользователь должен начать диалог с вашим ботом.
- БД SQLite создаётся автоматически в файле `app.db`.
