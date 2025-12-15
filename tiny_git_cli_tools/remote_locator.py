#!/usr/bin/env python3
from typing import final
from urllib.parse import urlparse
from abc import ABC, abstractmethod


class RemoteLocator(ABC):
    @abstractmethod
    def to_url(self) -> str:
        pass

    @property
    @abstractmethod
    def host(self) -> str:
        """
        Returns the repository host.
        """
        pass

    @property
    @abstractmethod
    def path(self) -> str:
        """
        Returns the repository path (without .git suffix).
        """
        pass

    @classmethod
    def parse_url(cls, url: str) -> "RemoteLocator":
        if url.startswith('https://'):
            parsed = urlparse(url)
            if not parsed.hostname or not parsed.path:
                raise ValueError(f'Unsupported HTTPS remote URL format: {url}')
            # Remove .git suffix if present
            path = parsed.path.lstrip('/')
            if path.endswith('.git'):
                path = path[:-4]
            return HttpsRemoteLocator(host=parsed.hostname, path=path)

        # Not really an URL, but it's called so in Git
        if '@' in url and ':' in url:
            left, path = url.split(':', 1)
            user, host = left.split('@', 1)
            # Remove .git suffix if present
            if path.endswith('.git'):
                path = path[:-4]
            return SshRemoteLocator(user=user, host=host, path=path)

        raise ValueError(f'Cannot parse remote URL: {url}')


@final
class HttpsRemoteLocator(RemoteLocator):
    def __init__(self, host: str, path: str):
        self._host = host
        self._path = path

    @property
    def host(self) -> str:
        """
        Returns the repository host.
        """
        return self._host

    @property
    def path(self) -> str:
        """
        Returns the repository path (without .git suffix).
        """
        return self._path

    def to_ssh(self, user: str) -> "SshRemoteLocator":
        return SshRemoteLocator(user=user, host=self._host, path=self._path)

    def to_url(self) -> str:
        # Always append .git extension
        return f'https://{self._host}/{self._path}.git'


@final
class SshRemoteLocator(RemoteLocator):
    def __init__(self, user: str, host: str, path: str):
        self._user = user
        self._host = host
        self._path = path

    @property
    def host(self) -> str:
        """
        Returns the repository host.
        """
        return self._host

    @property
    def path(self) -> str:
        """
        Returns the repository path (without .git suffix).
        """
        return self._path

    def to_https(self) -> "HttpsRemoteLocator":
        return HttpsRemoteLocator(host=self._host, path=self._path)

    def to_url(self) -> str:
        # Not really an URL, but it's called so in Git
        # Always append .git extension
        return f'{self._user}@{self._host}:{self._path}.git'
