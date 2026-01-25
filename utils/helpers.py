import os
import yaml
import traceback
import logging
from dotenv import load_dotenv
from pydantic import ValidationError

from typing import Tuple
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
        The folder that stores the newsletter config

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
