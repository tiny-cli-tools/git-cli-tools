#!/usr/bin/env python3
import argparse
import sys
from git import Repo

from .git_rewrite_utils import rewrite_branch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite all recent unsigned commits, signing them. "
            "Requires a clean working tree."
        )
    )
    parser.add_argument('--repo-path', default='.', help='Path to the root of the Git repository')
    parser.add_argument('--remote-name', default='origin', help='Name of the remote to push changes to')
    parser.add_argument('--push-changes', action='store_true', help='Push rewritten branch to remote')

    return parser.parse_args()


def main() -> None:
    args = parse_args()

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
        new_author=None,
        should_sign=True,
        should_rewrite=lambda commit: not commit.gpgsig,
    )

    print('Successfully signed all unsigned commits.')

    if args.push_changes:
        remote = repo.remotes[args.remote_name]

        remote.push(
            f'+{branch.name}:{branch.name}',
            force=True,
        )

        print(f'Pushed rewritten branch {branch.name} to remote.')


if __name__ == '__main__':
    main()
