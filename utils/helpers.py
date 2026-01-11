import os, yaml, traceback, logging

from typing import Tuple


logger = logging.getLogger('newsletter')


def get_config_and_issue(
        newsletter_folder: str) -> Tuple[bool, dict, int]:
    """
    Given JWT token parse the relevant config and issue file.

    Parameters
    ----------
    newsletter_folder : str
        The folder that stores the newsletter config

    Returns
    -------
    success : bool
        Whether the config file was successfully loaded
    config : dict
        The configuration for this newsletter
    curr_issue : int
        The current issue
    """
    try:
        with open(
            os.path.join(
                "/home/atp45",
                newsletter_folder,
                "config.yaml"
            ), "r"
        ) as config_file:
            config = yaml.safe_load(config_file)
    except OSError:
        logger.critical(f"Failed to load {newsletter_folder}")
        return False, {}, -1
    except yaml.YAMLError:
        logger.critical(f"Failed to parse {newsletter_folder}")
        return False, {}, -1

    try:
        with open(
            os.path.join(
                "/home/atp45",
                newsletter_folder,
                "issue"
            ), "r"
        ) as issue_file:
            curr_issue = int(issue_file.read())
    except OSError:
        logger.critical(f"Failed to load {newsletter_folder} issue file")
        return False, {}, -1
    except ValueError:
        logger.debug(traceback.format_exc())
        return False, {}, -1

    return True, config, curr_issue
