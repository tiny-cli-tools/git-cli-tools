#!/usr/bin/env python3
import sys
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError


def open_repository(
        repo_path: str,
) -> Repo:
    path = Path(repo_path).resolve()

    repo = _try_open_repository_recursively(path)

    if repo is None:
        print(f'Error: Not a Git repository (or any parent up to root): {repo_path}', file=sys.stderr)
        sys.exit(1)

    if repo.bare:
        print(f'Error: Repository at {repo_path} is bare, which is not supported', file=sys.stderr)
        sys.exit(1)

    print(f'Opened repository at {repo.working_tree_dir}')

    return repo


def _try_open_repository_recursively(
        repo_path: Path,
) -> Repo | None:
    repo = _try_open_repository(repo_path)

    if repo is None:
        parent_path = repo_path.parent

        if parent_path == repo_path:
            # Reached filesystem root
            return None
        return _try_open_repository_recursively(parent_path)
    else:
        return repo


def _try_open_repository(
        repo_path: Path,
) -> Repo | None:
    try:
        repo = Repo(repo_path)

        return repo
    except InvalidGitRepositoryError:
        return None
