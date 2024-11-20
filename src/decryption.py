import base64
import binascii
import hashlib

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad
from web3 import Web3


def is_base64(s):
    if not len(s):
        return False
    try:
        if len(s) == 64:
            Web3().eth.account.from_key(s)
            return False
    except Exception:
        ...
    try:
        decoded = base64.b64decode(s)
        reencoded = base64.b64encode(decoded)
        return reencoded == s.encode()
    except Exception:
        return False


def get_cipher(password):
    salt = hashlib.sha256(password.encode('utf-8')).digest()
    key = PBKDF2(password.encode('utf-8'), salt, dkLen=32, count=1)
    return AES.new(key, AES.MODE_ECB)


def decrypt_private_key(encrypted_base64_pk, password):
    cipher = get_cipher(password)
    encrypted_pk = base64.b64decode(encrypted_base64_pk)
    decrypted_bytes = unpad(cipher.decrypt(encrypted_pk), 16)
    decrypted_hex = binascii.hexlify(decrypted_bytes).decode()
    if len(decrypted_hex) in (66, 42):
        decrypted_hex = decrypted_hex[2:]
    return '0x' + decrypted_hex
