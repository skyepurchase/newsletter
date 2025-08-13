import os, hashlib


ITERATIONS = 100000
HASH_ALGO = 'sha256'


def format_html(html: str, replacements: dict) -> str:
    for key, value in replacements.items():
        html = html.replace(f"[{key}]", value)

    return html


def hash_passcode(passcode: str) -> bytes:
    salt: bytes = os.urandom(16)

    hash_value: bytes = hashlib.pbkdf2_hmac(
        HASH_ALGO,
        passcode.encode('utf-8'),
        salt,
        ITERATIONS
    )

    return salt + hash_value


def verify(passcode: str, hash: bytes):
    salt, key = hash[:16], hash[16:]

    test_hash: bytes = hashlib.pbkdf2_hmac(
        HASH_ALGO,
        passcode.encode('utf-8'),
        salt,
        ITERATIONS
    )

    if key == test_hash:
        return True

    return False
