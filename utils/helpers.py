import os
import yaml
import traceback
import logging
from datetime import datetime

from typing import Optional, Tuple

from .constants import State
from .type_hints import EmptyConfig, NewsletterConfig


NOW = datetime.now()


def load_config(
    newsletter_folder: str,
    logger: logging.Logger
) -> Tuple[bool, NewsletterConfig]:
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
    config : NewsletterConfig
        The configuration for this newsletter
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
        return False, EmptyConfig
    except yaml.YAMLError:
        logger.critical(f"Failed to parse {newsletter_folder}")
        return False, EmptyConfig

    try:
        with open(
            os.path.join(
                "/home/atp45",
                newsletter_folder,
                "issue"
            ), "r"
        ) as issue_file:
            issue = int(issue_file.read())
    except OSError:
        logger.critical(f"Failed to load {newsletter_folder} issue file")
        return False, EmptyConfig
    except ValueError:
        logger.debug(traceback.format_exc())
        return False, EmptyConfig

    return True, NewsletterConfig(
        name=config["name"],
        email=config["email"],
        folder=config["folder"],
        link=config["link"],
        issue=issue,
        defaults=config["defaults"]
    )


def _get_int_state() -> int:
    """
    Return the current week modulo 4
    """
    week_num = int(datetime.now().strftime("%U"))
    return (week_num - 1) % 4 # Change in 2027


def get_state() -> State:
    """
    Get the current newsletter state based on the current time.

    Returns
    -------
    state : State
        An enum representing the current state
    """
    int_state = _get_int_state()

    if int_state <= 1:
        return State.Question
    elif int_state == 2:
        return State.Answer
    else:
        return State.Publish


def check_and_increment_issue(newsletter_folder: str) -> Tuple[bool, Optional[str]]:
    """
    Check whether the issue number should be incremented and increment it if so.

    Returns
    -------
    success : bool
        Whether the incrementing succeeded. True if not incrementation required
    msg : str | None
        The error message if required
    """
    int_state = _get_int_state()

    if int_state == 0:
        try:
            with open(
                os.path.join("/home/atp45", newsletter_folder, "issue"), "r"
            ) as issue_file:
                issue = int(issue_file.read())
                issue_file.write(str(issue+1))
        except OSError:
            return False, "Failed to open issue file"
        except ValueError:
            return False, "Failed to parse issue file"

    return True, None
