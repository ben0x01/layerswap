import base64
import binascii
from Crypto.Util.Padding import pad
from src.decryption import get_cipher


def encrypt_private_key(private_key: str, password: str) -> str:
    private_key = private_key.strip() 
    if private_key.startswith("0x"):
        private_key = private_key[2:]

    if len(private_key) % 2 != 0:
        raise ValueError(f"Invalid private key: {private_key}. Key length must be even.")

    private_key_bytes = binascii.unhexlify(private_key)

    cipher = get_cipher(password)

    encrypted_bytes = cipher.encrypt(pad(private_key_bytes, 16))
    encrypted_base64 = base64.b64encode(encrypted_bytes).decode('utf-8')

    return encrypted_base64
