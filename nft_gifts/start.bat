@echo off
echo 🎁 Запуск NFT Gift Shop...

REM Проверка виртуального окружения
if not exist "venv" (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
)

REM Активация виртуального окружения
echo 🔧 Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Установка зависимостей
echo 📚 Установка зависимостей...
pip install -r requirements.txt

REM Создание директорий
echo 📁 Создание необходимых директорий...
if not exist "static\css" mkdir static\css
if not exist "templates" mkdir templates

REM Проверка .env файла
if not exist ".env" (
    echo ⚙️ Создание .env файла...
    copy .env.example .env
    echo ⚠️ Не забудьте настроить .env файл!
)

REM Запуск приложения
echo 🚀 Запуск сервера...
python main.py

pause
