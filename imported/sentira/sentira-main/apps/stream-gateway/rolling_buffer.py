from __future__ import annotations
import asyncio
from pathlib import Path
import time
import subprocess

class RollingBuffer:
    """Per-camera segment directory with deterministic bounded retention."""
    def __init__(self, root: str, camera_id: str, segment_seconds: int, retention_seconds: int):
        self.path = Path(root) / camera_id
        self.path.mkdir(parents=True, exist_ok=True)
        self.segment_seconds = segment_seconds
        self.retention_seconds = retention_seconds
        self.lock = asyncio.Lock()

    def pattern(self) -> str:
        return str(self.path / "segment-%Y%m%dT%H%M%S.mp4")

    async def cleanup(self) -> list[Path]:
        async with self.lock:
            cutoff = time.time() - self.retention_seconds
            expired = [f for f in self.path.glob("*.mp4") if f.stat().st_mtime < cutoff]
            for segment in expired:
                segment.unlink(missing_ok=True)
            return expired

    async def segments(self) -> list[Path]:
        async with self.lock:
            return sorted(self.path.glob("*.mp4"))

    async def select_interval(self, start_epoch: float, end_epoch: float) -> list[Path]:
        """Return only source segments overlapping an event interval by mtime.

        Segment/keyframe boundaries mean the resulting clip can include a small
        amount of adjacent video; callers must not claim a clip exists when this
        returns no source segments.
        """
        async with self.lock:
            return [segment for segment in sorted(self.path.glob("*.mp4"))
                    if segment.stat().st_mtime + self.segment_seconds >= start_epoch
                    and segment.stat().st_mtime <= end_epoch]

    async def assemble_clip(self, start_epoch: float, end_epoch: float, output: Path) -> Path | None:
        sources = await self.select_interval(start_epoch, end_epoch)
        if not sources:
            return None
        manifest = output.with_suffix('.concat.txt')
        manifest.write_text(''.join(f"file '{segment.resolve()}'\n" for segment in sources), encoding='utf-8')
        try:
            subprocess.run(['ffmpeg', '-nostdin', '-y', '-f', 'concat', '-safe', '0', '-i', str(manifest), '-c', 'copy', str(output)], check=True, capture_output=True, timeout=60)
            return output if output.exists() and output.stat().st_size else None
        finally:
            manifest.unlink(missing_ok=True)
