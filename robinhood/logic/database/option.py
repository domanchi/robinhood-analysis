import datetime
from urllib.parse import urlparse

from ... import database
from ...client import get_client
from ...models.option import Option as OptionModel
from ...models.option import OptionType
from .common import BaseDBLogic


class OptionDBLogic(BaseDBLogic):
    @property
    def MODEL(self) -> OptionModel:
        return OptionModel

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

        item = self.create(
            uuid=uuid,
            name=data['chain_symbol'],
            type=OptionType(data['type']),
            expiration_date=datetime.datetime.strptime(
                data['expiration_date'], '%Y-%m-%d',
            ).date(),
            strike_price=data['strike_price'],
        )
        database.session.commit()
        return item
