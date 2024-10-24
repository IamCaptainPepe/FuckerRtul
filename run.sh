#!/bin/bash

# Название виртуального окружения
VENV_NAME="myenv"

# Проверяем, установлен ли Python
if ! command -v python3 &>/dev/null; then
    echo "Python3 не установлен. Пожалуйста, установите Python3."
    exit 1
fi

# Проверяем, установлен ли pip
if ! command -v pip &>/dev/null; then
    echo "pip не установлен. Пожалуйста, установите pip."
    exit 1
fi

# Проверяем, установлен ли screen и устанавливаем его, если нет
if ! command -v screen &>/dev/null; then
    echo "screen не установлен. Устанавливаем screen..."
    sudo apt update && sudo apt install -y screen
    if [ $? -ne 0 ]; then
        echo "Ошибка установки screen."
        exit 1
    fi
fi

# Закрываем все сессии monitor_session перед запуском
screen -ls | grep monitor_session | awk '{print $1}' | xargs -I {} screen -S {} -X quit

# Создаем виртуальное окружение
if [ ! -d "$VENV_NAME" ]; then
    echo "Создаем виртуальное окружение..."
    python3 -m venv "$VENV_NAME"
else
    echo "Виртуальное окружение уже существует."
fi

# Активируем виртуальное окружение
echo "Активируем виртуальное окружение..."
source "$VENV_NAME/bin/activate"

# Устанавливаем зависимости
if [ -f "requirements.txt" ]; then
    echo "Устанавливаем зависимости из requirements.txt..."
    pip install -r requirements.txt
else
    echo "Файл requirements.txt не найден."
    exit 1
fi

# Проверка наличия monitor.py
if [ ! -f "monitor.py" ]; then
    echo "Скрипт monitor.py не найден."
    exit 1
fi

# Запуск monitor.py
echo "Запускаем monitor.py..."
python3 main.py

echo "Настройка завершена. Виртуальное окружение $VENV_NAME активировано и monitor.py запущен."
