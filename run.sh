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

# Проверяем, установлен ли screen
if ! command -v screen &>/dev/null; then
    echo "screen не установлен. Установите его командой: sudo apt install screen"
    exit 1
fi

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
