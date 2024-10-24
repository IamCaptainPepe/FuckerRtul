from wallet_manager import WalletManager
from config_manager import ConfigManager
from container_manager import ContainerManager
from transaction_checker import TransactionChecker
import time

class Main:
    def __init__(self, wallet_manager, config_manager, container_manager, transaction_checker, method_id, min_transactions, min_balance, check_interval):
        self.wallet_manager = wallet_manager
        self.config_manager = config_manager
        self.container_manager = container_manager
        self.transaction_checker = transaction_checker
        self.method_id = method_id
        self.min_transactions = min_transactions
        self.min_balance = min_balance
        self.check_interval = check_interval

    def run(self):
        try:
            current_private_key = self.wallet_manager.get_current_private_key()
            if not current_private_key:
                current_private_key = self.wallet_manager.get_first_private_key()

            if not current_private_key:
                print("Ошибка: ни один приватный ключ не найден.")
                return

            wallet_address = self.wallet_manager.get_wallet_address(current_private_key)
            print(f"Используемый адрес кошелька: {wallet_address}")

            while True:
                transactions = self.transaction_checker.get_account_transactions(wallet_address)
                filtered_transactions = self.transaction_checker.filter_transactions_by_method(transactions, self.method_id)

                print(f"Количество транзакций с вызовом метода {self.method_id}: {len(filtered_transactions)}")

                balance = self.transaction_checker.get_account_balance(wallet_address)
                print(f"Баланс кошелька {wallet_address}: {balance} ETH")

                if len(filtered_transactions) >= self.min_transactions or balance < self.min_balance:
                    print("Заменяем приватный ключ...")
                    self.config_manager.update_private_key(current_private_key)
                    self.container_manager.restart_containers()
                    self.wallet_manager.add_to_used_private_keys(current_private_key)

                    current_private_key = self.wallet_manager.get_first_private_key()
                    if not current_private_key:
                        print("Ошибка: приватные ключи закончились. Завершаем работу.")
                        break

                    wallet_address = self.wallet_manager.get_wallet_address(current_private_key)
                    print(f"Используемый адрес кошелька: {wallet_address}")
                else:
                    print("Текущий ключ подходит, продолжаем.")

                time.sleep(self.check_interval)

        except Exception as e:
            print(f"Ошибка: {str(e)}")


if __name__ == "__main__":
    # Инициализация настроек
    with open('settings.txt', 'r') as file:
        settings = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in file.readlines()}
    
    wallet_manager = WalletManager(
        config_paths=settings['config_paths'].split(','),
        private_key_file=settings['private_key_file'],
        used_private_keys_file=settings['used_private_keys_file'],
        web3_provider=settings['web3_provider']
    )
    config_manager = ConfigManager(config_paths=settings['config_paths'].split(','))
    container_manager = ContainerManager(containers=settings['containers'].split(','))
    transaction_checker = TransactionChecker(api_key=settings['api_key'], base_url=settings['base_url'])
    
    main = Main(
        wallet_manager=wallet_manager,
        config_manager=config_manager,
        container_manager=container_manager,
        transaction_checker=transaction_checker,
        method_id=settings['method_id'],
        min_transactions=int(settings['min_transactions']),
        min_balance=float(settings['min_balance']),
        check_interval=int(settings['check_interval'])
    )
    main.run()
