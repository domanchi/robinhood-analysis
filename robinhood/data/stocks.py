import json
from functools import lru_cache
from typing import Dict
from urllib.parse import urlparse

from ..client import get_client


def get_stock_ticker_from_instrument(url: str) -> str:
    """
    :param url: https://api.robinhood.com/instruments/8f6e5846-e6e3-4452-a1a2-5a46a630bd73/
    """
    uuid = urlparse(url).path.rstrip('/').split('/')[-1]
    try:
        return get_stocks()[uuid]
    except KeyError:
        client = get_client()
        data = client.get(url)
        ticker = data['symbol']

        get_stocks()[uuid] = ticker
        return ticker


@lru_cache(maxsize=1)
def get_stocks(filename: str = 'stocks.json') -> Dict[str, str]:
    """
    It looks like the Robinhood API uses UUIDs to map to individual "instruments".
    Since we don't want to make a network call to know which stock this refers to, let's
    just cache the results.
    """
    try:
        return load_from_disk(filename)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        pass

    return {}


def save_to_disk(filename: str = 'stocks.json') -> None:
    with open(filename, 'w') as f:
        f.write(json.dumps(get_stocks(), indent=2))


def load_from_disk(filename: str) -> None:
    """
    :raises: FileNotFoundError
    :raises: json.decoder.JSONDecodeError
    """
    with open(filename) as f:
        return json.loads(f.read())
