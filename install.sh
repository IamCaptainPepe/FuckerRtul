#!/bin/bash

set -e  # Прерывать выполнение скрипта при ошибках

# Чтение настроек из файла settings.txt
SETTINGS_FILE="./settings.txt"

declare -A settings

while IFS='=' read -r key value; do
  settings["$key"]="$value"
done < <(grep -v '^#' "$SETTINGS_FILE" | grep -v '^$')

# Извлечение настроек
CONFIG_PATHS="${settings[config_paths]}"
CONTAINERS="${settings[containers]}"
BASE_DEPLOY_PATH="${settings[base_deploy_path]}"

# Новый адрес для параметра "registry_address"
REGISTRY_ADDRESS="0x3B1554f346DFe5c482Bb4BA31b880c1C18412170"

# Новое значение для "rpc_url"
NEW_RPC_URL="https://mainnet.base.org/"

# Запрос приватного ключа у пользователя
read -s -p "Введите ваш приватный ключ: " PRIVATE_KEY
echo

# Проверка ввода приватного ключа
if [ -z "$PRIVATE_KEY" ]; then
  echo "Приватный ключ не введён. Прерывание выполнения."
  exit 1
fi

# 1. Установка Foundry
echo "Установка Foundry..."

# Проверка, установлен ли Foundry
if ! command -v foundryup &> /dev/null; then
  # Переходим в домашний каталог
  cd ~ || exit
  mkdir -p foundry
  cd foundry || exit

  # Установка Foundry
  curl -L https://foundry.paradigm.xyz | bash
  source ~/.bashrc
  foundryup
else
  echo "Foundry уже установлен."
fi

# 2. Клонирование репозитория, если директория не существует
if [ ! -d "$BASE_DEPLOY_PATH" ]; then
  echo "Клонирование репозитория infernet-container-starter..."
  git clone https://github.com/ritual-net/infernet-container-starter "$BASE_DEPLOY_PATH"
fi

# Переход в директорию репозитория
cd "$BASE_DEPLOY_PATH" || { echo "Не удалось перейти в директорию $BASE_DEPLOY_PATH"; exit 1; }

# 3. Удаление проблемных директорий
echo "Удаление проблемных директорий..."
rm -rf projects/hello-world/contracts/lib/forge-std
rm -rf lib/forge-std

# 4. Инициализация проекта и установка зависимостей
echo "Инициализация проекта и установка зависимостей..."
cd projects/hello-world/contracts || { echo "Не удалось перейти в директорию контрактов."; exit 1; }

# Инициализация проекта, если папка lib не существует
if [ ! -d "lib" ]; then
  forge init --force
fi

# Установка зависимостей
forge install --no-commit foundry-rs/forge-std
forge install --no-commit ritual-net/infernet-sdk

# 5. Возврат в базовую директорию
cd "$BASE_DEPLOY_PATH" || exit

# 6. Выполнение команды project=hello-world make deploy-container
echo "Выполнение команды project=hello-world make deploy-container..."
project=hello-world make deploy-container

# 7. Обновление конфигурационных файлов
echo "Обновление конфигурационных файлов..."
CONFIG_FILES=(${CONFIG_PATHS//,/ })

for CONFIG_FILE in "${CONFIG_FILES[@]}"; do
  if [ -f "$CONFIG_FILE" ]; then
    echo "Обновление файла $CONFIG_FILE"

    # Обновление полей в конфигурационном файле
    jq --arg version "1.4.0" \
       --arg key "$PRIVATE_KEY" \
       --arg reg_addr "$REGISTRY_ADDRESS" \
       --arg rpc_url "$NEW_RPC_URL" \
       '.version = $version |
        .chain.wallet.private_key = $key |
        .registry_address = $reg_addr |
        .chain.provider.rpc_url = $rpc_url |
        .snapshot_sync.sleep = 3 |
        .snapshot_sync.batch_size = 800 |
        .snapshot_sync.sync_period = 30 |
        .trail_head_blocks = 3' \
       "$CONFIG_FILE" > temp_config.json && mv temp_config.json "$CONFIG_FILE"
  else
    echo "Файл конфигурации $CONFIG_FILE не найден."
  fi
done

# 8. Обновление файла docker-compose.yaml
DOCKER_COMPOSE_FILE="$BASE_DEPLOY_PATH/deploy/docker-compose.yaml"
if [ -f "$DOCKER_COMPOSE_FILE" ]; then
  echo "Обновление файла docker-compose.yaml..."
  sed -i 's/image: infernode:.*/image: infernode:1.4.0/' "$DOCKER_COMPOSE_FILE"
else
  echo "Файл docker-compose.yaml не найден."
fi

# 9. Обновление registry_address в Deploy.s.sol и других файлах
DEPLOY_SOL_FILE="$BASE_DEPLOY_PATH/projects/hello-world/contracts/script/Deploy.s.sol"
if [ -f "$DEPLOY_SOL_FILE" ]; then
  echo "Обновление файла Deploy.s.sol..."
  sed -i "s/address registry =.*/address registry = $REGISTRY_ADDRESS;/" "$DEPLOY_SOL_FILE"
else
  echo "Файл Deploy.s.sol не найден."
fi

# Обновление Makefile
MAKEFILE="$BASE_DEPLOY_PATH/projects/hello-world/contracts/Makefile"
if [ -f "$MAKEFILE" ]; then
  echo "Обновление Makefile..."
  sed -i "s|RPC_URL=.*|RPC_URL=$NEW_RPC_URL|" "$MAKEFILE"
  sed -i "s|SENDER_KEY=.*|SENDER_KEY=$PRIVATE_KEY|" "$MAKEFILE"
else
  echo "Makefile не найден."
fi

# 10. Перезапуск Docker-контейнеров
echo "Перезапуск Docker-контейнеров..."
docker restart infernet-anvil || echo "Контейнер infernet-anvil не запущен."
docker restart hello-world || echo "Контейнер hello-world не запущен."
docker restart infernet-node || echo "Контейнер infernet-node не запущен."

# 11. Деплой потребительского контракта
echo "Деплой потребительского контракта..."
cd "$BASE_DEPLOY_PATH" || { echo "Не удалось перейти в базовую директорию."; exit 1; }
project=hello-world make deploy-contracts

# 12. Получение адреса нового контракта
# Извлечение адреса из файла результатов деплоя
DEPLOY_OUTPUT_DIR="$BASE_DEPLOY_PATH/projects/hello-world/contracts/broadcast/Deploy.s.sol"
if [ -d "$DEPLOY_OUTPUT_DIR" ]; then
  LATEST_CHAIN_ID_DIR=$(find "$DEPLOY_OUTPUT_DIR" -maxdepth 1 -type d | sort -nr | head -n 1)
  DEPLOY_JSON_PATH="$LATEST_CHAIN_ID_DIR/run-latest.json"
  if [ -f "$DEPLOY_JSON_PATH" ]; then
    CONTRACT_ADDRESS=$(jq -r '.. | objects | select(has("contractAddress")) | .contractAddress' "$DEPLOY_JSON_PATH" | head -n 1)
    if [ -n "$CONTRACT_ADDRESS" ]; then
      echo "Адрес нового контракта: $CONTRACT_ADDRESS"
    else
      echo "Не удалось извлечь адрес контракта из $DEPLOY_JSON_PATH"
      exit 1
    fi
  else
    echo "Файл $DEPLOY_JSON_PATH не найден."
    exit 1
  fi
else
  echo "Директория $DEPLOY_OUTPUT_DIR не найдена."
  exit 1
fi

# Преобразование адреса в формат с контрольной суммой
CHECKSUMMED_ADDRESS=$(python3 -c "from web3 import Web3; print(Web3.toChecksumAddress('$CONTRACT_ADDRESS'))")

# 13. Обновление CallContract.s.sol с новым адресом контракта
CALL_CONTRACT_FILE="$BASE_DEPLOY_PATH/projects/hello-world/contracts/script/CallContract.s.sol"
if [ -f "$CALL_CONTRACT_FILE" ]; then
  echo "Обновление CallContract.s.sol с новым адресом контракта..."
  sed -i "s|SaysGM saysGm = SaysGM(.*);|SaysGM saysGm = SaysGM($CHECKSUMMED_ADDRESS);|" "$CALL_CONTRACT_FILE"
else
  echo "Файл CallContract.s.sol не найден."
fi

# 14. Вызов контракта
echo "Вызов контракта..."
project=hello-world make call-contract

echo "Установка завершена."
