import requests
from wallet_manager import WalletManager  # Assuming wallet_manager.py is in the same directory
import json
import os

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

    # Initialize wallet manager
    config_paths = settings.get('config_paths').split(',')

    wallet_manager = WalletManager(
        config_paths=config_paths,
        private_key_file=settings.get('private_key_file'),
        used_private_keys_file=settings.get('used_private_keys_file'),
        web3_provider=web3_provider
    )

    # Initialize the transaction checker
    tx_checker = TransactionChecker(api_key=api_key, base_url=base_url, wallet_manager=wallet_manager)

    # Get private key and wallet address
    private_key, wallet_address = tx_checker.get_private_key_and_wallet()
    if wallet_address:
        # Retrieve successful transactions with specific method ID
        successful_transactions = tx_checker.get_successful_transactions(wallet_address, method_id)
        
        if successful_transactions:
            print(f"Successful transactions with method ID {method_id}: {len(successful_transactions)}")
        else:
            print("Не удалось найти успешные транзакции с указанным методом.")

if __name__ == "__main__":
    main()
