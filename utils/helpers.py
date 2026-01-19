import os
import yaml
import traceback
import logging

from typing import Tuple
from .type_hints import EmptyConfig, NewsletterConfig


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
    try:
        with open(
            os.path.join("/home/atp45", newsletter_folder, "config.yaml"), "r"
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
            os.path.join("/home/atp45", newsletter_folder, "issue"), "r"
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
        defaults=config["defaults"],
    )
