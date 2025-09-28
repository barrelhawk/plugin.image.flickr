# -*- coding: utf-8 -*-
"""
API package for Flickr Add-on
Handles Flickr API communication and authentication
"""

from .client import FlickrAPIClient
from .auth import FlickrOAuth2Manager

__all__ = [
    'FlickrAPIClient',
    'FlickrOAuth2Manager'
]