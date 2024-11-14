# Конфигурация для свапа
AMOUNT_FOR_SWAP = [0.01, 0.02]        # Диапазон суммы в ETH
PERCENT_OF_SWAP = [50, 65]            # Диапазон процента от баланса на кошельке
MIN_AMOUNT_FOR_SWAP = False            # Использовать минимальную сумму из диапазона AMOUNT_FOR_SWAP
MAX_AMOUNT_FOR_SWAP = False            # Использовать максимальную сумму из диапазона AMOUNT_FOR_SWAP
USE_PERCENT_FOR_SWAP = False            # Использовать процент от баланса вместо фиксированного диапазона
USE_AMOUNT_RANGE_FOR_SWAP = True      # Использовать диапазон суммы в ETH или процент от баланса

# Включить рандомизацию кошельков
SHUFFLE_WALLETS = True

# Время задержки между свапами
SLEEP_TIME_SWAP = [1, 5]

# Время задержки между попытками повторного подключения
SLEEP_TIME_RETRY = [1, 5]

# Сеть для свапа (используйте arb, op, base, scroll)
NETWORK_FROM = "arb"
