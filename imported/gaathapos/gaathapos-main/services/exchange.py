import requests
from datetime import datetime, timezone

EXCHANGE_API = "https://api.exchangerate.host/latest"


def fetch_exchange_rates(base='USD', symbols=None, timeout=10):
    """Fetch latest exchange rates from exchangerate.host.

    Returns dict of currency->rate or raises requests.RequestException.
    """
    params = {'base': base}
    if symbols:
        params['symbols'] = ','.join(symbols)
    r = requests.get(EXCHANGE_API, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if not data.get('success', True):
        raise RuntimeError('Exchange API returned unsuccessful response')
    rates = data.get('rates', {})
    # Ensure base currency present
    rates[base] = 1.0
    return {'rates': rates, 'timestamp': datetime.now(timezone.utc)}


def normalize_rates_dict(rates_dict, supported):
    """Return a dict filtered for supported currencies and ensure numeric rates."""
    out = {}
    for c in supported:
        val = rates_dict.get(c)
        if val is None:
            continue
        out[c] = float(val)
    return out
