#!/usr/bin/env python3
import argparse
import sys

from .git_rewrite_utils import rewrite_branch
from .git_repo_utils import open_repository_conventionally


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
    parser.add_argument(
        '--base-branch',
        default=None,
        help='Base branch to rewrite until (e.g., origin/main). If provided, rewrites all commits until the merge base instead of stopping at the first unsigned commit.'
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    repo = open_repository_conventionally(args.repo_path)

    if repo.is_dirty(untracked_files=True):
        print('Error: Working tree is dirty. Commit/stash your changes', file=sys.stderr)
        sys.exit(1)

    try:
        branch = repo.active_branch
    except TypeError:
        print('Error: Detached HEAD is not supported.', file=sys.stderr)
        sys.exit(1)

    if args.base_branch:
        try:
            base_commit = repo.commit(args.base_branch)
        except ValueError:
            print(f'Error: Could not find base branch: {args.base_branch}', file=sys.stderr)
            sys.exit(1)

        merge_bases = repo.merge_base(branch.commit, base_commit)

        if not merge_bases:
            print(f'Error: No common ancestor found between {branch.name} and {args.base_branch}', file=sys.stderr)
            sys.exit(1)

        merge_base_sha = merge_bases[0].hexsha

        print(f'Will rewrite commits until merge base: {merge_base_sha[:8]}')

        rewrite_branch(
            repo=repo,
            branch=branch,
            new_author=None,
            should_sign=True,
            should_rewrite=lambda commit: commit.hexsha != merge_base_sha
        )
    else:
        print('Will rewrite all unsigned commits until the first signed commit.')

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
