"""Common utilities."""

import re


def create_slug(*names: str) -> str:
    """Create slug.

    from app.common.utils import create_slug
    """
    return "-".join(
        [
            re.sub(
                r"[\W_]+", "-", n.lower().strip().removesuffix("-").removeprefix("-")
            )
            for n in names
        ]
    )
