#!/usr/bin/env python3
import argparse
import sys
import tempfile
import textwrap
from pathlib import Path
from urllib.parse import quote

import github
from github import GithubException, UnknownObjectException
from git import GitCommandError, Repo

from tiny_git_cli_tools.config import Config
from tiny_git_cli_tools.github_utils import create_github_client_conventionally
from tiny_git_cli_tools.git_repo_utils import open_repository_conventionally
from tiny_git_cli_tools.remote_locator import RemoteLocator


class _AnsiColors:
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    RESET = '\033[0m'


def _print_success(message: str) -> None:
    print(f"{_AnsiColors.GREEN}{message}{_AnsiColors.RESET}")


def _print_warning(message: str) -> None:
    print(f"{_AnsiColors.YELLOW}{message}{_AnsiColors.RESET}")


def _print_error(message: str) -> None:
    print(f"{_AnsiColors.RED}{message}{_AnsiColors.RESET}", file=sys.stderr)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize the GitHub organization profile repository (.github).")
    parser.add_argument(
        '--organization-name',
        help='Override the organization that owns the repository.',
    )
    parser.add_argument(
        '--repo-path',
        default='.',
        help='Path to a GitHub repository that belongs to the organization (used for inference).',
    )
    parser.add_argument(
        '--remote',
        default='origin',
        help='Remote name used to infer the organization when --organization-name is missing.',
    )
    return parser.parse_args()


def _build_remote_url(token: str, organization_name: str) -> str:
    encoded_token = quote(token, safe='')
    return f'https://x-access-token:{encoded_token}@github.com/{organization_name}/.github.git'


def _write_profile_readme(path: Path, organization_name: str) -> None:
    path.write_text(f"# {organization_name}\n")


def _create_temp_repo_and_push(token: str, organization_name: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        repo = Repo.init(repo_path)
        repo.git.checkout('-b', 'main')

        profile_dir = repo_path / 'profile'
        profile_dir.mkdir(parents=True)

        readme_path = profile_dir / 'README.md'
        _write_profile_readme(readme_path, organization_name=organization_name)

        repo.index.add([str(readme_path.relative_to(repo_path))])
        repo.index.commit('Add organization profile README')

        remote_url = _build_remote_url(token=token, organization_name=organization_name)
        repo.create_remote('origin', remote_url)

        try:
            repo.remotes.origin.push(refspec='main:main', set_upstream=True)
        except GitCommandError as exc:
            _print_error(f'Failed to push to {remote_url}: {exc}')
            sys.exit(1)


def main() -> None:
    args = _parse_args()
    repo = open_repository_conventionally(args.repo_path)

    try:
        remote = repo.remotes[args.remote]
    except IndexError:
        _print_error(f'Remote {args.remote} does not exist.')
        sys.exit(1)

    remote_url = next(iter(remote.urls))
    try:
        remote_locator = RemoteLocator.parse_url(remote_url)
    except ValueError as exc:
        _print_error(str(exc))
        sys.exit(1)

    if remote_locator.host != 'github.com':
        _print_error(f'Remote host {remote_locator.host} is not supported. Only github.com is supported.')
        sys.exit(1)

    inferred_org = remote_locator.path.split('/', 1)[0] if '/' in remote_locator.path else remote_locator.path
    organization_name = args.organization_name or inferred_org

    if not organization_name:
        _print_error('Could not infer an organization name from the remote. Please provide --organization-name.')
        sys.exit(1)

    config = Config.read()
    github_client, github_token = create_github_client_conventionally(config)

    try:
        organization = github_client.get_organization(organization_name)
    except UnknownObjectException:
        _print_error(f'Organization {organization_name} was not found. Please verify the name.')
        sys.exit(1)
    except GithubException as exc:
        _print_error(f'GitHub API error while fetching organization: {exc}')
        sys.exit(1)

    repo_name = '.github'
    try:
        organization.get_repo(repo_name)
        _print_success(f'Organization repository {organization_name}/{repo_name} already exists. Nothing to do.')
        return
    except UnknownObjectException:
        _print_warning(f'{organization_name}/{repo_name} does not exist. Creating it now...')
    except GithubException as exc:
        _print_error(f'GitHub API error while checking repository: {exc}')
        sys.exit(1)

    try:
        organization.create_repo(
            name=repo_name,
            private=False,
            auto_init=False,
        )
        _print_success(f'Created GitHub repository {organization_name}/{repo_name}.')
    except GithubException as exc:
        _print_error(f'GitHub API error while creating repository: {exc}')
        sys.exit(1)

    _print_warning('Preparing a temporary repository to push the initial profile README...')
    _create_temp_repo_and_push(token=github_token, organization_name=organization_name)
    _print_success(f'Initial profile README pushed to {organization_name}/{repo_name}.')


if __name__ == '__main__':
    main()
