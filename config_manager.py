import json

class ConfigManager:
    def __init__(self, config_paths, makefile_path):
        self.config_paths = config_paths
        self.makefile_path = makefile_path

    def update_private_key(self, new_private_key):
        # Обновление приватного ключа в JSON конфигурационных файлах
        for path in self.config_paths:
            with open(path, 'r') as file:
                config = json.load(file)
            if "chain" in config and "wallet" in config["chain"]:
                config["chain"]["wallet"]["private_key"] = new_private_key
                print(f"Приватный ключ обновлен в файле: {path}")
            with open(path, 'w') as file:
                json.dump(config, file, indent=4)

        # Обновление приватного ключа в Makefile
        with open(self.makefile_path, 'r') as file:
            lines = file.readlines()
        with open(self.makefile_path, 'w') as file:
            for line in lines:
                if line.startswith('sender :='):
                    file.write(f'sender := {new_private_key}\n')
                else:
                    file.write(line)
        print(f"Приватный ключ обновлен в файле: {self.makefile_path}")
