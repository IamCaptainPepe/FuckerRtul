#!/bin/bash

# Чтение настроек из файла settings.txt
SETTINGS_FILE="./settings.txt"

declare -A settings

while IFS='=' read -r key value; do
  settings["$key"]="$value"
done < <(grep -v '^#' "$SETTINGS_FILE" | grep -v '^$')

# Извлечение настроек
CONFIG_PATHS="${settings[config_paths]}"
PRIVATE_KEY_FILE="${settings[private_key_file]}"
USED_PRIVATE_KEYS_FILE="${settings[used_private_keys_file]}"
API_KEY="${settings[api_key]}"
BASE_URL="${settings[base_url]}"
METHOD_ID="${settings[method_id]}"
MIN_TRANSACTIONS="${settings[min_transactions]}"
MIN_BALANCE="${settings[min_balance]}"
CHECK_INTERVAL="${settings[check_interval]}"
WEB3_PROVIDER="${settings[web3_provider]}"
CONTAINERS="${settings[containers]}"
DEPLOY_JSON_PATH="${settings[deploy_json_path]}"
CALL_CONTRACT_PATH="${settings[call_contract_path]}"
DEPLOY_CONTRACTS_PATH="${settings[deploy_contracts_path]}"
BASE_DEPLOY_PATH="${settings[base_deploy_path]}"

# Запрос приватного ключа у пользователя
read -s -p "Введите ваш приватный ключ: " PRIVATE_KEY
echo

# Проверка ввода приватного ключа
if [ -z "$PRIVATE_KEY" ]; then
  echo "Приватный ключ не введён. Прерывание выполнения."
  exit 1
fi

# Функция для остановки контейнеров
stop_containers() {
  echo "Остановка Docker-контейнеров..."
  IFS=',' read -ra container_array <<< "$CONTAINERS"
  for CONTAINER in "${container_array[@]}"; do
    echo "Остановка контейнера: $CONTAINER"
    docker stop "$CONTAINER" || echo "Не удалось остановить контейнер $CONTAINER"
  done
}

# Функция для запуска контейнеров
start_containers() {
  echo "Запуск Docker-контейнеров..."
  cd "$BASE_DEPLOY_PATH/deploy" || { echo "Не удалось перейти в директорию с docker-compose.yaml"; exit 1; }
  docker compose up -d
}

# Остановка контейнеров
stop_containers

# Переход в директорию и обновление репозитория
echo "Переход в директорию $BASE_DEPLOY_PATH"
cd "$BASE_DEPLOY_PATH" || { echo "Не удалось перейти в директорию."; exit 1; }

echo "Сброс локальных изменений и очистка неотслеживаемых файлов..."
git reset --hard HEAD
git clean -fd

echo "Обновление репозитория..."
if git pull; then
  echo "Репозиторий успешно обновлён."
else
  echo "Ошибка при обновлении репозитория."
  exit 1
fi

# Обновление версии в конфигурационных файлах
echo "Обновление версии на 1.4.0 в конфигурационных файлах..."
CONFIG_FILES=(${CONFIG_PATHS//,/ })
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
  if [ -f "$CONFIG_FILE" ]; then
    echo "Обновление версии в файле $CONFIG_FILE"
    jq '.version = "1.4.0"' "$CONFIG_FILE" > temp_config.json && mv temp_config.json "$CONFIG_FILE"
  else
    echo "Файл конфигурации $CONFIG_FILE не найден."
  fi
done

# Обновление приватного ключа в конфигурационных файлах
echo "Обновление приватного ключа в конфигурационных файлах..."
for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
  if [ -f "$CONFIG_FILE" ]; then
    echo "Обновление приватного ключа в файле $CONFIG_FILE"
    jq --arg key "$PRIVATE_KEY" '.chain.wallet.private_key = $key' "$CONFIG_FILE" > temp_config.json && mv temp_config.json "$CONFIG_FILE"
  else
    echo "Файл конфигурации $CONFIG_FILE не найден."
  fi
done

# Запуск контейнеров
start_containers

# Деплой контрактов
echo "Деплой контрактов..."
cd "$BASE_DEPLOY_PATH" || { echo "Не удалось перейти в базовую директорию деплоя."; exit 1; }

# Выполнение команды деплоя контракта
project=hello-world make deploy-contracts

# Ожидание для завершения деплоя
echo "Ожидание завершения деплоя..."
sleep 30

# Проверка существования файла с результатами деплоя
if [ -f "$DEPLOY_JSON_PATH" ]; then
  # Извлечение адреса контракта из JSON-файла
  CONTRACT_ADDRESS=$(jq -r '.. | objects | select(has("contractAddress")) | .contractAddress' "$DEPLOY_JSON_PATH")
  if [ -n "$CONTRACT_ADDRESS" ]; then
    echo "Новый адрес контракта: $CONTRACT_ADDRESS"

    # Преобразование адреса в формат с контрольной суммой (checksummed address)
    CHECKSUMMED_ADDRESS=$(python3 -c "from web3 import Web3; print(Web3.toChecksumAddress('$CONTRACT_ADDRESS'))")
    echo "Адрес контракта в checksummed формате: $CHECKSUMMED_ADDRESS"

    # Обновление файла CallContract.s.sol новым адресом контракта
    if [ -f "$CALL_CONTRACT_PATH" ]; then
      echo "Обновление файла CallContract.s.sol новым адресом контракта..."
      # Используем более точное регулярное выражение и другой разделитель
      sed -i "s|\(SaysGM saysGm = SaysGM(\).*);\|\1$CHECKSUMMED_ADDRESS);|" "$CALL_CONTRACT_PATH"
    else
      echo "Файл CallContract.s.sol не найден по пути $CALL_CONTRACT_PATH"
    fi

    # Ожидание перед вызовом метода контракта
    echo "Ожидание перед вызовом метода контракта..."
    sleep 10

    # Вызов метода контракта
    echo "Вызов метода контракта..."
    project=hello-world make call-contract

  else
    echo "Адрес нового контракта не найден в $DEPLOY_JSON_PATH"
  fi
else
  echo "Файл результатов деплоя не найден по пути $DEPLOY_JSON_PATH"
fi

# Перезапуск контейнеров
echo "Перезапуск Docker-контейнеров..."
stop_containers
start_containers

echo "Готово."
