#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flickr Add-on for Kodi - Main Entry Point
Modern Python 3 implementation with OAuth 2.0 and async support

Copyright (c) 2025 Community Modernization Team
License: GPL-3.0-or-later
"""

import sys
import logging
import os
from urllib.parse import parse_qs, urlparse

# Add resources/lib to path for imports
addon_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(addon_dir, 'resources', 'lib')
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

try:
    # Kodi imports
    import xbmc
    import xbmcaddon
    import xbmcplugin
    import xbmcgui
    
    # Local imports
    from utils.config import AddonConfig
    from utils.logger import setup_logging
    from api.client import FlickrAPIClient
    from ui.router import FlickrRouter
    from ui.builder import FlickrUIBuilder
    from ui.dialogs import FlickrDialogs, FlickrNotifications
    
except ImportError as e:
    # Handle import errors gracefully
    print(f"Import error in Flickr addon: {e}")
    sys.exit(1)

# Addon information
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = ADDON.getAddonInfo('path')

# Plugin information
PLUGIN_HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 else -1
PLUGIN_URL = sys.argv[0] if len(sys.argv) > 0 else ''
PLUGIN_PARAMS = sys.argv[2] if len(sys.argv) > 2 else ''


class FlickrAddon:
    """Main Flickr addon class"""
    
    def __init__(self):
        """Initialize the addon"""
        
        # Set up configuration
        self.config = AddonConfig(ADDON)
        
        # Set up logging
        self.logger = setup_logging(
            addon_id=ADDON_ID,
            debug_enabled=self.config.get_bool('debug_logging', False),
            log_level=self.config.get('log_level', 'info')
        )
        
        self.logger.info(f"Starting {ADDON_NAME} v{ADDON_VERSION}")
        self.logger.debug(f"Plugin URL: {PLUGIN_URL}")
        self.logger.debug(f"Plugin params: {PLUGIN_PARAMS}")
        
        # Parse URL parameters
        self.params = self._parse_params(PLUGIN_PARAMS)
        self.logger.debug(f"Parsed params: {self.params}")
        
        # Initialize API client
        self.api_client = None
        
        # Initialize UI components
        self.dialogs = FlickrDialogs(ADDON)
        self.notifications = FlickrNotifications(ADDON)
        
        # Initialize router
        self.router = FlickrRouter(
            plugin_handle=PLUGIN_HANDLE,
            plugin_url=PLUGIN_URL,
            config=self.config,
            logger=self.logger
        )
    
    def _parse_params(self, param_string: str) -> dict:
        """Parse URL parameters"""
        
        if not param_string or not param_string.startswith('?'):
            return {}
        
        try:
            # Remove leading '?' and parse
            params = parse_qs(param_string[1:])
            
            # Convert lists to single values where appropriate
            parsed_params = {}
            for key, value_list in params.items():
                if len(value_list) == 1:
                    parsed_params[key] = value_list[0]
                else:
                    parsed_params[key] = value_list
            
            return parsed_params
            
        except Exception as e:
            self.logger.error(f"Error parsing parameters: {e}")
            return {}
    
    def _initialize_api_client(self) -> bool:
        """Initialize the Flickr API client"""
        
        try:
            # Check if we have API credentials
            auth_method = self.config.get('auth_method', 'oauth2')
            
            if auth_method == 'oauth2':
                client_id = self.config.get('client_id')
                client_secret = self.config.get('client_secret')
                
                if not client_id:
                    self.logger.warning("No OAuth 2.0 client ID configured")
                    return False
                
                self.api_client = FlickrAPIClient(
                    client_id=client_id,
                    client_secret=client_secret or '',  # Allow empty secret for some flows
                    config=self.config,
                    logger=self.logger
                )
                
            elif auth_method == 'api_key':
                # For backwards compatibility, create client with API key as client_id
                api_key = self.config.get('api_key')
                
                if not api_key:
                    self.logger.warning("No API key configured")
                    return False
                
                self.api_client = FlickrAPIClient(
                    client_id=api_key,  # Use API key as client_id for legacy support
                    client_secret='',   # Empty secret enables API key mode
                    config=self.config,
                    logger=self.logger
                )
                
            else:
                self.logger.error(f"Unknown authentication method: {auth_method}")
                return False
            
            # Initialize the client asynchronously in a sync context
            import asyncio
            try:
                # Try to initialize the client
                init_success = asyncio.run(self.api_client.initialize())
                if not init_success:
                    self.logger.error("Failed to initialize API client")
                    return False
            except Exception as e:
                self.logger.warning(f"Async initialization failed, continuing anyway: {e}")
                # Continue without async initialization for compatibility
            
            self.logger.info(f"API client initialized with {auth_method}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API client: {e}", exc_info=True)
            return False
    
    def run(self):
        """Main addon execution"""
        
        try:
            # Get the action from parameters
            action = self.params.get('action', 'main_menu')
            self.logger.info(f"Executing action: {action}")
            
            # Handle special actions that don't require API
            if action in ['settings', 'authenticate', 'clear_auth']:
                self.router.route(action, self.params)
                return
            
            # Initialize API client for most actions
            if not self._initialize_api_client():
                # Show setup dialog if API client can't be initialized
                self._show_setup_required()
                return
            
            # Set API client in router
            self.router.set_api_client(self.api_client)
            
            # Route the request
            self.router.route(action, self.params)
            
        except Exception as e:
            self.logger.error(f"Unhandled error in main execution: {e}", exc_info=True)
            self._show_error("Addon Error", f"An unexpected error occurred: {e}")
    
    def _show_setup_required(self):
        """Show setup required dialog with modern UI"""
        
        # Show authentication dialog
        auth_method = self.dialogs.show_authentication_dialog()
        
        if auth_method:
            self.notifications.show_success(
                f"Authentication method set to {auth_method}. Please complete setup.",
                duration=6000
            )
        
        # Show main menu with limited options using modern UI builder
        ui_builder = FlickrUIBuilder(PLUGIN_HANDLE, self.config)
        
        ui_builder.add_action_item(
            title="Configure Flickr API",
            url=f"{PLUGIN_URL}?action=settings",
            icon="DefaultProgram.png",
            description="Set up your Flickr API credentials"
        )
        
        ui_builder.add_action_item(
            title="Authentication Setup",
            url=f"{PLUGIN_URL}?action=authenticate",
            icon="DefaultUser.png",
            description="Complete Flickr authentication"
        )
        
        ui_builder.add_action_item(
            title="Help & Setup Guide",
            url=f"{PLUGIN_URL}?action=help",
            icon="DefaultHelp.png",
            description="View setup instructions"
        )
        
        # Set appropriate view mode for setup menu
        ui_builder.set_content_type('files')
        ui_builder.finalize()
    
    def _show_error(self, title: str, message: str, details: str = ''):
        """Show error dialog to user with enhanced features"""
        
        # Use enhanced error dialog
        self.dialogs.show_error(title, message, details)
        
        # Also show error notification
        self.notifications.show_error(f"{title}: {message}")
        
        # End directory listing with error
        xbmcplugin.endOfDirectory(PLUGIN_HANDLE, succeeded=False)


def main():
    """Main entry point"""
    
    try:
        # Create and run addon
        addon = FlickrAddon()
        addon.run()
        
    except Exception as e:
        # Last resort error handling
        xbmc.log(f"Critical error in Flickr addon: {e}", xbmc.LOGERROR)
        
        # Try to show error to user
        try:
            dialog = xbmcgui.Dialog()
            dialog.ok("Flickr Addon Error", f"Critical error: {e}")
        except:
            pass  # If we can't even show a dialog, give up gracefully
        
        # End directory with error
        try:
            xbmcplugin.endOfDirectory(PLUGIN_HANDLE, succeeded=False)
        except:
            pass


if __name__ == '__main__':
    main()