#!/usr/bin/env python3
import os
import sys

import openai

from tiny_git_cli_tools.config import Config


OPENAI_ENV_VAR = 'OPENAI_API_KEY'


def create_open_ai_client_conventionally(config: Config) -> openai.OpenAI:
    api_key = os.environ.get(OPENAI_ENV_VAR) or config.openai_api_key

    if api_key is None:
        print(
            f'OpenAI API key is not configured. Set {OPENAI_ENV_VAR} or openai_api_key in {Config.CONFIG_DISPLAY_PATH}',
            file=sys.stderr,
        )
        sys.exit(1)

    return openai.OpenAI(api_key=api_key)
