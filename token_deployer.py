import json
import os
import time
import subprocess
from web3 import Web3

# Загрузка настроек из файла settings.txt
settings_file_path = "settings.txt"
settings = {}
with open(settings_file_path, 'r') as settings_file:
    for line in settings_file:
        key, value = line.strip().split('=', 1)
        settings[key] = value

# Пути из файла настроек
file_path = settings['deploy_json_path']
call_contract_file_path = settings['call_contract_path']
base_deploy_path = settings['base_deploy_path']
temp_address_file = "temp_contract_address.txt"

# Функция для чтения JSON файла и поиска contractAddress
def find_contract_address(data):
    if isinstance(data, dict):
        if 'contractAddress' in data:
            return data['contractAddress']
        for key, value in data.items():
            result = find_contract_address(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_contract_address(item)
            if result:
                return result
    return None

# Функция для получения contractAddress из файла
def get_contract_address():
    with open(file_path, 'r') as file:
        data = json.load(file)
    return find_contract_address(data)

# Функция для обновления contractAddress в CallContract.s.sol
def update_call_contract_file():
    with open(temp_address_file, 'r') as temp_file:
        new_address = temp_file.read().strip()
    
    # Преобразование адреса в checksummed-формат
    checksummed_address = Web3.to_checksum_address(new_address)
    
    with open(call_contract_file_path, 'r') as file:
        lines = file.readlines()
    
    with open(call_contract_file_path, 'w') as file:
        for line in lines:
            if "SaysGM saysGm = SaysGM(" in line:
                file.write(f"        SaysGM saysGm = SaysGM({checksummed_address});\n")
            else:
                file.write(line)

# Переход в базовую директорию перед деплоем
os.chdir(base_deploy_path)

# Выполнение команды project=hello-world make deploy-contracts из базовой директории
subprocess.run(["/bin/sh", "-c", "project=hello-world make deploy-contracts"])

# Ожидание 30 секунд
time.sleep(30)

# Получение нового contractAddress
new_address = get_contract_address()

# Сравнение адресов
if new_address:
    # Сохранение адреса в промежуточный файл для сохранения регистра
    with open(temp_address_file, 'w') as temp_file:
        temp_file.write(new_address)
    
    print(f"New Contract Address: {new_address}")
    update_call_contract_file()

    # Ожидание 10 секунд
    time.sleep(10)

    # Выполнение команды project=hello-world make call-contract из базовой директории
    subprocess.run(["/bin/sh", "-c", f"project=hello-world make call-contract"])
else:
    print("No new contract address found.")
