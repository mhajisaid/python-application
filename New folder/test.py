from Crypto.Cipher import AES # type: ignore
from Crypto.Random import get_random_bytes # type: ignore

key = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_EAX)
nonce = cipher.nonce
ciphertext, tag = cipher.encrypt_and_digest(b'Test message')

print("Encryption successful")