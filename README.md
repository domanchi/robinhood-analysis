# robinhood-analysis

This repository contains logic to process trades on your Robinhood portfolio, for better
financial analysis (at least, better than Robinhood provides out of the box). There are
two parts to its operation:

1. Extracting trades from Robinhood, and caching them into a local database.
2. Running analysis with Jupyter notebooks from data in said database.

## Setup

### Cloning the Repository

First, let's clone the repository to be able to run the analysis locally. Note that we use
git [submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) in order to work with
a local fork of the `pyrh` library (mainly because
https://github.com/robinhood-unofficial/pyrh/issues/282) has not been addressed upstream.

```bash
$ git clone https://github.com/domanchi/robinhood-analysis --recurse-submodules
$ cd robinhood-analysis
$ make minimal
```

### Logging In for the First Time

Now, we need to initialize our Robinhood client, so that our Jupyter notebook can retrieve
information from our portfolio accordingly. To do this, run

```python
from robinhood.client import get_client
get_client()
```

This will prompt you for your Robinhood username, password and MFA secret value (assuming
you use 2FA for your account). To obtain this secret value, sign into your Robinhood account,
and enable 2FA. Upon being prompted for which 2FA app you want to use, select "other" to
get an alphanumeric code.

If you've already enabled 2FA, you would need to create a new secret key by disabling 2FA,
then re-enabling it and following the steps above. It is recommended that you store this
secret in your preferred password manager so that you can use these notebooks again, without
needing to go through this process.

Once successful, this will create a `session.json` file locally, which stores OAuth2 tokens
that grant access to your account.

### Running the Analysis

Finally, you can run the Jupyter notebook in the analysis/ folder using your preferred
medium. Personally, I like the VSCode's built-in Jupyter kernel to do this. Be sure to
configure your jupyter notebook to use the correct Python kernel (specifically, the
one built by `make minimal` in `venv/bin/python`) as it will have reference to the
`robinhood` library that powers the analysis.

The notebooks will pull data from Robinhood's API (using the `pyrh` module, and credentials
found in `session.json`), and cache them in `database.sqlite3`. This is why you may find that
the initial analysis processing time may be slower, but subsequent runs (after the data is
cached) is much quicker.
