#!/usr/bin/env python3
import argparse
import sys
from git import Actor, Repo

from .git_rewrite_utils import rewrite_branch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite a branch so every commit uses a new author identity. "
            "Requires a clean working tree."
        )
    )
    parser.add_argument('--repo-path', default='.', help='Path to the root of the Git repository')
    parser.add_argument('--author-name', required=True, help='New author name')
    parser.add_argument('--author-email', required=True, help='New author email')
    parser.add_argument('--gpg-sign', action='store_true', help='Sign commits with GPG')

    return parser.parse_args()



def main() -> None:
    args = parse_args()

    new_author = Actor(args.author_name, args.author_email)

    repo = Repo(args.repo_path)

    if repo.bare:
        print('Error: This is a bare repository.', file=sys.stderr)
        sys.exit(1)

    if repo.is_dirty(untracked_files=True):
        print('Error: Working tree is dirty. Commit/stash your changes', file=sys.stderr)
        sys.exit(1)

    try:
        branch = repo.active_branch
    except TypeError:
        print('Error: Detached HEAD is not supported.', file=sys.stderr)
        sys.exit(1)

    rewrite_branch(
        repo=repo,
        branch=branch,
        new_author=new_author,
        should_sign=args.gpg_sign,
        should_rewrite=lambda commit: True,
    )


if __name__ == '__main__':
    main()
