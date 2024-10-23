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

# Создаем виртуальное окружение
if [ ! -d "$VENV_NAME" ]; then
    echo "Создаем виртуальное окружение..."
    python3 -m venv "$VENV_NAME"
else
    echo "Виртуальное окружение уже существует. Удалите директорию $VENV_NAME, если хотите создать новое."
    exit 1
fi

# Активируем виртуальное окружение
echo "Активируем виртуальное окружение..."
source "$VENV_NAME/bin/activate"

# Устанавливаем зависимости
if [ -f "requirements.txt" ]; then
    echo "Устанавливаем зависимости из requirements.txt..."
    pip install -r requirements.txt
else
    echo "Файл requirements.txt не найден. Убедитесь, что он находится в том же каталоге, что и скрипт."
    exit 1
fi

echo "Настройка завершена. Виртуальное окружение $VENV_NAME активировано."
echo "Теперь вы можете запускать ваш скрипт с помощью команды: python <ваш_скрипт.py>"
