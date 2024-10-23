#!/bin/bash

# Название виртуального окружения
VENV_NAME="myenv"

# Проверяем, установлен ли Python
if ! command -v python3 &>/dev/null; then
    echo "Python3 не установлен. Пожалуйста, установите Python3."
    sudo apt update && sudo apt install -y python3 python3-pip
    if [ $? -ne 0 ]; then
        echo "Ошибка установки Python3."
        exit 1
    fi
fi

# Проверяем, установлен ли pip
if ! command -v pip &>/dev/null; then
    echo "pip не установлен. Устанавливаем pip..."
    sudo apt install -y python3-pip
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

# Закрываем все screen-сессии с именем monitor_session
echo "Закрываем все существующие screen-сессии с именем monitor_session..."
screen -ls | grep monitor_session | awk '{print $1}' | xargs -n 1 screen -S {} -X quit

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

# Запуск monitor.py в screen
echo "Запускаем monitor.py в screen..."
screen -dmS monitor_session bash -c "python monitor.py; exec bash"

echo "Настройка завершена. Виртуальное окружение $VENV_NAME активировано и monitor.py запущен в screen сессии 'monitor_session'."
