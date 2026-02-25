#!/usr/bin/env python3
import sys

import github

from tiny_git_cli_tools.config import Config


def create_github_client_conventionally(config: Config) -> github.Github:
    github_token = config.github_token

    if github_token is None:
        print('GitHub token is not configured. Please set github_token in ~/.config/tiny_git_tools/config.toml',
              file=sys.stderr)
        sys.exit(1)

    return github.Github(auth=github.Auth.Token(github_token))
