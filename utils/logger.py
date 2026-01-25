import logging
import os
from dotenv import load_dotenv


load_dotenv()


LOG_DIR = os.getenv("LOG_DIR", "/dev/null")


def setup_logger(name, log_file, level=logging.DEBUG):
    log_dir = os.path.dirname(log_file)
    if not os.path.isdir(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError:
            log_file = "/dev/null"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s %(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


renderer_logger = setup_logger("renderer", os.path.join(LOG_DIR, "renderer"))
mailer_logger = setup_logger("mailer", os.path.join(LOG_DIR, "mailer"))
database_logger = setup_logger("database", os.path.join(LOG_DIR, "database"))
