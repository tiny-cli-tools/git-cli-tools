from dataclasses import dataclass
from typing import Optional

import toml
from pathlib import Path

_config_path = '~/.config/tiny_git_tools/config.toml'

@dataclass
class Config:
    """
    Configuration for Tiny Git Tools stored in ~/.config/tiny_git_tools/config.toml.
    """

    @classmethod
    def read(cls) -> "Config":
        config_path = Path(_config_path).expanduser()

        try:
            with config_path.open('r') as f:
                data = toml.load(f)
        except FileNotFoundError:
            # Config file missing: return defaults
            return cls(openai_api_key=None)

        return cls(
            openai_api_key=data.get('openai_api_key', None),
            github_token=data.get('github_token', None),
        )

    openai_api_key: Optional[str]
    github_token: Optional[str]
