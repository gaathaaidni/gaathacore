from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OnvifCredentials:
    username: str = ""
    password: str = ""
    digest: bool = True


@dataclass(frozen=True)
class OnvifProfile:
    token: str
    name: str | None
    resolution: dict[str, int] | None
    encoding: str | None
    fps: float | None
    video_source: dict[str, Any] | None
    video_encoder: dict[str, Any] | None
