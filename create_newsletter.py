import os, yaml
from getpass import getpass
from argparse import ArgumentParser

from utils.html import hash_passcode
from utils.database import create_newsletter


if __name__=='__main__':
    parser = ArgumentParser("Create Newsletter")
    parser.add_argument("--title", required=True, help="The title of the newsletter.")
    parser.add_argument("--email", required=True, help="The email to be used when sending out requests.")

    args = parser.parse_args()
    passcode = getpass("Passcode: ")
    pass_hash = hash_passcode(passcode)

    folder_name = args.title.lower().replace(" ", "_")
    folder = os.path.join("public_html/cgi-bin/newsletter/", folder_name)

    if not os.path.isdir(folder):
        os.makedirs(folder)
        # Not the most secure but it's something
        os.chmod(folder, 0o0710)

    base_config = {
        "name": args.title,
        "email": args.email,
        "folder": folder,
        "link": "https://skye.purchasethe.uk/projects/newsletter/",
        "issue": 1,
        "passphrase": passcode,
        "defaults": [
            ("⛅ One Good Thing", "text"),
            ("👀 Check It Out", "text"),
            ("📸 Photo Wall", "image")
        ]
    }

    with open(os.path.join(folder, "config.yaml"), "w") as f:
        yaml.dump(base_config, f)
    with open(os.path.join(folder, "emails.txt"), "w") as f:
        pass

    print(f"Update {os.path.join(folder, 'emails.txt')} to include the emails of the participants.")

    create_newsletter(args.title, pass_hash, folder)
