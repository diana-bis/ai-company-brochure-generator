
"""
Website scraping utilities.

Reuses the existing scraper.py implementation to avoid
duplicating scraping logic.
"""

from scraper import (
    fetch_website_contents,
    fetch_website_links,
)

__all__ = [
    "fetch_website_contents",
    "fetch_website_links",
]
