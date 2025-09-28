# -*- coding: utf-8 -*-
"""
UI package for Flickr Add-on
Handles all user interface components with modern Kodi features
"""

from .router import FlickrRouter
from .builder import FlickrUIBuilder, FlickrViewModes, FlickrContextMenu, FlickrSlideshow
from .dialogs import FlickrDialogs, FlickrNotifications, FlickrImageViewer, FlickrMediaPlayer

__all__ = [
    'FlickrRouter',
    'FlickrUIBuilder', 
    'FlickrViewModes',
    'FlickrContextMenu',
    'FlickrSlideshow',
    'FlickrDialogs',
    'FlickrNotifications',
    'FlickrImageViewer',
    'FlickrMediaPlayer'
]