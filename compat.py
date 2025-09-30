#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flickr Add-on for Kodi - Compatibility Bridge
This file serves as a bridge between the old default.py and Kodi's newer versions
"""

import sys
import os
import traceback

try:
    import xbmc
    import xbmcaddon
    import xbmcgui
except ImportError:
    # This is for local development - Kodi modules aren't available
    pass

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PATH = ADDON.getAddonInfo('path')

# Use the compatibility settings.xml for old code
old_settings_path = os.path.join(ADDON_PATH, 'resources', 'settings.old.xml')
settings_path = os.path.join(ADDON_PATH, 'resources', 'settings.xml')

# First attempt - if we're in newer Kodi and default.py fails
try:
    # Forward to the original default.py
    default_script = os.path.join(ADDON_PATH, 'default.py')
    
    # Import the module directly
    sys.path.insert(0, ADDON_PATH)
    import default
    
    # If we got here, it worked!
    xbmc.log(f"{ADDON_ID}: Successfully loaded default.py using compatibility wrapper", xbmc.LOGINFO)
    
except Exception as e:
    # Log the error
    error_msg = f"Error in default.py: {str(e)}\n{traceback.format_exc()}"
    xbmc.log(f"{ADDON_ID}: {error_msg}", xbmc.LOGERROR)
    
    # Show an error dialog
    import xbmcgui
    xbmcgui.Dialog().ok(
        "Flickr Add-on Error",
        f"Failed to initialize the Flickr addon.\n\nError: {str(e)}\n\nPlease check logs for more information."
    )