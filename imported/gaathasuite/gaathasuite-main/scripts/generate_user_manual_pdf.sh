#!/usr/bin/env bash
# Simple helper to generate USER_MANUAL.pdf using pandoc
set -e
if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc is not installed. Install pandoc and try again."
  echo "On Debian/Ubuntu: sudo apt install pandoc"
  exit 1
fi
pandoc USER_MANUAL.md -o USER_MANUAL.pdf
echo "USER_MANUAL.pdf generated."
