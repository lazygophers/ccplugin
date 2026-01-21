"""
CCPlugin lib - Shared library for ccplugin with logging and utilities.
"""

from .logging import enable_debug, info, debug, error, warn

__all__ = ['enable_debug', 'info', 'debug', 'error', 'warn']