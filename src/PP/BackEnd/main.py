"""WAOOAW Platform Portal - Backend API.

This module re-exports the actual ASGI `app` defined in `main_proxy.py`.
"""

from main_proxy import app


__all__ = ["app"]
