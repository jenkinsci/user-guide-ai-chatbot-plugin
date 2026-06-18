import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections.abc import Callable
from typing import Any

JENKINS_DOCS_URL = "https://www.jenkins.io/"
PLUGIN_DOCS_URL = "https://plugins.jenkins.io/"
JENKINS_SUBREDDIT_URL = "https://old.reddit.com/r/jenkinsci/"
JENKINS_DISCOURSE_URL = "https://community.jenkins.io/"


def datetime_serializer(obj):
    """
    Custom serializer to handle datetime objects when saving to JSON.
    Converts datetime to an ISO format string.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} is not JSON serializable")


def convert_date_str_in_iso(date_str, format="%B %d, %Y"):
    """Convert a date str in a specific format human readable format in iso format."""
    return datetime.strptime(date_str, format).date().isoformat()


def read_json_file(input_path: Path | str, encoding="utf-8") -> Any:
    """Load JSON file and return data, with proper error handling."""
    try:
        with open(input_path, "r", encoding=encoding) as f:
            return json.load(f)

    except OSError as e:
        print(f"File error while reading {input_path}: {e}")
    except UnicodeDecodeError as e:
        print(f"File {input_path} is not using {encoding} encoding: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error in {input_path}: {e}")

    return None


def write_json_file(
    output_path: Path | str,
    data: dict | list,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii=False,
    default: Callable[[Any], Any] | None = None,
):
    """Write JSON file in output path and return True if successful otherwise False, with proper error handling."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding=encoding) as f:
            json.dump(
                data, f, ensure_ascii=ensure_ascii, indent=indent, default=default
            )
            return True

    except OSError as e:
        print(f"File error while writing to {data}: {e}")

    return False
