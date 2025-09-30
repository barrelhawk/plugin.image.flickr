#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flickr Add-on for Kodi - Entry Point
This file tries to use the new main.py first, then falls back to default.py if needed
"""

import sys
import os
import traceback

# Add current directory to path
addon_dir = os.path.dirname(os.path.abspath(__file__))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

# Add lib directory to path
lib_dir = os.path.join(addon_dir, 'resources', 'lib')
if os.path.exists(lib_dir) and lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

try:
    # Try to import Kodi modules
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcplugin
    
    # Initialize addon
    ADDON = xbmcaddon.Addon()
    ADDON_ID = ADDON.getAddonInfo('id')
    
    # Log function for debugging
    def log(message, level=xbmc.LOGINFO):
        xbmc.log(f"{ADDON_ID}: {message}", level)
    
    # First try to use the modern main.py
    try:
        log("Trying to use modern main.py")
        import main
        if hasattr(main, 'main'):
            log("Using modern main.py")
            main.main()
            sys.exit(0)
    except ImportError as e:
        log(f"Could not import main.py: {e}", xbmc.LOGWARNING)
    except Exception as e:
        log(f"Error in main.py: {e}\n{traceback.format_exc()}", xbmc.LOGERROR)
    
    # Fall back to default.py if main.py fails
    try:
        log("Falling back to default.py")
        import default
        # No need to call anything - default.py executes on import
    except ImportError as e:
        log(f"Could not import default.py: {e}", xbmc.LOGERROR)
        
        # Show error dialog
        dialog = xbmcgui.Dialog()
        dialog.ok(
            "Flickr Add-on Error",
            f"Failed to initialize the addon. Neither main.py nor default.py could be loaded.\n\nError: {e}"
        )
    except Exception as e:
        log(f"Error in default.py: {e}\n{traceback.format_exc()}", xbmc.LOGERROR)
        
        # Show error dialog
        dialog = xbmcgui.Dialog()
        dialog.ok(
            "Flickr Add-on Error",
            f"Failed to initialize the addon. Error in default.py.\n\nError: {e}"
        )

except ImportError as e:
    # Kodi modules not available - we're probably running outside of Kodi
    print(f"Kodi modules not available: {e}")
except Exception as e:
    # Last resort error handling
    print(f"Critical error: {e}\n{traceback.format_exc()}")