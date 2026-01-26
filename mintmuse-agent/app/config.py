# mintmuse-agent/app/config.py
# ------------------------------------------------------
# Centralized environment variable loader
# Ensures .env is always loaded correctly regardless of
# how the application is started (uvicorn, tests, CLI)

import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------
# Explicitly locate and load the .env file
# This avoids issues with working directory differences
# ------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

def get_env_var(name: str, default=None):
    """
    Retrieve a required or optional environment variable.

    Args:
        name (str): Environment variable name
        default (any, optional): Fallback value if variable is missing

    Returns:
        str | any: Environment variable value

    Raises:
        ValueError: If variable is missing and no default is provided
    """
    value = os.getenv(name)

    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"Missing required environment variable: {name}")

    return value
