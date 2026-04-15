"""
OpenHarness Enterprise - Multi-user enterprise version.

This module extends OpenHarness with:
- Multi-user support
- Web-based chat interface
- Admin management
- Shared resources
"""

from openharness.enterprise.server import app, main

__version__ = "0.1.0"
__all__ = ["app", "main"]