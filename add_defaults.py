from utils.database import insert_default_question, get_newsletters
from utils.html import verify

from typing import List, Tuple


def main(
    issue: int,
    passcode: str,
    questions: List[Tuple[str, str]]
) -> None:
    """
    Insert default questions into the current newsletter issue.

    Parameters
    ----------
    issue : int
        The issue number
    passcode : str
        The passcode to authenticate the newsletter
    questions : list[tuple[str, str]]
        A list of (question, type) tuples to insert
    """
    for entry in get_newsletters():
        n_id, _, n_hash, _ = entry

        if verify(passcode, n_hash):
            for question, form in questions:
                insert_default_question(
                    n_id,
                    issue,
                    question,
                    form
                )
            return

    print("Failed to access newsletter with provided credentials")



if __name__=='__main__':
    import yaml, sys
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--config", required=True, help="The configuration file to use.")

    args = parser.parse_args()

    try:
        with open(args.config, "r") as f:
            config = yaml.safe_load(f.read())
    except:
        print(f"Failed to load config file {args.config}.")
        sys.exit(1)

    main(
        config["issue"],
        config["passphrase"],
        config["defaults"]
    )
