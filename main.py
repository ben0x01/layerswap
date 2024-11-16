import os
import asyncio
import random
from typing import Any

from src.filereader import load_and_decrypt_wallets
from src.network_config import SHORTCUTS
from src.swap import Layerswap
from src.helper import get_working_rpc_for_network
from src.logger import Logger
from user_config import (
    SHUFFLE_WALLETS, SLEEP_TIME_SWAP, NETWORK_FROM,
    AMOUNT_FOR_SWAP, USE_PERCENT_FOR_SWAP,
    MIN_AMOUNT_FOR_SWAP, MAX_AMOUNT_FOR_SWAP, PERCENT_OF_SWAP, USE_AMOUNT_RANGE_FOR_SWAP
)

log = Logger(name="Main", log_file="main.log").get_logger()


async def calculate_amount(w3, wallet_address: str) -> float:
    log.info(f"Получение баланса для кошелька: {wallet_address}")
    balance_wei = w3.eth.get_balance(wallet_address)
    balance = balance_wei / 10 ** 18
    log.info(f"Баланс кошелька (ETH): {balance:.18f} ETH")

    if USE_AMOUNT_RANGE_FOR_SWAP:
        min_amount, max_amount = AMOUNT_FOR_SWAP
        amount = random.uniform(min_amount, max_amount)
        log.info(f"Выбран диапазон суммы: {min_amount} - {max_amount} ETH, рассчитанная сумма: {amount:.6f} ETH")

    elif USE_PERCENT_FOR_SWAP:
        min_percent, max_percent = PERCENT_OF_SWAP
        chosen_percent = random.uniform(min_percent, max_percent) / 100
        amount = balance * chosen_percent
        log.info(f"Процент выбран: {chosen_percent * 100:.2f}% от баланса {balance:.6f} ETH, рассчитанная сумма: {amount:.6f} ETH")

    elif MIN_AMOUNT_FOR_SWAP:
        amount = AMOUNT_FOR_SWAP[0]
        log.info(f"Используется минимальная сумма для свапа: {amount:.6f} ETH")

    elif MAX_AMOUNT_FOR_SWAP:
        amount = AMOUNT_FOR_SWAP[1]
        log.info(f"Используется максимальная сумма для свапа: {amount:.6f} ETH")

    else:
        log.error("No swap amount configuration is set to True.")
        raise ValueError("Invalid swap configuration: No valid amount range or percentage defined")

    if amount > balance:
        log.error(f"Сумма свапа {amount:.6f} ETH превышает баланс {balance:.6f} ETH.")
        raise ValueError(f"Недостаточный баланс на кошельке. Требуется: {amount:.6f} ETH, Доступно: {balance:.6f} ETH")

    log.info(f"Рассчитанная сумма для свапа: {amount:.6f} ETH")
    return amount

async def main() -> Any | None:
    decrypt_choice = input("Do you want to decrypt wallets? (yes/no): ").strip().lower()
    use_encryption = decrypt_choice == "yes"
    password = input("Enter password for wallet decryption: ").strip() if use_encryption else ""

    private_key_file = os.path.abspath('./data/wallets.txt')
    addresses_file = os.path.abspath('./data/Fuel-Wallets.txt')

    wallets = load_and_decrypt_wallets(private_key_file, password=password)
    with open(addresses_file, 'r') as addr_file:
        addresses = [line.strip() for line in addr_file if line.strip()]

    if len(wallets) != len(addresses):
        log.error("Количество приватных ключей не совпадает с количеством адресов.")
        return

    wallet_pairs = list(zip(wallets, addresses))
    if SHUFFLE_WALLETS:
        random.shuffle(wallet_pairs)

    network_data = SHORTCUTS.get(NETWORK_FROM.lower())
    if not network_data:
        log.warning("Неправильное имя сети в конфигурации. Проверьте значение NETWORK_FROM.")
        return

    network_name = network_data["name"]
    explorer_url = network_data["explorer"]

    rpc = await get_working_rpc_for_network(network_name)
    if not rpc:
        log.error(f"Нет рабочих RPC-эндпоинтов для {network_name}.")
        return

    for private_key, fuel_address in wallet_pairs:
        log.info(f"Использование приватного ключа: {private_key}")
        log.info(f"Использование адреса: {fuel_address}")

        layerswap_instance = Layerswap(rpc, private_key, fuel_address, 0, network_name, explorer_url)

        try:
            amount = await calculate_amount(layerswap_instance.w3, layerswap_instance.wallet.address)
            layerswap_instance.amount = amount
            await layerswap_instance.swap_to_fuel()
        except Exception as e:
            log.error(f"Ошибка при выполнении свапа: {str(e)}")

        delay_between_swaps = random.randint(SLEEP_TIME_SWAP[0], SLEEP_TIME_SWAP[1])
        log.info(f"Ожидание {delay_between_swaps} секунд перед следующим свапом...")
        await asyncio.sleep(delay_between_swaps)

    log.info("Все кошельки использованы.")

if __name__ == "__main__":
    asyncio.run(main())
