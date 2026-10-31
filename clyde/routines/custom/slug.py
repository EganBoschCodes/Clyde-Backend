import re

import clyde.utils as utils

from .types import KEY_PREFIX, PREVIEW_KEY


MAX_SLUG_LEN = 60
KEY_PATTERN = re.compile(r"^studio_[a-z0-9_]{1,60}$")


def slugify(name: str) -> utils.Result[str]:
    body = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:MAX_SLUG_LEN].strip("_")
    if not body:
        return utils.err(ValueError(f"Cannot derive a routine key from name '{name}'"))
    return utils.ok(f"{KEY_PREFIX}{body}")


def validate_key(key: str) -> utils.Result[str]:
    if KEY_PATTERN.match(key) is None:
        return utils.err(ValueError(f"Invalid routine key '{key}': expected '{KEY_PREFIX}' followed by lowercase letters, digits, underscores"))
    if key == PREVIEW_KEY:
        return utils.err(ValueError(f"'{PREVIEW_KEY}' is reserved"))
    return utils.ok(key)
