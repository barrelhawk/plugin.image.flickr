#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flickr Add-on for Kodi - Entry Point
This file tries to use the new main.py first, then falls back to default.py if needed
"""

import sys
import os
import traceback

# Define a version for compatibility checks
ADDON_VERSION = "2.0.0"

# Add current directory to path
addon_dir = os.path.dirname(os.path.abspath(__file__))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

# Add lib directory to path
lib_dir = os.path.join(addon_dir, 'resources', 'lib')
if os.path.exists(lib_dir) and lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

try:
    # Kodi modules
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcplugin
    
    try:
        # Kodi Matrix and above
        import xbmcvfs
    except ImportError:
        # Already available in xbmc for older versions
        pass
    
    # Initialize addon
    ADDON = xbmcaddon.Addon()
    ADDON_ID = ADDON.getAddonInfo('id')
    
    # Log function for debugging
    def log(message, level=xbmc.LOGINFO):
        xbmc.log(f"{ADDON_ID}: {message}", level)
    
    # First ensure compatibility layer is loaded
    try:
        log("Setting up compatibility layer")
        from resources.lib import compat_settings
        compat_settings.setup_compatibility()
        
        # Make sure settings configuration will work
        try:
            # Kodi Matrix and above
            addon_data_path = xbmcvfs.translatePath('special://profile/addon_data/plugin.image.flickr/')
        except:
            # Kodi Leia and below
            addon_data_path = xbmc.translatePath('special://profile/addon_data/plugin.image.flickr/')
            
        if not os.path.exists(addon_data_path):
            os.makedirs(addon_data_path)
        
        # If this is first run, migrate settings
        settings_migration_flag = os.path.join(addon_data_path, '.settings_migrated')
        if not os.path.exists(settings_migration_flag):
            log("First run - migrating settings")
            compat_settings.migrate_settings()
            # Create flag file to prevent future migrations
            with open(settings_migration_flag, 'w') as f:
                f.write('1')
                
        # Try to register settings action (for configure button)
        try:
            from resources.lib.utils import settings_helper
            settings_helper.register_settings_action()
            log("Settings action registered successfully")
        except Exception as e:
            log(f"Failed to register settings action: {e}", xbmc.LOGWARNING)
    except Exception as e:
        log(f"Error setting up compatibility: {e}\n{traceback.format_exc()}", xbmc.LOGWARNING)
    
    # Try to use the modern main.py
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
        
        # Show a more helpful error dialog
        dialog = xbmcgui.Dialog()
        dialog.ok(
            "Flickr Add-on Error",
            "Failed to initialize the addon. This is likely due to a Python version mismatch or missing dependencies.",
            f"Error details: {str(e)[:100]}"
        )

except ImportError as e:
    # Kodi modules not available - we're probably running outside of Kodi
    print(f"Kodi modules not available: {e}")
except Exception as e:
    # Last resort error handling
    print(f"Critical error: {e}\n{traceback.format_exc()}")