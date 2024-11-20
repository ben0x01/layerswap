import random
import asyncio
import os
import httpx

from dataclasses import dataclass, asdict
from functools import wraps
from typing import Any, List, Tuple
from web3.exceptions import TransactionNotFound

from src.network_config import NETWORKS
from src.logger import Logger

log = Logger(name="HelperFunctions", log_file="helper_functions.log").get_logger()


@dataclass
class Payload:
    amount: float
    source_network: str
    destination_network: str = "FUEL_MAINNET"
    source_token: str = "ETH"
    destination_token: str = "ETH"
    destination_address: str = ""
    refuel: bool = False
    use_deposit_address: bool = False
    source_address: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


async def make_post_request(url: str, headers: dict, payload: dict) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                log.error(f"HTTP error {response.status_code}: {response.text}")
                return None
    except httpx.RequestError as e:
        log.error(f"Request error: {e}")
        return None


async def is_transaction_successful(w3, tx_hash: hex, wallet_address: str, amount) -> bool:
    await asyncio.sleep(30)
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        return receipt['status'] == 1
    except TransactionNotFound:
        log.warning(f"Wallet: {wallet_address} | Amount: {amount} | Transaction with hash {tx_hash} not found.")
        return False
    except Exception as e:
        log.error(f"Wallet: {wallet_address} | Amount: {amount} | Error checking transaction: {str(e)}")
        return False


def retry_async(attempts=3, delay=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    log.error(f"Attempt {attempt} failed with error: {str(e)}")
                    if attempt < attempts:
                        log.info(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        log.error("All retry attempts failed.")
                        raise e

        return wrapper

    return decorator


@retry_async(attempts=3, delay=random.randint(1, 5))
async def get_call_data(amount: float, network_from: str, fuel_address: str, source_address: str) -> dict | None:
    url = "https://api.layerswap.io/api/v2/swaps"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'access-control-allow-origin': '*',
        'content-type': 'application/json',
        'origin': 'https://layerswap.io',
        'referer': 'https://layerswap.io/',
        'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
        'x-ls-apikey': 'NDBxG+aon6WlbgIA2LfwmcbLU52qUL9qTnztTuTRPNSohf/VnxXpRaJlA5uLSQVqP8YGIiy/0mz+mMeZhLY4/Q',
    }
    payload = Payload(
        amount=amount,
        source_network=network_from,
        destination_address=fuel_address,
        source_address=source_address
    ).to_dict()

    print("Payload:", payload)

    response_data = await make_post_request(url, headers, payload)
    if response_data and "data" in response_data and "deposit_actions" in response_data["data"]:
        return response_data
    log.error(f"Unexpected response structure or failed request: {response_data}")
    return None


async def check_rpc_status(rpc_url: str) -> bool:
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "method": "web3_clientVersion",
        "params": [],
        "id": 1
    }

    response_data = await make_post_request(rpc_url, headers, payload)
    if response_data and "result" in response_data:
        log.info(f"RPC {rpc_url} is working")
        return True
    log.warning(f"RPC {rpc_url} might be down or not responding correctly: {response_data}")
    return False


async def get_working_rpc_for_network(network_name: str) -> Any | None:
    rpc_list = NETWORKS.get(network_name)
    if not rpc_list:
        log.warning(f"Network {network_name} not found.")
        return None

    for rpc_url in rpc_list:
        if await check_rpc_status(rpc_url):
            return rpc_url
    log.error(f"No working RPC found for {network_name}.")
    return None


def load_wallet_data(private_keys_file: str, addresses_file: str, use_random: bool) -> List[Tuple[str, str]]:
    private_keys_file = os.path.abspath(private_keys_file)
    addresses_file = os.path.abspath(addresses_file)

    if not os.path.isfile(private_keys_file):
        raise FileNotFoundError(f"The file with the private keys was not found: {private_keys_file}")
    if not os.path.isfile(addresses_file):
        raise FileNotFoundError(f"The file with the addresses was not found: {addresses_file}")

    with open(private_keys_file, 'r') as pk_file:
        private_keys = [line.strip() for line in pk_file if line.strip()]
    with open(addresses_file, 'r') as addr_file:
        addresses = [line.strip() for line in addr_file if line.strip()]

    if not private_keys:
        raise ValueError("The private keys file is empty or invalid")
    if not addresses:
        raise ValueError("The addresses file is empty or invalid")

    if len(private_keys) != len(addresses):
        raise ValueError("The number of private keys does not match the number of addresses")
    wallets = list(zip(private_keys, addresses))

    if use_random:
        log.info("Shuffling wallets...")
        random.shuffle(wallets)
        log.debug(f"Shuffled wallets: {wallets}")
    else:
        log.info("Wallet shuffling is disabled.")

    log.info(f"Wallets loaded successfully | Count: {len(wallets)}")
    return wallets
