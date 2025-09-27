import os, hashlib, bleach


ITERATIONS = 100000
HASH_ALGO = 'sha256'


def format_html(
    html: str,
    replacements: dict,
    sanitize: bool = False
) -> str:
    for key, value in replacements.items():
        if sanitize:
            cleaned = bleach.clean(value)
            linkified = bleach.linkify(cleaned)
            lined = linkified.replace("\n", "<br/>")
        else:
            lined = value

        html = html.replace(f"[{key}]", lined)

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
