#!/usr/bin/env python3
import sys

import openai

from tiny_git_cli_tools.config import Config


def create_open_ai_client_conventionally(config: Config) -> openai.OpenAI:
    api_key = config.openai_api_key

    if api_key is None:
        print(
            f'OpenAI API key is not configured. Please set openai_api_key in {Config.CONFIG_DISPLAY_PATH}',
            file=sys.stderr,
        )
        sys.exit(1)

    return openai.OpenAI(api_key=api_key)
