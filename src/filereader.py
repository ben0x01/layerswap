import random

from typing import List

from src.decryption import is_base64, decrypt_private_key


def load_lines(filename: str) -> list:
    with open(filename) as f:
        return [row.strip() for row in f if row and not row.startswith('#')]

def load_and_decrypt_wallets(file_path: str, password: str, shuffle: bool = False) -> List[str]:
    with open(file_path, 'r') as file:
        wallets = [line.strip() for line in file if line.strip()]
    if shuffle:
        random.shuffle(wallets)
    return wallets


class FileReader:
    def __init__(self, file_name):
        self.wallets = []
        self.file_name = file_name

    def load(self) -> list:
        with open(self.file_name, 'r') as f:
            self.wallets = [line.strip() for line in f if line.strip()]
        return self.wallets

    def decrypt(self, password):
        for i, wallet in enumerate(self.wallets):
            if is_base64(wallet):
                self.wallets[i] = decrypt_private_key(wallet, password)

    def is_encrypted(self):
        return any(is_base64(wallet) for wallet in self.wallets)

    def check(self) -> bool:
        return bool(self.wallets)
