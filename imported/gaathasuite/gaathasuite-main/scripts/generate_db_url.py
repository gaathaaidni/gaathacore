#!/usr/bin/env python3
"""Generate a safe SQLAlchemy database URL (percent-encodes password).
Usage: python scripts/generate_db_url.py postgres password host dbname
"""
import sys
from urllib.parse import quote_plus

if len(sys.argv) != 5:
    print("Usage: generate_db_url.py <user> <password> <host> <dbname>")
    sys.exit(1)

user, password, host, db = sys.argv[1:5]
enc = quote_plus(password)
print(f"postgresql+psycopg2://{user}:{enc}@{host}:5432/{db}?sslmode=require")
