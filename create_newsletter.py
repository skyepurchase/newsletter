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

    folder = args.title.lower().replace(" ", "_")

    if not os.path.isdir(folder):
        os.makedirs(folder)

    base_config = {
        "name": args.title,
        "email": args.email,
        "folder": folder,
        "link": "https://skye.purchasethe.uk/projects/newsletter/",
        "issue": 1
    }

    with open(os.path.join(folder, "config.yaml"), "w") as f:
        yaml.dump(base_config, f)
    with open(os.path.join(folder, "emails.txt"), "w") as f:
        pass

    print(f"Update {os.path.join(folder, 'emails.txt')} to include the emails of the participants.")

    create_newsletter(args.title, pass_hash, folder)
