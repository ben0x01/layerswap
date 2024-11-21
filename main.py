import os
import asyncio
import random
import platform
from typing import Any

from src.filereader import FileReader
from src.network_config import SHORTCUTS
from src.swap import Layerswap
from src.helper import get_working_rpc_for_network
from src.logger import Logger
from src.decryption import decrypt_private_key, is_base64
from user_config import (
    SHUFFLE_WALLETS, SLEEP_TIME_SWAP, NETWORK_FROM,
    AMOUNT_FOR_SWAP, USE_PERCENT_FOR_SWAP,
    MIN_AMOUNT_FOR_SWAP, MAX_AMOUNT_FOR_SWAP, PERCENT_OF_SWAP, USE_AMOUNT_RANGE_FOR_SWAP
)

log = Logger(name="Main", log_file="main.log").get_logger()


def input_password() -> str:
    """Handles cross-platform password input with hidden characters."""
    system = platform.system().lower()
    if system in ["linux", "darwin"]:
        try:
            os.system("stty -echo")
            password = input("Enter encryption/decryption password (or press Enter to skip): ").strip()
            print()
        finally:
            os.system("stty echo")
        return password
    elif system == "windows":
        import msvcrt
        print("Enter encryption/decryption password (or press Enter to skip): ", end="", flush=True)
        password = ""
        while True:
            char = msvcrt.getch()
            if char == b'\r':  
                break
            elif char == b'\b': 
                if len(password) > 0:
                    password = password[:-1]
                    print("\b \b", end="", flush=True)
            else:
                password += char.decode("utf-8")
                print("*", end="", flush=True)
        print()
        return password
    else:
        raise OSError(f"Unsupported operating system: {system}")


async def calculate_amount(w3, wallet_address: str) -> float:
    log.info(f"Getting a balance for wallet: {wallet_address}")
    balance_wei = w3.eth.get_balance(wallet_address)
    balance = balance_wei / 10 ** 18
    log.info(f"Wallet Balance (ETH): {balance:.18f} ETH")

    if USE_AMOUNT_RANGE_FOR_SWAP:
        min_amount, max_amount = AMOUNT_FOR_SWAP
        amount = random.uniform(min_amount, max_amount)
        log.info(f"Selected amount range: {min_amount} - {max_amount} ETH, calculated amount: {amount:.6f} ETH")
    elif USE_PERCENT_FOR_SWAP:
        min_percent, max_percent = PERCENT_OF_SWAP
        chosen_percent = random.uniform(min_percent, max_percent) / 100
        amount = balance * chosen_percent
        log.info(f"Selected percentage: {chosen_percent * 100:.2f}% from balance {balance:.6f} ETH, calculated amount: {amount:.6f} ETH")
    elif MIN_AMOUNT_FOR_SWAP:
        amount = AMOUNT_FOR_SWAP[0]
        log.info(f"Using minimum swap amount: {amount:.6f} ETH")
    elif MAX_AMOUNT_FOR_SWAP:
        amount = AMOUNT_FOR_SWAP[1]
        log.info(f"Using maximum swap amount: {amount:.6f} ETH")
    else:
        log.error("No valid swap configuration set.")
        raise ValueError("Invalid swap configuration: No valid amount range or percentage defined")

    if amount > balance:
        log.error(f"Swap amount {amount:.6f} ETH exceeds the balance {balance:.6f} ETH.")
        raise ValueError(f"Insufficient balance on the wallet. Required: {amount:.6f} ETH, Available: {balance:.6f} ETH")

    log.info(f"The calculated amount for the swap: {amount:.6f} ETH")
    return amount


async def main() -> Any | None:
    password = input_password()  
    use_encryption = bool(password)

    private_key_file = os.path.abspath('./data/wallets.txt')
    addresses_file = os.path.abspath('./data/Fuel-Wallets.txt')

    if not os.path.exists(private_key_file):
        log.error(f"Private key file not found: {private_key_file}")
        return

    if not os.path.exists(addresses_file):
        log.error(f"Addresses file not found: {addresses_file}")
        return

    file_reader = FileReader(private_key_file)

    try:
        wallets = file_reader.load()
        if not wallets:
            log.error("No wallets loaded from the file.")
            return
        log.info(f"Loaded {len(wallets)} wallets.")

        if use_encryption:
            log.info("Decrypting wallets...")
            decrypted_wallets = []
            for private_key in wallets:
                if is_base64(private_key):
                    decrypted_wallets.append(decrypt_private_key(private_key, password))
                else:
                    decrypted_wallets.append(private_key)
            wallets = decrypted_wallets
            log.info("All wallets have been successfully decrypted.")
    except Exception as e:
        log.error(f"Error loading wallets: {e}")
        return

    with open(addresses_file, 'r') as addr_file:
        addresses = [line.strip() for line in addr_file if line.strip()]

    if not addresses:
        log.error("No addresses loaded from the file.")
        return

    if len(wallets) != len(addresses):
        log.error(f"Mismatch between wallets ({len(wallets)}) and addresses ({len(addresses)}).")
        return

    wallet_pairs = list(zip(wallets, addresses))
    if SHUFFLE_WALLETS:
        random.shuffle(wallet_pairs)

    network_data = SHORTCUTS.get(NETWORK_FROM.lower())
    if not network_data:
        log.warning("The network name in the configuration is incorrect. Check the value NETWORK_FROM.")
        return

    network_name = network_data["name"]
    explorer_url = network_data["explorer"]

    rpc = await get_working_rpc_for_network(network_name)
    if not rpc:
        log.error(f"There are no working RPC endpoints for {network_name}.")
        return

    for private_key, fuel_address in wallet_pairs:
        log.info(f"Using the address: {fuel_address}")

        layerswap_instance = Layerswap(rpc, private_key, fuel_address, 0, network_name, explorer_url)

        try:
            amount = await calculate_amount(layerswap_instance.w3, layerswap_instance.wallet.address)
            layerswap_instance.amount = amount
            await layerswap_instance.swap_to_fuel()
        except Exception as e:
            log.error(f"Error when performing swap: {str(e)}")

        delay_between_swaps = random.randint(SLEEP_TIME_SWAP[0], SLEEP_TIME_SWAP[1])
        log.info(f"Waiting {delay_between_swaps} seconds before the next swap...")
        await asyncio.sleep(delay_between_swaps)

    log.info("All wallets are used.")


if __name__ == "__main__":
    asyncio.run(main())
