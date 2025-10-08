# mintmuse-agent/app/config.py

import os
from dotenv import load_dotenv

# Load environment variables from the .env file into memory
load_dotenv()

def get_env_var(name, default=None):
    """
    Retrieve a required or optional environment variable.

    Parameters:
    - name: The name of the environment variable
    - default: Optional fallback value if variable is missing

    Returns:
    - The value of the environment variable

    Raises:
    - ValueError if the variable is not found and no default is provided
    """
    value = os.getenv(name)
    if not value and default is None:
        raise ValueError(f"Missing required env var: {name}")
    return value or default
