#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Settings compatibility layer for Flickr add-on
This handles the transition between old and new settings formats
"""

import os
import sys
import xbmcaddon
import xbmc

def setup_compatibility():
    """Setup compatibility for different Kodi versions"""
    addon = xbmcaddon.Addon()
    addon_id = addon.getAddonInfo('id')
    addon_path = addon.getAddonInfo('path')
    
    # Determine Kodi version
    kodi_version = get_kodi_version()
    
    # Use appropriate settings file
    if kodi_version < 19:  # Pre-Matrix
        # Use old settings format
        settings_file = "settings.old.xml"
    else:
        # Use new settings format
        settings_file = "settings.xml"
    
    # Log the setup
    xbmc.log(f"{addon_id}: Using {settings_file} for Kodi version {kodi_version}", xbmc.LOGINFO)
    
    return True

def get_kodi_version():
    """Get the current Kodi version"""
    try:
        kodi_version = int(xbmc.getInfoLabel("System.BuildVersion").split('.')[0])
    except:
        # If we can't determine version, assume newer
        kodi_version = 19
    return kodi_version

def migrate_settings():
    """Migrate settings from old format to new format"""
    addon = xbmcaddon.Addon()
    
    # Map old settings to new ones
    settings_map = {
        'authenticate': 'authenticate',
        'api_key': 'api_key',
        'client_id': 'client_id',
        'client_secret': 'client_secret',
        'flickr_username': 'flickr_username',
        'network_token_path': 'network_token_path',
        'default_thumb_size': 'thumb_size',
        'default_display_size': 'display_size',
        'max_per_page': 'items_per_page',
        'enable_maps': 'enable_maps',
        'save_path': 'download_path'
    }
    
    # Read old settings and set new ones
    for old_key, new_key in settings_map.items():
        try:
            value = addon.getSetting(old_key)
            if value:
                addon.setSetting(new_key, value)
        except:
            pass

# Run setup on import
setup_compatibility()