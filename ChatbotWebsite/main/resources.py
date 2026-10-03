"""Data-backed support resources used by the public resource pages."""

import json
from pathlib import Path


SUPPORT_RESOURCES_PATH = (
    Path(__file__).resolve().parent.parent / "static" / "data" / "support_resources.json"
)


def get_support_resources():
    """Return the configured support resources, or an empty list if unavailable."""
    try:
        with SUPPORT_RESOURCES_PATH.open(encoding="utf-8") as resource_file:
            resources = json.load(resource_file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(resources, list):
        return []
    return [resource for resource in resources if isinstance(resource, dict)]
