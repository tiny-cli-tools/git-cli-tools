#!/usr/bin/env python3
import os
import sys

import github

from tiny_git_cli_tools.config import Config


GITHUB_ENV_VAR = 'GITHUB_TOKEN'


def create_github_client_conventionally(config: Config) -> github.Github:
    github_token = os.environ.get(GITHUB_ENV_VAR) or config.github_token

    if github_token is None:
        print(
            f'GitHub token is not configured. Set {GITHUB_ENV_VAR} or github_token in {Config.CONFIG_DISPLAY_PATH}',
            file=sys.stderr,
        )
        sys.exit(1)

    return github.Github(auth=github.Auth.Token(github_token))
