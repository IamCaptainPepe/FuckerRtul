import requests
from wallet_manager import WalletManager  # Assuming wallet_manager.py is in the same directory
from config_manager import ConfigManager
from container_manager import ContainerManager
import json
import os
import random
import time
import subprocess

class TransactionChecker:
    def __init__(self, api_key, base_url, wallet_manager):
        self.api_key = api_key
        self.base_url = base_url
        self.wallet_manager = wallet_manager

    def get_successful_transactions(self, wallet_address, method_id):
        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": self.api_key
        }
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1":
                transactions = data.get("result", [])
                successful_transactions = [tx for tx in transactions if tx.get("isError") == "0" and tx.get("input", "").startswith(method_id)]
                return successful_transactions
            else:
                return []
        else:
            return []

    def get_private_key_and_wallet(self):
        for path in self.wallet_manager.config_paths:
            try:
                with open(path, 'r') as file:
                    config = json.load(file)
                    if "chain" in config and "wallet" in config["chain"]:
                        private_key = config["chain"]["wallet"].get("private_key")
                        if private_key:
                            wallet_address = self.wallet_manager.get_wallet_address(private_key)
                            return private_key, wallet_address
            except Exception as e:
                continue
        return None, None

    def get_account_balance(self, wallet_address):
        params = {
            "module": "account",
            "action": "balance",
            "address": wallet_address,
            "apikey": self.api_key
        }
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1":
                wei_balance = int(data.get("result", 0))
                eth_balance = wei_balance / 10**18
                return eth_balance
        return 0.0

class ConfigManager:
    def __init__(self, config_paths):
        self.config_paths = config_paths

    def update_private_key(self, new_private_key):
        for path in self.config_paths:
            try:
                with open(path, 'r') as file:
                    config = json.load(file)
                if "chain" in config and "wallet" in config["chain"]:
                    config["chain"]["wallet"]["private_key"] = new_private_key
                    with open(path, 'w') as file:
                        json.dump(config, file, indent=4)
                    print(f"Приватный ключ обновлен в файле: {path}")
            except Exception as e:
                print(f"Ошибка при обновлении приватного ключа в файле {path}: {str(e)}")

def main():
    # Load your settings from the config
    settings = {}
    with open('settings.txt', 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            settings[key] = value

    api_key = settings.get('api_key')
    base_url = settings.get('base_url')
    method_id = settings.get('method_id')
    web3_provider = settings.get('web3_provider')
    min_transactions = int(settings.get('min_transactions', 50))
    min_balance = float(settings.get('min_balance', 0.00005))
    check_interval = int(settings.get('check_interval', 60))

    # Initialize wallet manager
    config_paths = settings.get('config_paths').split(',')

    wallet_manager = WalletManager(
        config_paths=config_paths,
        private_key_file=settings.get('private_key_file'),
        used_private_keys_file=settings.get('used_private_keys_file'),
        web3_provider=web3_provider
    )
    config_manager = ConfigManager(config_paths=config_paths)
    container_manager = ContainerManager(containers=settings['containers'].split(','))

    # Initialize the transaction checker
    tx_checker = TransactionChecker(api_key=api_key, base_url=base_url, wallet_manager=wallet_manager)

    # Get private key and wallet address
    private_key, wallet_address = tx_checker.get_private_key_and_wallet()
    if wallet_address:
        try:
            while True:
                # Retrieve successful transactions with specific method ID
                successful_transactions = tx_checker.get_successful_transactions(wallet_address, method_id)
                random_threshold = min_transactions + random.randint(0, 10)

                print(f"Количество успешных транзакций с вызовом метода {method_id}: {len(successful_transactions)}")

                # Get wallet balance
                balance = tx_checker.get_account_balance(wallet_address)
                print(f"Баланс кошелька {wallet_address}: {balance} ETH")

                # Check if the number of transactions or balance conditions are met
                if len(successful_transactions) >= random_threshold or balance < min_balance:
                    print(f"Количество успешных транзакций достигло порога: {random_threshold} или баланс ниже {min_balance} ETH. Заменяем приватный ключ...")
                    # Logic to replace the private key
                    current_private_key = private_key
                    wallet_manager.add_to_used_private_keys(current_private_key)
                    new_private_key = wallet_manager.get_first_private_key()
                    if not new_private_key:
                        print("Ошибка: приватные ключи закончились. Завершаем работу.")
                        break
                    else:
                        private_key = new_private_key
                        wallet_address = wallet_manager.get_wallet_address(private_key)
                        print(f"Новый использующийся адрес кошелька: {wallet_address}")

                    # Update private key in config files
                    config_manager.update_private_key(new_private_key)

                    # Restart containers after replacing private key
                    print("Перезапуск контейнеров...")
                    container_manager.restart_containers()
                    time.sleep(10)

                    # Run token_deployer.py after restarting containers
                    print("Запуск token_deployer.py...")
                    subprocess.run(["python", "token_deployer.py"])
                    time.sleep(10)

                    # Restart containers again
                    print("Перезапуск контейнеров снова...")
                    container_manager.restart_containers()
                else:
                    print("Текущий ключ подходит, продолжаем.")

                time.sleep(check_interval)
        except Exception as e:
            print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    main()
