#!/usr/bin/env python3
"""Pre-deploy check: ensure SECRET_KEY exists and is not the dev default.

Exit codes:
 0 - ok
 1 - missing or default key
"""
import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=str(basedir / '.env'))
load_dotenv(dotenv_path=str(basedir / 'instance' / '.env'))

def main():
    key = os.environ.get('SECRET_KEY')
    if not key or key == 'dev_secret_change_me':
        print('ERROR: SECRET_KEY is missing or using default dev value')
        return 1
    print('OK: SECRET_KEY set')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
