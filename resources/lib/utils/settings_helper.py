#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Settings helper for Flickr Add-on
Helps ensure settings UI is properly accessible
"""

import xbmc
import xbmcaddon
import xbmcgui
import sys

def register_settings_action():
    """
    Register a settings action in Kodi to ensure the settings button works
    This is a workaround for some Kodi versions where the settings button
    might not appear in the addon info dialog
    """
    try:
        # Get addon instance
        addon = xbmcaddon.Addon()
        addon_id = addon.getAddonInfo('id')
        
        # Log our attempt
        xbmc.log(f"{addon_id}: Registering settings action", xbmc.LOGINFO)
        
        # Execute an action to ensure settings are registered
        xbmc.executebuiltin(f'Addon.OpenSettings({addon_id})')
        xbmc.executebuiltin('Action(Back)')
        
        # Return success
        return True
    except Exception as e:
        xbmc.log(f"Failed to register settings action: {e}", xbmc.LOGERROR)
        return False

def open_settings():
    """
    Open addon settings directly
    """
    try:
        addon = xbmcaddon.Addon()
        addon_id = addon.getAddonInfo('id')
        xbmc.executebuiltin(f'Addon.OpenSettings({addon_id})')
        return True
    except Exception as e:
        xbmc.log(f"Failed to open settings: {e}", xbmc.LOGERROR)
        return False

def get_settings_version():
    """
    Determine which settings format is being used
    Returns: str - "v1" for Kodi 19+ (Matrix) or "v0" for older versions
    """
    try:
        # Try to detect Kodi version
        kodi_version = int(xbmc.getInfoLabel("System.BuildVersion").split('.')[0])
        return "v1" if kodi_version >= 19 else "v0"
    except:
        # If we can't determine version, check settings file format
        import os
        addon = xbmcaddon.Addon()
        settings_path = xbmc.translatePath(os.path.join(addon.getAddonInfo('path'), 'resources', 'settings.xml'))
        
        try:
            with open(settings_path, 'r') as f:
                content = f.read()
                if 'settings version="1"' in content:
                    return "v1"
                else:
                    return "v0"
        except:
            return "unknown"