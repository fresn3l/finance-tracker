"""
Utility modules for configuration and logging.

This package contains utility modules that provide cross-cutting concerns:
- Configuration management (YAML-based settings)
- Logging setup and configuration
- Common helper functions

These utilities are used throughout the application to maintain consistency
in configuration and logging.
"""

from finance_tracker.config import get_config
from finance_tracker.logging_config import setup_logging

__all__ = ["get_config", "setup_logging"]

