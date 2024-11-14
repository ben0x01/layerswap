## Установка
1) Клонируйте репозиторий:
   git clone https://github.com/ben0x01/layerswap.git
   cd layerswap

2) Настройка виртуального окружения:
  python -m venv venv
  source venv/bin/activate  #для мака/linux
  venv\Scripts\activate #для windows

3) Установка зависимостей:
  pip install -r requirements.txt


## Настройка rpc
1) В src/network_config.py можно добавить любое количество rpc для нужной сети, софт будет заменять нерабочую на следующую


## Настройка конфига

NETWORK_FROM = "arb"  # Короткое обозначение сети, можно использовать сети: arb, op, scroll, base

SLEEP_TIME_SWAP = [5, 15]  # Диапазон времени задержки между свапами

SLEEP_TIME_RETRY = [5, 15] # Диапазон времени задержек между повторениями


### В случае если нам нужен модуль, то ставим True, а в остальных местах оставляем False

AMOUNT_FOR_SWAP = [0.01, 0.02]  # Диапазон фиксированных сумм для обмена в ETH

PERCENT_OF_SWAP = [90, 100]  # Процент от баланса для обмена (например, от 90% до 100%)

SHUFFLE_WALLETS = True  # Рандомный выбор кошельков

MIN_AMOUNT_FOR_SWAP = False #свап минимальной суммы введенной в AMOUNT_FOR_SWAP

MAX_AMOUNT_FOR_SWAP = False #свап максимальной суммы введенной в AMOUNT_FOR_SWAP

PERCENT_FOR_SWAP = True # если выбираем процент, то оставляем True
