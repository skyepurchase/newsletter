import os, yaml, traceback, logging

from typing import Tuple


logger = logging.getLogger('newsletter')


def get_config_and_issue(
    token: dict,
    HttpResponse
) -> Tuple[dict, int]:
    """
    Given JWT token parse the relevant config and issue file.
    Throws HttpResponses.

    Parameters
    ----------
    token : dict
        The dict of processed JSON web token
    HttpResponse : Error
        The suitable error to throw HTTP Responses

    Returns
    -------
    config : dict
        The configuration for this newsletter
    curr_issue : int
        The current issue
    """
    try:
        with open(
            os.path.join(
                "/home/atp45",
                token["newsletter_folder"],
                "config.yaml"
            ), "r"
        ) as config_file:
            config = yaml.safe_load(config_file)
    except OSError:
        logger.critical(f"Failed to load {token['newsletter_folder']}")
        raise HttpResponse(500, "Error loading config file")
    except yaml.YAMLError:
        logger.critical(f"Failed to parse {token['newsletter_folder']}")
        raise HttpResponse(500, "Error loading YAML configuration")

    try:
        with open(
            os.path.join(
                "/home/atp45",
                token["newsletter_folder"],
                "issue"
            ), "r"
        ) as issue_file:
            curr_issue = int(issue_file.read())
    except OSError:
        logger.critical(f"Failed to load {token['newsletter_folder']} issue file")
        raise HttpResponse(500, "Error loading issue file")
    except ValueError:
        logger.debug(traceback.format_exc())
        raise HttpResponse(500, "Error loading issue file")

    return config, curr_issue
