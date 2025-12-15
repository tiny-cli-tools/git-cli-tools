#!/usr/bin/env python3
import argparse
import sys
from enum import Enum

from git import Repo, Remote

from .remote_locator import RemoteLocator, HttpsRemoteLocator, SshRemoteLocator


class RemoteProtocol(Enum):
    HTTPS = 'https'
    SSH = 'ssh'


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
            return None
        elif isinstance(current_locator, SshRemoteLocator):
            return current_locator.to_https()
        else:
            raise ValueError(f'Unrecognized remote locator type: {type(current_locator)}')
    elif target_protocol == RemoteProtocol.SSH:
        if isinstance(current_locator, SshRemoteLocator):
            return None
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
