#!/usr/bin/env python3
import argparse
import json
import sys


def main() -> int:
    args = parse_args()
    for filename in args.filenames:
        try:
            assert_jupyter_file_has_no_output(filename)
        except AssertionError:
            print(
                f'ERROR: {filename} still has analysis results in the notebook!',
            )
            print(
                'For privacy reasons, we try to prevent such cases. Please clear all output '
                'from your notebook.',
            )
            return 1

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filenames',
        nargs='*',
        help='Filenames to check.',
    )

    return parser.parse_args()


def assert_jupyter_file_has_no_output(filename: str) -> None:
    with open(filename) as f:
        data = json.loads(f.read())

    for cell in data['cells']:
        assert len(cell.get('outputs', [])) == 0


if __name__ == '__main__':
    sys.exit(main())
