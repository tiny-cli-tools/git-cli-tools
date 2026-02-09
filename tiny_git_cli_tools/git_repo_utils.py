#!/usr/bin/env python3
import sys

from git import Repo


def open_repository(
        repo_path: str,
) -> Repo:
    repo = Repo(repo_path)

    if repo.bare:
        print('Error: This is a bare repository.', file=sys.stderr)
        sys.exit(1)

    return repo
