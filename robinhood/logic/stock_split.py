from collections import namedtuple
from typing import List

from .. import database
from .database.stock_split import StockSplitDBLogic


Split = namedtuple(
    'Split',
    (
        'name',
        'from_amount',
        'to_amount',
        'date',
    ),
)


def process_splits(splits: List[Split]) -> None:
    logic = StockSplitDBLogic()

    # Perform DB query everytime for now, because we don't expect to get much.
    for split in splits:
        should_process = True
        items = logic.get(name=split.name)
        if items:
            for item in items:
                # We make the (safe) assumption that (name, date) uniquely identifies
                # a stock split.
                if item.date == split.date:
                    should_process = False
                    break

        if not should_process:
            continue

        logic.create(**split._asdict())

    database.session.commit()


if __name__ == '__main__':
    # TODO: make interactive
    pass
