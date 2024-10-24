import requests

class TransactionChecker:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def get_account_transactions(self, address):
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": self.api_key
        }
        response = requests.get(self.base_url, params=params)
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

    def filter_transactions_by_method(self, transactions, method_id):
        return [tx for tx in transactions if tx['input'].startswith(method_id)]

    def get_account_balance(self, address):
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "apikey": self.api_key
        }
        response = requests.get(self.base_url, params=params)
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
