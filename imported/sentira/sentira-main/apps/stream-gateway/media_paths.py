"""Server-generated MediaMTX paths for controlled Sentira streams."""

import re


_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def media_path(organization_id: str, site_id: str, camera_id: str) -> str:
    """Build a stable path from trusted Sentira-owned identifiers.

    The path identifies a stream only. Media authorization must be enforced at
    the API/gateway boundary and is intentionally not inferred from this path.
    """
    identifiers = (organization_id, site_id, camera_id)
    if not all(identifier and _ID.fullmatch(identifier) for identifier in identifiers):
        raise ValueError("media identifiers must be non-empty URL-safe IDs")
    return f"sentira/{organization_id}/{site_id}/{camera_id}"


def media_path_parts(path: str) -> tuple[str, str, str] | None:
    parts = path.split("/")
    if len(parts) != 4 or parts[0] != "sentira" or not all(_ID.fullmatch(part) for part in parts[1:]):
        return None
    return parts[1], parts[2], parts[3]