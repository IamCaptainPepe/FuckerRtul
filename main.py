import requests
from wallet_manager import WalletManager  # Предполагается, что wallet_manager.py находится в той же директории
from container_manager import ContainerManager
import json
import os
import random
import time
import subprocess

class TransactionChecker:
    # Ваш существующий код класса TransactionChecker без изменений
    # ...

class ConfigManager:
    def __init__(self, config_paths, makefile_path):
        self.config_paths = config_paths
        self.makefile_path = makefile_path

    def update_private_key(self, new_private_key):
        # Обновление приватного ключа в JSON конфигурационных файлах
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

        # Обновление приватного ключа в Makefile
        try:
            with open(self.makefile_path, 'r') as file:
                lines = file.readlines()
            with open(self.makefile_path, 'w') as file:
                for line in lines:
                    if line.startswith('sender :='):
                        file.write(f'sender := {new_private_key}\n')
                    else:
                        file.write(line)
            print(f"Приватный ключ обновлен в файле: {self.makefile_path}")
        except Exception as e:
            print(f"Ошибка при обновлении приватного ключа в файле {self.makefile_path}: {str(e)}")

def main():
    # Загрузка настроек из файла settings.txt
    settings = {}
    with open('settings.txt', 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                settings[key] = value

    api_key = settings.get('api_key')
    base_url = settings.get('base_url')
    method_id = settings.get('method_id')
    web3_provider = settings.get('web3_provider')
    min_transactions = int(settings.get('min_transactions', 50))
    min_balance = float(settings.get('min_balance', 0.00005))
    check_interval = int(settings.get('check_interval', 60))

    # Инициализация wallet_manager
    config_paths = settings.get('config_paths').split(',')
    makefile_path = settings.get('makefile_path')

    wallet_manager = WalletManager(
        config_paths=config_paths,
        private_key_file=settings.get('private_key_file'),
        used_private_keys_file=settings.get('used_private_keys_file'),
        web3_provider=web3_provider
    )

    config_manager = ConfigManager(config_paths=config_paths, makefile_path=makefile_path)
    container_manager = ContainerManager(containers=settings['containers'].split(','))

    # Инициализация TransactionChecker
    tx_checker = TransactionChecker(api_key=api_key, base_url=base_url, wallet_manager=wallet_manager)

    # Получение приватного ключа и адреса кошелька
    private_key, wallet_address = tx_checker.get_private_key_and_wallet()
    if wallet_address:
        try:
            while True:
                # Ваш существующий код проверки транзакций и логики замены приватного ключа
                # ...
                # Обновление приватного ключа в конфигурационных файлах и Makefile
                config_manager.update_private_key(new_private_key)
                # Остальной код цикла остается без изменений
                # ...

        except Exception as e:
            print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    main()
