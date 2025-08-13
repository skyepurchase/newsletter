from getpass import getpass
from argparse import ArgumentParser

from utils import hash_passcode
from database import create_newsletter


if __name__=='__main__':
    parser = ArgumentParser("Create Newsletter")
    parser.add_argument("--title", help="The title of the newsletter")

    args = parser.parse_args()
    passcode = getpass("Passcode: ")
    pass_hash = hash_passcode(passcode)

    create_newsletter(args.title, pass_hash)
