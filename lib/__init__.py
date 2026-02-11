"""
CCPlugin lib - Shared library for ccplugin with logging and utilities.
"""

from . import logging
from .logging import enable_debug, info, debug, error, warn

__all__ = [
    # Logging
    'logging',
    'enable_debug',
    'info',
    'debug',
    'error',
    'warn',
]