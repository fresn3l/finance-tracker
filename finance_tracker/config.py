"""Configuration management for finance tracker."""

import logging
from pathlib import Path
from typing import Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class Config:
    """Application configuration."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to config file. Defaults to ~/.finance-tracker/config.yaml
        """
        if config_file is None:
            config_file = Path.home() / ".finance-tracker" / "config.yaml"

        self.config_file = Path(config_file)
        self.data: Dict = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_file.exists():
            self.data = self._default_config()
            self.save()
            logger.info(f"Created default config at {self.config_file}")
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Error loading config: {e}, using defaults")
            self.data = self._default_config()

    def save(self) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)

    def get(self, key: str, default=None):
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., "data.directory")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        data = self.data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    def _default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "data": {
                "directory": str(Path.home() / ".finance-tracker"),
            },
            "logging": {
                "level": "INFO",
                "file": None,  # None means console only
            },
            "categorization": {
                "auto_categorize": True,
                "overwrite_existing": False,
            },
            "duplicates": {
                "check_on_import": True,
                "skip_duplicates": True,
            },
        }


def get_config(config_file: Optional[Path] = None) -> Config:
    """
    Get configuration instance.

    Args:
        config_file: Optional path to config file

    Returns:
        Config instance
    """
    return Config(config_file)

