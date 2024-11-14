import os
import asyncio
import random
from typing import Any

from src.filereader import load_and_decrypt_wallets
from src.network_config import NETWORKS, SHORTCUTS
from src.swap import Layerswap
from src.helper import get_working_rpc_for_network
from src.logger import Logger
from user_config import (
    SHUFFLE_WALLETS, SLEEP_TIME_SWAP, NETWORK_FROM,
    AMOUNT_FOR_SWAP, PERCENT_FOR_SWAP,
    min_amount_for_swap, max_amount_for_swap, percent_for_swap
)

log = Logger(name="Main", log_file="main.log").get_logger()

async def calculate_amount(w3, wallet_address: str) -> float:
    balance = w3.eth.get_balance(wallet_address) / 10 ** 18
    if percent_for_swap:
        min_percent, max_percent = PERCENT_FOR_SWAP
        chosen_percent = random.uniform(min_percent, max_percent) / 100
        amount = balance * chosen_percent
    elif min_amount_for_swap:
        amount = AMOUNT_FOR_SWAP[0]
    elif max_amount_for_swap:
        amount = AMOUNT_FOR_SWAP[1]
    else:
        log.error("No swap amount configuration is set to True.")
        raise ValueError("Invalid swap configuration")
    if amount > balance:
        log.error(f"Swap amount {amount} ETH exceeds wallet balance {balance} ETH.")
        raise ValueError(f"Insufficient balance on wallet. Required: {amount} ETH, Available: {balance} ETH")
    return amount

async def main() -> Any | None:
    decrypt_choice = input("Do you want to decrypt wallets? (yes/no): ").strip().lower()
    use_encryption = decrypt_choice == "yes"
    password = input("Enter password for wallet decryption: ").strip() if use_encryption else ""

    private_key_file = os.path.abspath('./data/wallets.txt')
    addresses_file = os.path.abspath('./data/Fuel-Wallets.txt')

    wallets = load_and_decrypt_wallets(private_key_file, password=password, shuffle=SHUFFLE_WALLETS)
    with open(addresses_file, 'r') as addr_file:
        addresses = [line.strip() for line in addr_file if line.strip()]

    if len(wallets) != len(addresses):
        log.error("The number of private keys does not match the number of addresses.")
        return

    network_from = SHORTCUTS.get(NETWORK_FROM.lower(), NETWORK_FROM.upper())
    if network_from not in NETWORKS:
        log.warning("Invalid network name in configuration. Please enter a valid network (e.g., arb, op, base, scroll).")
        return

    rpc = await get_working_rpc_for_network(network_from)
    if not rpc:
        log.error(f"No working RPC endpoints found for {network_from}.")
        return

    for private_key, fuel_address in zip(wallets, addresses):
        log.info(f"Using Private Key: {private_key}")
        log.info(f"Using Address: {fuel_address}")

        layerswap_instance = Layerswap(rpc, private_key, fuel_address, 0, network_from)
        amount = await calculate_amount(layerswap_instance.w3, layerswap_instance.wallet.address)
        layerswap_instance.amount = amount
        await layerswap_instance.swap_to_fuel()

        delay_between_swaps = random.randint(SLEEP_TIME_SWAP[0], SLEEP_TIME_SWAP[1])
        log.info(f"Waiting {delay_between_swaps} seconds before the next swap...")
        await asyncio.sleep(delay_between_swaps)

    log.info("All wallets have been used.")

if __name__ == "__main__":
    asyncio.run(main())
