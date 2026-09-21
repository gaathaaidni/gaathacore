#!/bin/bash
# Script to clear Python bytecode and temporary export files

echo "Cleaning Gaatha Suite cache..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf /tmp/export_*

echo "Cache cleared successfully."