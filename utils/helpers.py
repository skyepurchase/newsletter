import os
import yaml
import traceback
import logging
from dotenv import load_dotenv
from pydantic import ValidationError
from datetime import datetime

from typing import Optional, Tuple

from .constants import State
from .type_hints import EmptyConfig, NewsletterConfig


load_dotenv()


HOME = os.getenv("HOME")


def load_config(
    newsletter_folder: str, logger: logging.Logger
) -> Tuple[bool, NewsletterConfig]:
    """
    Given JWT token parse the relevant config and issue file.

    Parameters
    ----------
    newsletter_folder : str
        The folder that stores the newsletter config. Requires full path name.

    Returns
    -------
    success : bool
        Whether the config file was successfully loaded
    config : NewsletterConfig
        The configuration for this newsletter
    """
    if HOME is None:
        logger.critical("Failed to find home directory")
        return False, EmptyConfig

    try:
        with open(
            os.path.join(HOME, newsletter_folder, "config.yaml"), "r"
        ) as config_file:
            config = yaml.safe_load(config_file)
    except OSError:
        logger.warning(f"Failed to load {newsletter_folder}")
        return False, EmptyConfig
    except yaml.YAMLError:
        logger.warning(f"Failed to parse {newsletter_folder}")
        return False, EmptyConfig

    try:
        with open(os.path.join(HOME, newsletter_folder, "issue"), "r") as issue_file:
            issue = int(issue_file.read())
    except OSError:
        logger.warning(f"Failed to load {newsletter_folder} issue file")
        return False, EmptyConfig
    except ValueError:
        logger.warning(f"Failed to parse {newsletter_folder} issue file")
        logger.debug(traceback.format_exc())
        return False, EmptyConfig

    try:
        parsed_config = NewsletterConfig(
            name=config["name"],
            email=config["email"],
            folder=config["folder"],
            link=config["link"],
            issue=issue,
            defaults=config["defaults"],
        )
    except ValidationError:
        logger.warning(f"Failed to validate {newsletter_folder}")
        return False, EmptyConfig

    return True, parsed_config


def _get_int_state() -> int:
    """
    Return the current week modulo 4
    """
    week_num = int(datetime.now().strftime("%U"))
    return (week_num - 1) % 4  # Change in 2027


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
        Whether the incrementing succeeded. True if no incrementation required
    msg : str | None
        The error message if required
    """
    int_state = _get_int_state()

    if int_state == 0:
        try:
            with open(os.path.join(newsletter_folder, "issue"), "r+") as issue_file:
                issue = int(issue_file.read())
                issue_file.seek(0)
                issue_file.write(str(issue + 1))
        except OSError:
            return False, "Failed to open issue file"
        except ValueError:
            return False, "Failed to parse issue file"

    return True, None
