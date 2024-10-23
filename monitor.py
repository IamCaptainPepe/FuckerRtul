import json
import os
import time
import requests
import subprocess
from web3 import Web3

# Настройки
API_KEY = "IIB5A6I991FBYFB9YE6CE6QRJWYQZ5GHU6"
METHOD_ID = "0xc509543d"
BASESCAN_API_URL = "https://api.basescan.org/api"
MIN_TRANSACTIONS = 50  # Минимальное количество транзакций для замены ключа
MIN_BALANCE = 0.00005  # Минимальный баланс (в ETH) для замены ключа
CHECK_BALANCE = True  # Переключатель: проверять баланс или нет
CHECK_INTERVAL = 60  # Интервал проверки в секундах

# Пути к файлам
config_paths = [
    os.path.expanduser("~/infernet-container-starter/deploy/config.json"),
    os.path.expanduser("~/infernet-container-starter/projects/hello-world/container/config.json")
]
private_key_path = "private_key.txt"  # Путь к файлу с приватными ключами
used_private_keys_path = "used_private_keys.txt"  # Путь к файлу с использованными приватными ключами

# Список контейнеров для перезагрузки
containers = [
    "hello-world",
    "infernet-node",
    "deploy-redis-1",
    "infernet-anvil",
    "deploy-fluentbit-1"
]

# Инициализация Web3
w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth"))  # Укажите правильный RPC для сети


# Функция для получения кошелька из приватного ключа
def get_wallet_address_from_private_key(private_key):
    account = w3.eth.account.from_key(private_key)
    return account.address


# Функция для получения всех транзакций аккаунта
def get_account_transactions(address, api_key):
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",  # Сортировка транзакций по возрастанию
        "apikey": api_key
    }

    response = requests.get(BASESCAN_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1":
            return data.get("result", [])
        else:
            print(f"Ошибка API: {data.get('message', 'Неизвестная ошибка')}")
            return []
    else:
        print(f"Ошибка HTTP: {response.status_code}")
        return []


# Функция для фильтрации транзакций по методу
def filter_transactions_by_method(transactions, method_id):
    return [tx for tx in transactions if tx['input'].startswith(method_id)]


# Функция для получения баланса в ETH
def get_account_balance(address, api_key):
    params = {
        "module": "account",
        "action": "balance",
        "address": address,
        "apikey": api_key
    }

    response = requests.get(BASESCAN_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1":
            wei_balance = int(data["result"])
            eth_balance = wei_balance / 10**18
            return eth_balance
        else:
            print(f"Ошибка API: {data.get('message', 'Неизвестная ошибка')}")
            return None
    else:
        print(f"Ошибка HTTP: {response.status_code}")
        return None


# Функция для замены приватного ключа в конфиге
def update_private_key(config_path, new_private_key):
    with open(config_path, 'r') as file:
        config = json.load(file)

    if "chain" in config and "wallet" in config["chain"]:
        config["chain"]["wallet"]["private_key"] = new_private_key
        print(f"Приватный ключ обновлен в файле: {config_path}")

    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)


# Функция для получения первого приватного ключа из txt файла
def get_first_private_key(private_key_file):
    with open(private_key_file, 'r') as file:
        keys = file.readlines()

    if keys:
        first_key = keys[0].strip()
        with open(private_key_file, 'w') as file:
            file.writelines(keys[1:])
        return first_key
    else:
        raise ValueError("Файл с приватными ключами пуст.")


# Функция для добавления использованного приватного ключа в файл
def add_to_used_private_keys(new_private_key, used_private_keys_file):
    with open(used_private_keys_file, 'a') as used_file:
        used_file.write(new_private_key + "\n")
    print(f"Приватный ключ добавлен в {used_private_keys_file}")


# Функция для перезагрузки Docker контейнеров
def restart_containers(container_names):
    for container in container_names:
        try:
            print(f"Перезагружаем контейнер: {container}")
            subprocess.run(["docker", "restart", container], check=True)
            print(f"Контейнер {container} успешно перезагружен.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при перезагрузке контейнера {container}: {e}")


# Основной цикл
def main():
    while True:
        try:
            # Получаем первый приватный ключ из txt файла
            new_private_key = get_first_private_key(private_key_path)
            wallet_address = get_wallet_address_from_private_key(new_private_key)
            print(f"Используемый адрес кошелька: {wallet_address}")

            # Получаем список транзакций
            transactions = get_account_transactions(wallet_address, API_KEY)
            filtered_transactions = filter_transactions_by_method(transactions, METHOD_ID)

            print(f"Количество транзакций с вызовом метода {METHOD_ID}: {len(filtered_transactions)}")

            # Проверка баланса, если включено
            if CHECK_BALANCE:
                balance = get_account_balance(wallet_address, API_KEY)
                if balance is not None:
                    print(f"Баланс кошелька {wallet_address}: {balance} ETH")
                else:
                    print("Не удалось получить баланс.")
            else:
                balance = float('inf')  # Если баланс не проверяется, ставим бесконечность

            # Проверка на замену ключа
            if len(filtered_transactions) >= MIN_TRANSACTIONS or balance < MIN_BALANCE:
                print("Заменяем приватный ключ...")

                # Обновляем приватный ключ в файлах конфигурации
                for path in config_paths:
                    update_private_key(path, new_private_key)

                # Перезагружаем контейнеры
                restart_containers(containers)

                # Добавляем использованный ключ в файл использованных ключей
                add_to_used_private_keys(new_private_key, used_private_keys_path)
            else:
                print("Текущий ключ подходит, продолжаем.")

            # Проверка на окончание приватных ключей
            with open(private_key_path, 'r') as file:
                remaining_keys = file.readlines()
            if not remaining_keys:
                print("Приватные ключи закончились. Завершаем работу.")
                break

            # Ожидание перед следующей проверкой
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"Ошибка: {str(e)}")
            break


if __name__ == "__main__":
    main()
