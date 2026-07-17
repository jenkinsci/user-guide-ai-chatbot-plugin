import os
import sys
from dotenv import load_dotenv
import json

OPTIONAL_ENV_VARS = ["QDRANT_SECRET_KEY"]

REQUIRED_ENV_VARS = [
    "QDRANT_HOST",
    "QDRANT_PORT",
    "QDRANT_SSL",
    "QDRANT_COLLECTION_NAME",
    "ALLOW_ORIGINS",
    "HUGGING_FACE_EMBEDDING_NAME",
    "POSTGRES_URL",
    "JWT_SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
]


def get_env(key: str) -> str:
    clean_key = key.strip()
    value = os.getenv(clean_key, "")

    return value


def get_env_as_list(key: str, ok: bool = True) -> list[str]:
    clean_key = key.strip()
    json_value = os.getenv(clean_key, "[]")

    try:
        return json.loads(json_value)
    except:
        if ok:
            return []
        else:
            raise Exception("Env list is formatted incorrectly")


def verify_env_variables():
    """
    Loads the .env file and verifies that all required variables are present and not empty.
    """
    # Load environment variables from the .env file into os.environ
    load_dotenv()

    missing_vars = []

    for env_var in REQUIRED_ENV_VARS:
        # os.getenv returns None if the variable does not exist
        value = os.getenv(env_var)

        # We check both for existence (None) and for empty strings
        if value is None or value.strip() == "":
            missing_vars.append(env_var)

    if missing_vars:
        # Print errors to standard error stream
        print(
            "CRITICAL ERROR: Missing or empty environment variables in .env file:",
            file=sys.stderr,
        )

        for missing in missing_vars:
            print(f"  - {missing}", file=sys.stderr)

        print(
            "\nPlease ensure your .env file is correctly configured before starting the application.",
            file=sys.stderr,
        )

        # Exit the program immediately with an error code to stop execution
        sys.exit(1)

    print("SUCCESS: All required environment variables are present and valid.")


if __name__ == "__main__":
    verify_env_variables()
