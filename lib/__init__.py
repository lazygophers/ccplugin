"""
CCPlugin lib - Shared library for ccplugin with logging, utilities and database ORM.
"""

from . import logging
from .logging import enable_debug, info, debug, error, warn

__all__ = [
    'logging',
    'enable_debug',
    'info',
    'debug',
    'error',
    'warn',
]