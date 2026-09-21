#!/bin/bash
# Gaatha Suite Project Restructuring Script

echo "🚀 Starting physical project restructuring..."

# Create primary directories
mkdir -p backend/app
mkdir -p backend/blueprints/books
mkdir -p frontend/src
mkdir -p frontend/public
mkdir -p scripts

# Move Backend core files
mv app.py backend/ 2>/dev/null
mv main.py backend/ 2>/dev/null
mv config.py backend/ 2>/dev/null
mv extensions.py backend/ 2>/dev/null
mv requirements.txt backend/ 2>/dev/null
mv models.py backend/ 2>/dev/null
mv app/ backend/ 2>/dev/null
mv blueprints/ backend/ 2>/dev/null
mv migrations/ backend/ 2>/dev/null

# Move Frontend assets
mv package.json frontend/ 2>/dev/null
mv vite.config.js frontend/ 2>/dev/null
mv .eslintrc.cjs frontend/ 2>/dev/null
mv static/* frontend/public/ 2>/dev/null

# Vite standard: index.html should be at the frontend root, not in public
mv frontend/public/index.html frontend/ 2>/dev/null

# Cleanup and sync
mv .env backend/ 2>/dev/null

echo "✅ Restructuring complete. Backend and Frontend are now decoupled."