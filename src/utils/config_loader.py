"""Configuration loader for the Cloner project."""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any


class ConfigLoader:
    """Load and manage configuration from YAML and environment variables."""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_env()
        self._load_yaml()

    def _load_env(self):
        """Load environment variables from .env file."""
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

    def _load_yaml(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Replace environment variable placeholders
        self._replace_env_vars(self.config)

    def _replace_env_vars(self, config: Dict[str, Any]):
        """
        Recursively replace environment variable placeholders in config.

        Placeholders should be in the format: ${VAR_NAME}
        """
        for key, value in config.items():
            if isinstance(value, dict):
                self._replace_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                config[key] = os.getenv(env_var, value)

    def get(self, *keys, default=None):
        """
        Get a configuration value using dot notation.

        Args:
            *keys: Sequence of keys to traverse
            default: Default value if key doesn't exist

        Returns:
            The configuration value or default

        Example:
            config.get("voice", "elevenlabs", "api_key")
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            section: The section name

        Returns:
            Dictionary containing the section configuration
        """
        return self.config.get(section, {})

    def __getitem__(self, key: str):
        """Allow dictionary-style access to config."""
        return self.config[key]

    def __repr__(self):
        """String representation of the configuration."""
        return f"ConfigLoader(config_path={self.config_path})"
