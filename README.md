# FuckerRtul
Скрипт предназначен для мониторинга Base-кошелька, используя приватные ключи из текстового файла. Он выполняет следующие функции:

Получение адреса кошелька: Скрипт извлекает адрес кошелька из приватного ключа, используя библиотеку Web3.

Мониторинг транзакций: Каждую минуту скрипт запрашивает список транзакций для указанного адреса на сервисе API (в данном случае, basescan). Он фильтрует транзакции по определённому методу, используя заданный идентификатор метода.

Проверка баланса: При включённом переключателе скрипт проверяет баланс кошелька. Если баланс меньше заданного порога или если количество транзакций превышает заданный лимит, скрипт заменяет текущий приватный ключ.

Замена приватного ключа: После замены приватного ключа в конфигурационных файлах, скрипт добавляет использованный ключ в отдельный файл и перезагружает указанные Docker-контейнеры для применения изменений.

Циклический мониторинг: Скрипт работает в бесконечном цикле и выполняет указанные проверки каждую минуту. Он завершает свою работу только в случае, если все приватные ключи были использованы.

Запуск

`git clone https://github.com/IamCaptainPepe/FuckerRtul.git && cd ~/FuckerRtul`

Добавляем приватки, меняем настрйоки если надо и запускаем либо в скрине, либо через команду

Запускать в скрине

`screen -S FuckerRtul`

`chmod +x run.sh && ./run.sh`

Логи 

`screen -r FuckerRtul`

Добавил 

restart_version.sh

Ставит версию 1.2.0, перезагружает докер и возращает 1.3.1 бытует мнение что это поможет отправлять транзы. 

Запуск 

`chmod +x restart_version.sh && ./restart_version.sh`
