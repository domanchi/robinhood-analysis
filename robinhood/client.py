import io
import os
import sys
from contextlib import contextmanager
from functools import lru_cache
from getpass import getpass
from typing import Generator

import pyotp

from .util import get_path_to
from pyrh import dump_session
from pyrh import load_session
from pyrh import Robinhood
from pyrh.exceptions import AuthenticationError
from pyrh.exceptions import InvalidCacheFile


@lru_cache(maxsize=1)
def get_client():
    try:
        client = load_session(get_path_to('session.json'))
        client.user()
    except (AuthenticationError, InvalidCacheFile):
        email = os.environ.get('USERNAME') or input('Email: ')
        password = os.environ.get('PASSWORD') or getpass()
        mfa_secret = os.environ.get('MFA_SECRET') or getpass('MFA Secret: ')

        client = login(email, password, mfa_secret)
        dump_session(client, get_path_to('session.json'))

    return client


def login(email: str, password: str, mfa_secret: str) -> Robinhood:
    client = Robinhood(email, password)
    totp = pyotp.TOTP(mfa_secret)

    # We do this, because we don't want to modify the underlying API library
    # excessively to support this. Therefore, we monkey-patch our way to
    # success.
    with mock_stdin(totp.now()):
        client.login()

    return client


@contextmanager
def mock_stdin(value: str) -> Generator[None, None, None]:
    try:
        original = sys.stdin
        sys.stdin = io.StringIO(value)

        yield
    finally:
        sys.stdin = original
