import json

class ConfigManager:
    def __init__(self, config_paths):
        self.config_paths = config_paths

    def update_private_key(self, new_private_key):
        for path in self.config_paths:
            with open(path, 'r') as file:
                config = json.load(file)
            if "chain" in config and "wallet" in config["chain"]:
                config["chain"]["wallet"]["private_key"] = new_private_key
                print(f"Приватный ключ обновлен в файле: {path}")
            with open(path, 'w') as file:
                json.dump(config, file, indent=4)
