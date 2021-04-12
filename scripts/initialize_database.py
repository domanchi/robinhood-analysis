#!/usr/bin/env python3
import datetime

from robinhood import database
from robinhood.logic.stock_split import process_splits
from robinhood.logic.stock_split import Split


def main() -> None:
    database.session.setup()

    # Manually curated data
    process_splits([
        # Source: https://www.splithistory.com/ibb/
        Split(
            name='IBB', from_amount=1, to_amount=3,
            date=datetime.date(2017, 12, 1),
        ),

        # Source: https://www.splithistory.com/tsla/
        Split(
            name='TSLA', from_amount=1, to_amount=5,
            date=datetime.date(2020, 8, 31),
        ),
    ])


if __name__ == '__main__':
    main()
