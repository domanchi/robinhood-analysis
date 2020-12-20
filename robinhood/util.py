from typing import Any
from typing import Dict
from typing import Generator

from pyrh import Robinhood


def get_paginated_results(
    client: Robinhood,
    url: str,
    **kwargs: Any
) -> Generator[Dict[str, Any], None, None]:
    page = client.get(url, **kwargs)
    yield from page['results']
    while page['next']:
        page = client.get(page['next'])
        yield from page['results']
