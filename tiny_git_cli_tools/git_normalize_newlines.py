#!/usr/bin/env python3
import argparse
import os
import sys
from enum import Enum
from typing import Callable, Union

from git import Commit, Repo

from .git_repo_utils import open_repository


class TrailingNewlineStatus(Enum):
    WAS_NORMALIZED = 1
    ALREADY_NORMALIZED = 2
    DECODING_ERROR = 3


def normalize_trailing_newline(string: str) -> str:
    """
    Normalizes the trailing newline(s) of a string to a single newline character.
    """
    return string.rstrip('\n') + '\n'


def rewrite_file_content(
        file_path: str,
        transform: Callable[[str], str],
) -> bool:
    """
    Replaces the content of the file at file_path using the transform function.
    Returns True if the file was changed, False otherwise.
    Throws an error if the file cannot be read or written.
    """
    with open(file_path, 'r+', encoding='utf-8') as file:
        old_content = file.read()
        new_content = transform(old_content)
        if old_content != new_content:
            file.seek(0)
            file.write(new_content)
            file.truncate()
            return True
        return False


def normalize_file_trailing_newline(file_path: str) -> TrailingNewlineStatus:
    """
    Adds a trailing newline to the file at the given path if it does not already have one.
    """
    try:
        was_changed = rewrite_file_content(
            file_path=file_path,
            transform=normalize_trailing_newline,
        )

        if was_changed:
            return TrailingNewlineStatus.WAS_NORMALIZED
        else:
            return TrailingNewlineStatus.ALREADY_NORMALIZED
    except UnicodeDecodeError:
        return TrailingNewlineStatus.DECODING_ERROR


def repo_index_diff(repo: Repo, other: Union[Commit, None]) -> set[str]:
    return set(
        item.a_path for item in repo.index.diff(other)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensure all touched text files in a Git repo have a trailing newline")
    parser.add_argument('--repo-path', help='Path to the root of the Git repository', default='.')
    args: argparse.Namespace = parser.parse_args()

    repo = open_repository(args.repo_path)

    # Get touched files (unstaged, staged, untracked)
    touched_file_paths: set[str] = repo_index_diff(
        repo=repo,
        other=None,
    ) | repo_index_diff(
        repo=repo,
        other=repo.head.commit,
    ) | set(repo.untracked_files)

    for git_file_path in touched_file_paths:
        absolute_file_path: str = os.path.join(args.repo_path, git_file_path)

        # All paths got from Git should be file paths, but add an extra check anyway
        if os.path.isfile(absolute_file_path):
            print(f"Processing file: {absolute_file_path}")

            status = normalize_file_trailing_newline(file_path=absolute_file_path)

            if status == TrailingNewlineStatus.WAS_NORMALIZED:
                print("Trailing newline(s) normalized successfully ℹ️")
            elif status == TrailingNewlineStatus.ALREADY_NORMALIZED:
                print("A single trailing newline was already present ✅")
            elif status == TrailingNewlineStatus.DECODING_ERROR:
                print("Decoding error! Is it binary? Ignoring ❌")


if __name__ == "__main__":
    main()
