from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import toml


@dataclass
class Config:
    """
    Configuration for Tiny Git Tools stored in ~/.config/tiny_git_tools/config.toml.
    """

    CONFIG_RELATIVE_PATH = Path('.config/tiny_git_tools/config.toml')
    CONFIG_DISPLAY_PATH = f"~/{CONFIG_RELATIVE_PATH.as_posix()}"

    @classmethod
    def read(cls, path: Path | None = None) -> "Config":
        config_path = (path or (Path.home() / cls.CONFIG_RELATIVE_PATH)).expanduser()

        try:
            with config_path.open('r') as f:
                data = toml.load(f)
        except FileNotFoundError:
            # Config file missing: return defaults
            return cls(openai_api_key=None, github_token=None)

        return cls(
            openai_api_key=data.get('openai_api_key', None),
            github_token=data.get('github_token', None),
        )

    openai_api_key: Optional[str]
    github_token: Optional[str]
