import requests

BASE = "http://localhost:5000"

def check_health():
    r = requests.get(f"{BASE}/_health", timeout=5)
    print("Health:", r.status_code, r.text)

def check_protected(path):
    r = requests.get(f"{BASE}{path}", timeout=5)
    print(path, "->", r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)

if __name__ == '__main__':
    check_health()
    # Protected endpoints that require authentication should return 401 when unauthenticated
    check_protected('/api/v2/crm/customers')
    check_protected('/api/v2/books/invoices')
    check_protected('/expenses/')
    check_protected('/api/v2/inventory/items')
