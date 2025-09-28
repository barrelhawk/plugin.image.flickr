# -*- coding: utf-8 -*-
"""
Cache package for Flickr Add-on
Provides caching functionality for API responses and metadata
"""

from .manager import CacheManager, APICache

__all__ = [
    'CacheManager',
    'APICache'
]