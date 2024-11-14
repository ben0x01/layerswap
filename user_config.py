#Ввод процентов для свапа.
AMOUNT_FOR_SWAP = [0.01, 0.02]         # Диапазон суммы в ETH
PERCENT_FOR_SWAP = [50, 65]           # Диапазон процента от баланса на кошельке
min_amount_for_swap = False
max_amount_for_swap = False
percent_for_swap = True

#включить рандомизацию кошельков
SHUFFLE_WALLETS = True

#время задержки между свапами
SLEEP_TIME_SWAP = [1, 5]

#время задержки между повтором
SLEEP_TIME_RETRY = [1, 5]

#arb, op, base, scroll
NETWORK_FROM = "arb"