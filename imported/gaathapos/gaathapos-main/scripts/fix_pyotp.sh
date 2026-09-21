#!/usr/bin/env bash
set -euo pipefail

# fix_pyotp.sh
# Usage: bash fix_pyotp.sh
# Run this on PythonAnywhere (SSH or Bash console) to install pyotp into your virtualenv,
# verify the import, append it to requirements-production.txt and print next steps.

USER_HOME="$(eval echo ~${USER})"
# Candidate project directories (common typos handled)
CANDIDATES=("$USER_HOME/nexorapos" "$USER_HOME/serviopos" "$USER_HOME/nexorapos/nexorapos" "$USER_HOME/serviopos/nexorapos")
PROJECT_DIR=""
for p in "${CANDIDATES[@]}"; do
  if [ -d "$p" ]; then
    PROJECT_DIR="$p"
    break
  fi
done

if [ -z "$PROJECT_DIR" ]; then
  echo "ERROR: Could not find project directory. Checked:" >&2
  for p in "${CANDIDATES[@]}"; do echo "  - $p"; done
  echo "Please run this script from your account where your Gaatha POS repo is located." >&2
  exit 1
fi

echo "Using project directory: $PROJECT_DIR"

# Detect virtualenv pip/python. Common location on PythonAnywhere: ~/.virtualenvs/nexorapos
VENV_PIP=""
VENV_PY=""
if [ -x "$USER_HOME/.virtualenvs/nexorapos/bin/pip" ]; then
  VENV_PIP="$USER_HOME/.virtualenvs/nexorapos/bin/pip"
  VENV_PY="$USER_HOME/.virtualenvs/nexorapos/bin/python"
elif [ -x "$PROJECT_DIR/venv/bin/pip" ]; then
  VENV_PIP="$PROJECT_DIR/venv/bin/pip"
  VENV_PY="$PROJECT_DIR/venv/bin/python"
elif command -v pip3 >/dev/null 2>&1; then
  # Fallback to system pip (not ideal) — warn
  echo "WARNING: No dedicated virtualenv detected; falling back to system pip. This may not affect your WSGI process." >&2
  VENV_PIP="$(command -v pip3)"
  VENV_PY="$(command -v python3)"
else
  echo "ERROR: Could not find pip. Please ensure a virtualenv exists or install pip." >&2
  exit 1
fi

echo "Using pip: $VENV_PIP"
echo "Using python: $VENV_PY"

# Install common missing packages and verify imports
echo "Installing common missing packages into virtualenv..."
PACKAGES=(pyotp qrcode Pillow python-barcode)
"$VENV_PIP" install --upgrade pip setuptools wheel

INSTALLED_VERS=( )
for pkg in "${PACKAGES[@]}"; do
  echo "Installing: $pkg"
  "$VENV_PIP" install "$pkg"
done

echo "Verifying imports and collecting versions..."
set +e
IMPORT_REPORT=$("$VENV_PY" - <<'PY'
results = []
mapping = {
  'pyotp': 'pyotp',
  'qrcode': 'qrcode',
  'Pillow': 'PIL',
  'python-barcode': 'barcode'
}
import importlib, traceback
for pkg_name, mod in mapping.items():
  try:
    m = importlib.import_module(mod)
    ver = getattr(m, '__version__', None)
    if ver is None:
      # try alternative version attribute
      ver = getattr(m, 'VERSION', None) or getattr(m, 'version', None) or 'unknown'
    results.append((pkg_name, 'OK', str(ver)))
  except Exception:
    results.append((pkg_name, 'FAIL', traceback.format_exc()))
for r in results:
  print('|'.join(r))
PY
)
set -e

echo "Import report:" 
echo "$IMPORT_REPORT"

REQ_FILE="$PROJECT_DIR/requirements-production.txt"
# Append to requirements file if not present
if [ -f "$REQ_FILE" ]; then
  if grep -Eiq '^pyotp(==|[>=<])' "$REQ_FILE"; then
    echo "requirements-production.txt already contains pyotp entry. Skipping append."
  else
    echo "Appending pyotp==$VER to $REQ_FILE"
    printf "pyotp==%s\n" "$VER" >> "$REQ_FILE"
    echo "Appended. You may want to commit this change:"
    echo "  cd $PROJECT_DIR && git add requirements-production.txt && git commit -m 'chore: add pyotp to requirements' && git push origin main"
  fi
else
  echo "WARNING: $REQ_FILE not found. Creating with pyotp==$VER"
  printf "pyotp==%s\n" "$VER" > "$REQ_FILE"
  echo "Created $REQ_FILE — commit and push as needed."
fi

# Ensure instance dir exists (helpful for DB issues too)
INSTANCE_DIR="$PROJECT_DIR/instance"
if [ ! -d "$INSTANCE_DIR" ]; then
  echo "Creating instance directory: $INSTANCE_DIR"
  mkdir -p "$INSTANCE_DIR"
  chmod 700 "$INSTANCE_DIR"
else
  echo "instance directory exists: $INSTANCE_DIR"
fi

# Try to initialize the DB (safe operation — creates tables if not present)
echo "Attempting to run db.create_all() to ensure DB file can be created (if DB is sqlite)..."
"$VENV_PY" - <<PY
import os
os.chdir(r"$PROJECT_DIR")
try:
    from app import create_app
    from models import db
    app = create_app()
    with app.app_context():
        db.create_all()
        print('DB init: OK, engine=', db.engine.url)
except Exception as e:
    import traceback
    traceback.print_exc()
    print('DB init: FAILED (see traceback above)')
    raise
PY

echo "\nDONE: pyotp installed and basic initialization attempted."

cat <<EOF
Next steps (manual):
 1) Reload your PythonAnywhere web app from the Web tab so WSGI picks up the new packages.
 2) Check the error log: Web tab -> Error log. If more ModuleNotFoundError messages appear, run this script again to install the missing packages.
 3) Commit the requirements file change if desired:
    cd $PROJECT_DIR
    git add requirements-production.txt
    git commit -m "chore: add pyotp to requirements"
    git push origin main

If you want me to also create a Git commit automatically, re-run the script with GIT_COMMIT=1 environment variable set.
Example:
  GIT_COMMIT=1 bash fix_pyotp.sh
EOF

# Optionally auto-commit if requested
if [ "${GIT_COMMIT-}" = "1" ]; then
  if command -v git >/dev/null 2>&1 && [ -d "$PROJECT_DIR/.git" ]; then
    echo "Auto-committing requirements-production.txt"
    cd "$PROJECT_DIR"
    git add requirements-production.txt || true
    git commit -m "chore: add pyotp to requirements" || true
    git push origin main || true
    echo "Auto-commit attempt complete (check output above)."
  else
    echo "GIT_COMMIT=1 requested but no git repo found or git not installed. Skipping auto-commit."
  fi
fi

exit 0
