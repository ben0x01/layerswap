import random
from web3 import Web3
from user_config import SLEEP_TIME_RETRY
from src.helper import is_transaction_successful, retry_async, get_call_data
from src.logger import Logger

log = Logger(name="Swap", log_file="swap.log").get_logger()

class Layerswap:
    def __init__(self, rpc, private_key, fuel_address, amount, network_from, explorer_url):
        self.amount = amount
        self.explorer_url = explorer_url
        self.private_key = private_key
        self.fuel_address = fuel_address
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self.wallet = self.w3.eth.account.from_key(private_key)
        self.network_from = network_from

    @retry_async(attempts=3, delay=random.randint(SLEEP_TIME_RETRY[0], SLEEP_TIME_RETRY[1]))
    async def swap_to_fuel(self):
        call_data = await get_call_data(self.amount, self.network_from, self.fuel_address, self.wallet.address)
        if not call_data:
            log.error("Failed to retrieve call data. Skipping transaction.")
            return

        try:
            nonce = self.w3.eth.get_transaction_count(self.wallet.address, "pending")
            base_fee = self.w3.eth.gas_price
            max_priority_fee_per_gas = self.w3.eth.max_priority_fee

            increase_factor = 1.2
            max_priority_fee_per_gas = int(max_priority_fee_per_gas * increase_factor)
            max_fee_per_gas = int((base_fee + max_priority_fee_per_gas) * increase_factor)

            tx = {
                "from": self.wallet.address,
                "to": Web3.to_checksum_address("0x2Fc617E933a52713247CE25730f6695920B3befe"),
                "data": call_data['data']['deposit_actions'][0]['call_data'],
                "value": Web3.to_wei(self.amount, "ether"),
                "maxPriorityFeePerGas": max_priority_fee_per_gas,
                "maxFeePerGas": max_fee_per_gas,
                "nonce": nonce,
                "chainId": self.w3.eth.chain_id,
            }

            tx["gas"] = self.w3.eth.estimate_gas(tx)

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)

            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if await is_transaction_successful(self.w3, tx_hash.hex(), self.wallet.address, self.amount):
                log.info(
                    f'Wallet: {self.wallet.address} | Amount: {self.amount} | Transaction hash: {self.explorer_url}0x{tx_hash.hex()}')
            else:
                raise Exception(f"Transaction with hash {tx_hash.hex()} failed.")
        except Exception as e:
            log.error(f"Error during transaction: {e}")
            raise
