# CONTRIUBTING

This repository was written with the philosophy that while Jupyter is a fantastic tool for
data analysis/visualization, it leaves much to be desired when it comes to writing DRY code.
As such, it should **solely focus on the analysis component** (without needing to know the
details of data sourcing / transformations), leveraging a Python package to handle all the
boilerplate ETL work.

## Layout

```
/analysis           # this is where jupyter notebooks live
/pyrh               # keep a local copy of the library, since updates are not on pypi
/robinhood          # this is where ETL logic lives, to cache API data and make it usable
  |- logic          # Robinhood API processing
      |- database   # database interfaces
      |- dataframe  # ETL logic to facilitate better Jupyter notebooks
  |- models         # database tables, represented by sqlalchemy models
  |- client.py      # interface with pyrh library, and securely initializes connection
  |- database.py    # boilerplate database interface
/scripts            # convenient one-off scripts
```

## Development Flow

First, start with:

```bash
make development
```

This will install `pre-commit` to keep the code standardized with linters and other such
life improvements.

When you're pulling the latest changes, use the following command to also update submodules
(if relevant):

```bash
$ git pull origin master --recurse-submodules
```

### Making Changes to `analysis`

If you're just writing a new way to analyze the data, you can just create any relevant
notebooks in this directory. However, remember to **clear your analysis output** before
committing it to git, since we don't want your earnings info to be within Git history.

There's a handy `pre-commit` hook that enforces this. As long as you run `make development`
to setup your development environment, you should be fine.

### Making Changes to `robinhood`

Currently, there are no tests, since a lot of it is minimal ETL work. That is, it is more
likely that the API structure itself were to change (since this is an unofficial API) to cause
breakage, rather than the code itself.

As such, test your code manually, before committing changes.

### Making Changes to `pyrh`

We use git submodules to manage our local fork of `pyrh`. As such, there are some peculiarities
to abide by when making changes to files within this folder. However, as long as you abide by
the following guidelines, you should be fine:

1. Keep in mind that the `pyrh` clone is a completely separate git repo.

   If it helps, you can think about it as if `pyrh` was in a different directory (rather than
   being under `robinhood-analysis`). We bundle it together since development is so intertwined
   that it makes sense to group them together. Furthermore, it makes installation slightly easier
   (so we don't have to pip install from a git repository).

   Since it is in a different repository, any changes to its files needs to be within that
   directory. For example, to pull latest updates for `pyrh`, you need to do:

   ```bash
   cd pyrh && git pull origin master
   ```

2. The `robinhood-analysis` repository has a tracked file which pins the `pyrh` clone to a
   specific commit.

   As such, if you make changes to the `pyrh` repo, you would also need to make changes to the
   parent repository to pin it to your latest changes. For example, it might look something like:

   ```bash
   $ cd pyrh && git push origin master
   $ git add pyrh
   $ git commit -m 'bumping pyrh to add new feature'
   ```

3. When you pull the latest changes from `robinhood-analysis`, you only pull the latest commit
   for the submodule. There's an extra step to go into the submodule folder, and update it
   manually.

   Alternatively, if using git v2.20 or above, you can just use the `--recurse-submodules`
   during `git pull` to do this automatically.
