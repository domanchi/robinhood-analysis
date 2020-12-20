from typing import Any
from typing import Dict
from typing import List

from pyrh import Robinhood


def get_paginated_results(client: Robinhood, url: str) -> List[Dict[str, Any]]:
    output = []

    page = client.get(url)
    output.extend(page['results'])
    while page['next']:
        page = client.get(page['next'])
        output.extend(page['results'])

    return output
