#!/bin/bash

# Скрипт запуска NFT Gift Shop

echo "🎁 Запуск NFT Gift Shop..."

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📚 Установка зависимостей..."
pip install -r requirements.txt

# Создание директорий
echo "📁 Создание необходимых директорий..."
mkdir -p static/css
mkdir -p templates

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "⚙️ Создание .env файла..."
    cp .env.example .env
    echo "⚠️ Не забудьте настроить .env файл!"
fi

# Запуск приложения
echo "🚀 Запуск сервера..."
python main.py
