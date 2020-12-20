from urllib.parse import urlparse

from ... import database
from ...client import get_client
from ...models.stock import Stock as StockModel
from .common import BaseDBLogic


class StockDBLogic(BaseDBLogic):
    @property
    def MODEL(self) -> StockModel:
        return StockModel

    def get_from_instrument_url(self, url: str) -> str:
        """
        It looks like the Robinhood API uses UUIDs to map to individual "instruments".
        Since we don't want to make a network call to know which stock this refers to, let's
        just cache the results.
        """
        uuid = urlparse(url).path.rstrip('/').split('/')[-1]
        results = self.get(uuid=uuid)
        if results:
            return results[0]

        client = get_client()
        data = client.get(url)
        ticker = data['symbol']

        item = self.create(uuid=uuid, name=ticker)
        database.session.commit()
        return item
