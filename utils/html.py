import os, hashlib, bleach


ITERATIONS = 100000
HASH_ALGO = 'sha256'

DIR = os.path.dirname(__file__)
NAVBAR = open(
    os.path.join(DIR, "../templates/navbar.html")).read()


def format_html(
    html: str,
    replacements: dict,
    sanitize: bool = False
) -> str:
    for key, value in replacements.items():
        if key not in html:
            raise KeyError("Substitution key not found in text to replace")

        if sanitize:
            cleaned = bleach.clean(value)
            linkified = bleach.linkify(cleaned)
            lined = linkified.replace("\n", "<br/>")
        else:
            lined = value

        if lined is None: lined = ""
        html = html.replace(f"[{key}]", lined)

    return html


def make_navbar(
    issue: int,
    curr_issue: int
) -> str:
    if issue < 0 or issue > curr_issue:
        raise ValueError("Issue outside of valid range")

    p_valid = "disable" if issue <= 0 else ""
    n_valid = "disable" if issue >= curr_issue else ""
    c_valid = "disable" if issue == curr_issue else ""

    return format_html(
        NAVBAR,
        {
            "PREV" : str(max(issue - 1, 0)),
            "P_VALID": p_valid,
            "NEXT" : str(issue + 1),
            "N_VALID": n_valid,
            "C_VALID": c_valid
        }
     )


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
