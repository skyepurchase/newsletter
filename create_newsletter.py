import os
import yaml
from getpass import getpass
from argparse import ArgumentParser

from utils.html import hash_passcode
from utils.database import create_newsletter


def create(title: str, email: str,  passcode: str):
    pass_hash = hash_passcode(passcode)

    folder_name = title.lower().replace(" ", "_")
    folder = os.path.join("newsletters", folder_name)

    if not os.path.isdir(folder):
        os.makedirs(folder)
        # Not the most secure but it's something
        os.chmod(folder, 0o0710)

    base_config = {
        "name": title,
        "email": email,
        "folder": folder,
        "link": "https://skye.purchasethe.uk/projects/newsletter/",
        "issue": 1,
        "passphrase": passcode,
        "defaults": [
            ["⛅ One Good Thing", "text"],
            ["👀 Check It Out", "text"],
            ["📸 Photo Wall", "image"],
        ],
    }

    with open(os.path.join(folder, "config.yaml"), "w") as f:
        yaml.dump(base_config, f)
    open(os.path.join(folder, "emails.txt"), "w").close()
    open(os.path.join(folder, "log"), "w").close()

    print(
        f"Update {os.path.join(folder, 'emails.txt')} to include the emails of the participants."
    )

    create_newsletter(title, pass_hash, folder)


if __name__ == "__main__":
    parser = ArgumentParser("Create Newsletter")
    parser.add_argument("--title", required=True, help="The title of the newsletter.")
    parser.add_argument(
        "--email", required=True, help="The email to be used when sending out requests."
    )

    args = parser.parse_args()
    passcode = getpass("Passcode: ")

    create(args.title, args.email, passcode)
