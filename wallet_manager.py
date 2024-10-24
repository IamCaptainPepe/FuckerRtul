import json
from web3 import Web3

class WalletManager:
    def __init__(self, config_paths, private_key_file, used_private_keys_file, web3_provider):
        self.config_paths = config_paths
        self.private_key_file = private_key_file
        self.used_private_keys_file = used_private_keys_file
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))

    def get_current_private_key(self):
        for path in self.config_paths:
            with open(path, 'r') as file:
                config = json.load(file)
                if "chain" in config and "wallet" in config["chain"]:
                    return config["chain"]["wallet"].get("private_key")
        return None

    def get_first_private_key(self):
        with open(self.private_key_file, 'r') as file:
            keys = file.readlines()
        if keys:
            first_key = keys[0].strip()
            with open(self.private_key_file, 'w') as file:
                file.writelines(keys[1:])
            return first_key
        return None

    def add_to_used_private_keys(self, private_key):
        with open(self.used_private_keys_file, 'a') as file:
            file.write(private_key + "\n")

    def get_wallet_address(self, private_key):
        account = self.w3.eth.account.from_key(private_key)
        return account.address
