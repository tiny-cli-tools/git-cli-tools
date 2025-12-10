#!/usr/bin/env python3
import argparse
import sys
from typing import final, Tuple
from urllib.parse import urlparse
from enum import Enum
from abc import ABC, abstractmethod

from git import Repo, Remote


class RemoteProtocol(Enum):
    HTTPS = 'https'
    SSH = 'ssh'


class RemoteLocator(ABC):
    @abstractmethod
    def to_url(self) -> str:
        pass

    @classmethod
    def parse_url(cls, url: str) -> "RemoteLocator":
        if url.startswith('https://'):
            parsed = urlparse(url)
            if not parsed.hostname or not parsed.path:
                raise ValueError(f'Unsupported HTTPS remote URL format: {url}')
            return HttpsRemoteLocator(host=parsed.hostname, path=parsed.path.lstrip('/'))

        # Not really an URL, but it's called so in Git
        if '@' in url and ':' in url:
            left, path = url.split(':', 1)
            user, host = left.split('@', 1)
            return SshRemoteLocator(user=user, host=host, path=path)

        raise ValueError(f'Cannot parse remote URL: {url}')

@final
class HttpsRemoteLocator(RemoteLocator):
    def __init__(self, host: str, path: str):
        self._host = host
        self._path = path

    def to_ssh(self, user: str) -> "SshRemoteLocator":
        return SshRemoteLocator(user=user, host=self._host, path=self._path)

    def to_url(self) -> str:
        return f'https://{self._host}/{self._path}'

@final
class SshRemoteLocator(RemoteLocator):
    def __init__(self, user: str, host: str, path: str):
        self._user = user
        self._host = host
        self._path = path

    def to_https(self) -> "HttpsRemoteLocator":
        return HttpsRemoteLocator(host=self._host, path=self._path)

    def to_url(self) -> str:
        # Not really an URL, but it's called so in Git
        return f'{self._user}@{self._host}:{self._path}'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Change the URL protocol for a Git remote (https <-> ssh)."
        )
    )
    parser.add_argument('--repo-path', default='.', help='Path to the root of the Git repository')
    parser.add_argument('--remote', default='origin', help='Remote name to adjust')
    parser.add_argument('--protocol', choices=('https', 'ssh'), required=True, help='Target protocol to use')
    parser.add_argument('--user', default='git', help='Username for SSH protocol')

    return parser.parse_args()


def build_new_locator(
    current_locator: RemoteLocator,
    target_protocol: RemoteProtocol,
    user: str,
) -> RemoteLocator | None:
    if target_protocol == RemoteProtocol.HTTPS:
        if isinstance(current_locator, HttpsRemoteLocator):
            return
        elif isinstance(current_locator, SshRemoteLocator):
            return current_locator.to_https()
        else:
            raise ValueError(f'Unrecognized remote locator type: {type(current_locator)}')
    elif target_protocol == RemoteProtocol.SSH:
        if isinstance(current_locator, SshRemoteLocator):
            return
        elif isinstance(current_locator, HttpsRemoteLocator):
            return current_locator.to_ssh(user=user)
        else:
            raise ValueError(f'Unrecognized remote locator type: {type(current_locator)}')
    else:
        raise ValueError(f'Unrecognized target protocol: {target_protocol}')


def change_remote_protocol(
    remote: Remote,
    target_protocol: RemoteProtocol,
    user: str,
) -> None:
    current_url = next(iter(remote.urls))
    current_locator = RemoteLocator.parse_url(current_url)

    new_locator = build_new_locator(
        current_locator=current_locator,
        target_protocol=target_protocol,
        user=user,
    )

    if new_locator is None:
        print(f'Remote {remote.name} already uses {target_protocol.value} protocol.')
        return

    new_url = new_locator.to_url()
    remote.set_url(new_url)

    print(f'Updated {remote.name}: {current_url} -> {new_url}')


def main() -> None:
    args = parse_args()

    repo = Repo(args.repo_path)

    if repo.bare:
        print('Error: This is a bare repository.', file=sys.stderr)
        sys.exit(1)

    try:
        remote = repo.remotes[args.remote]
    except IndexError:
        print(f'Error: Remote {args.remote} does not exist.', file=sys.stderr)
        sys.exit(1)

    try:
        change_remote_protocol(
            remote=remote,
            target_protocol=RemoteProtocol(args.protocol),
            user=args.user,
        )
    except ValueError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
