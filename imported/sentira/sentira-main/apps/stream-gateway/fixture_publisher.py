"""Deterministic synthetic RTSP publisher for MediaMTX integration runs.

Run inside the Compose network: `python fixture_publisher.py --path fixture`.
It uses FFmpeg's generated test pattern; no camera or downloaded media is used.
"""
import argparse
import subprocess

def command(path: str, host: str) -> list[str]:
    return ['ffmpeg', '-re', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=10', '-f', 'lavfi', '-i', 'sine=frequency=880', '-shortest', '-c:v', 'libx264', '-g', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-f', 'rtsp', '-rtsp_transport', 'tcp', f'rtsp://{host}:8554/{path}']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--path', default='fixture'); parser.add_argument('--host', default='mediamtx'); args = parser.parse_args()
    raise SystemExit(subprocess.call(command(args.path, args.host)))
