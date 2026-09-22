"""Deterministic synthetic RTSP publisher for MediaMTX integration runs.

Run inside the Compose network with the server-generated default path, or pass
`--path` only for an explicit local fixture path.
It uses FFmpeg's generated test pattern; no camera or downloaded media is used.
"""
import argparse
import subprocess

from media_paths import media_path

def command(path: str, host: str) -> list[str]:
    return ['ffmpeg', '-re', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=10', '-f', 'lavfi', '-i', 'sine=frequency=880', '-shortest', '-c:v', 'libx264', '-g', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-f', 'rtsp', '-rtsp_transport', 'tcp', f'rtsp://{host}:8554/{path}']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path')
    parser.add_argument('--organization-id', default='fixture-org')
    parser.add_argument('--site-id', default='fixture-site')
    parser.add_argument('--camera-id', default='fixture-camera')
    parser.add_argument('--host', default='mediamtx')
    args = parser.parse_args()
    path = args.path or media_path(args.organization_id, args.site_id, args.camera_id)
    raise SystemExit(subprocess.call(command(path, args.host)))
