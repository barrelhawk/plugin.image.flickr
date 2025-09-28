# -*- coding: utf-8 -*-
"""
URL routing for Flickr Add-on
Handles navigation and action routing within the addon
"""

from typing import Dict, Any, Optional, Callable
import xbmcplugin
import xbmcgui


class FlickrRouter:
    """Router for handling Flickr addon actions"""
    
    def __init__(self, plugin_handle: int, plugin_url: str, config, logger):
        """Initialize router"""
        
        self.plugin_handle = plugin_handle
        self.plugin_url = plugin_url
        self.config = config
        self.logger = logger
        self.api_client = None
        
        # Route mapping
        self.routes: Dict[str, Callable] = {
            'main_menu': self.show_main_menu,
            'settings': self.open_settings,
            'authenticate': self.authenticate_user,
            'clear_auth': self.clear_authentication,
            'help': self.show_help,
            'photostream': self.show_photostream,
            'photosets': self.show_photosets,
            'browse_photoset': self.browse_photoset,
            'search': self.show_search,
            'search_photos': self.search_photos,
            'favorites': self.show_favorites,
            'contacts': self.show_contacts,
            'show_photo': self.show_photo,
            'slideshow': self.start_slideshow,
            'download': self.download_item,
            'refresh_cache': self.refresh_cache,
            'diagnostics': self.run_diagnostics
        }
    
    def set_api_client(self, api_client):
        """Set the API client for the router"""
        self.api_client = api_client
    
    def route(self, action: str, params: Dict[str, Any]) -> None:
        """Route an action to the appropriate handler"""
        
        self.logger.debug(f"Routing action: {action} with params: {params}")
        
        if action in self.routes:
            try:
                handler = self.routes[action]
                handler(params)
            except Exception as e:
                self.logger.error(f"Error executing action '{action}': {e}", exc_info=True)
                self._show_error("Action Error", f"Failed to execute {action}: {e}")
        else:
            self.logger.warning(f"Unknown action: {action}")
            self._show_error("Unknown Action", f"Action '{action}' is not supported")
    
    def show_main_menu(self, params: Dict[str, Any]) -> None:
        """Show the main menu"""
        
        from ui.builder import FlickrUIBuilder
        
        ui_builder = FlickrUIBuilder(self.plugin_handle, self.config)
        
        # Check if we're authenticated
        if self.config.is_authenticated():
            # Show full menu for authenticated users
            ui_builder.add_folder(
                title="My Photostream",
                url=f"{self.plugin_url}?action=photostream",
                thumbnail="resources/images/photostream.png",
                description="Browse your photo stream"
            )
            
            ui_builder.add_folder(
                title="My Photosets",
                url=f"{self.plugin_url}?action=photosets",
                thumbnail="resources/images/sets.png", 
                description="Browse your photo sets"
            )
            
            ui_builder.add_folder(
                title="My Favorites",
                url=f"{self.plugin_url}?action=favorites",
                thumbnail="resources/images/favorites.png",
                description="Browse your favorite photos"
            )
            
            ui_builder.add_folder(
                title="My Contacts",
                url=f"{self.plugin_url}?action=contacts",
                thumbnail="resources/images/contacts.png",
                description="Browse your contacts"
            )
        
        # Search is available to all users
        ui_builder.add_action_item(
            title="Search Photos",
            url=f"{self.plugin_url}?action=search",
            icon="resources/images/search_flickr.png",
            description="Search for photos on Flickr"
        )
        
        # Settings and help
        ui_builder.add_action_item(
            title="Settings",
            url=f"{self.plugin_url}?action=settings",
            icon="resources/images/settings.png",
            description="Configure addon settings"
        )
        
        ui_builder.add_action_item(
            title="Help",
            url=f"{self.plugin_url}?action=help",
            icon="resources/images/help.png",
            description="View help and setup instructions"
        )
        
        ui_builder.finalize()
    
    def open_settings(self, params: Dict[str, Any]) -> None:
        """Open addon settings"""
        
        # This will be handled by Kodi automatically
        # when the user selects the settings item
        pass
    
    def authenticate_user(self, params: Dict[str, Any]) -> None:
        """Handle user authentication"""
        
        if not self.api_client:
            self._show_error("Authentication Error", "API client not available")
            return
        
        try:
            # Start OAuth 2.0 flow
            from api.auth import FlickrOAuth2Manager
            
            auth_manager = FlickrOAuth2Manager(
                client_id=self.config.get('client_id'),
                client_secret=self.config.get('client_secret'),
                config=self.config,
                logger=self.logger
            )
            
            # This will be implemented in the auth module
            success = auth_manager.authenticate()
            
            if success:
                dialog = xbmcgui.Dialog()
                dialog.notification(
                    heading="Flickr Authentication",
                    message="Authentication successful!",
                    icon=xbmcgui.NOTIFICATION_INFO,
                    time=3000
                )
            else:
                self._show_error("Authentication Failed", "Could not authenticate with Flickr")
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}", exc_info=True)
            self._show_error("Authentication Error", str(e))
    
    def clear_authentication(self, params: Dict[str, Any]) -> None:
        """Clear authentication data"""
        
        dialog = xbmcgui.Dialog()
        
        if dialog.yesno(
            "Clear Authentication", 
            "Are you sure you want to clear your authentication data?"
        ):
            self.config.clear_authentication()
            
            dialog.notification(
                heading="Flickr Authentication",
                message="Authentication data cleared",
                icon=xbmcgui.NOTIFICATION_INFO,
                time=3000
            )
    
    def show_help(self, params: Dict[str, Any]) -> None:
        """Show help information"""
        
        help_text = """
Flickr Add-on Help

SETUP:
1. Get Flickr API credentials from https://www.flickr.com/services/apps/create/
2. Open addon Settings
3. Enter your Client ID and Client Secret
4. Select 'Authenticate' from the main menu

FEATURES:
- Browse your photostream, photosets, and favorites
- Search public photos on Flickr
- View photos in slideshow mode
- Download photos (if enabled)

TROUBLESHOOTING:
- If authentication fails, check your API credentials
- For network issues, check timeout settings
- Enable debug logging for detailed error information

For more help, visit:
https://github.com/barrelhawk/plugin.image.flickr
"""
        
        dialog = xbmcgui.Dialog()
        dialog.textviewer("Flickr Add-on Help", help_text)
    
    def show_photostream(self, params: Dict[str, Any]) -> None:
        """Show user's photostream"""
        
        if not self._ensure_authenticated():
            return
        
        # This will be implemented when we have the API client
        self._show_placeholder("Photostream", "User photostream will be shown here")
    
    def show_photosets(self, params: Dict[str, Any]) -> None:
        """Show user's photosets"""
        
        if not self._ensure_authenticated():
            return
        
        # This will be implemented when we have the API client
        self._show_placeholder("Photosets", "User photosets will be shown here")
    
    def browse_photoset(self, params: Dict[str, Any]) -> None:
        """Browse a specific photoset"""
        
        photoset_id = params.get('photoset_id')
        if not photoset_id:
            self._show_error("Error", "No photoset ID provided")
            return
        
        # This will be implemented when we have the API client
        self._show_placeholder("Browse Photoset", f"Photos from photoset {photoset_id}")
    
    def show_search(self, params: Dict[str, Any]) -> None:
        """Show search interface"""
        
        from ui.dialogs import FlickrDialogs
        
        dialogs = FlickrDialogs(self.config.addon)
        search_config = dialogs.show_search_dialog()
        
        if search_config:
            # Redirect to search results
            search_params = {
                'action': 'search_photos',
                'text': search_config['text'],
                'scope': search_config.get('scope', 'all'),
                'user_id': search_config.get('user_id', '')
            }
            
            self.search_photos(search_params)
    
    def search_photos(self, params: Dict[str, Any]) -> None:
        """Search for photos"""
        
        search_text = params.get('text')
        if not search_text:
            self._show_error("Error", "No search text provided")
            return
        
        # This will be implemented when we have the API client
        self._show_placeholder("Search Results", f"Search results for '{search_text}'")
    
    def show_favorites(self, params: Dict[str, Any]) -> None:
        """Show user's favorites"""
        
        if not self._ensure_authenticated():
            return
        
        # This will be implemented when we have the API client
        self._show_placeholder("Favorites", "User favorites will be shown here")
    
    def show_contacts(self, params: Dict[str, Any]) -> None:
        """Show user's contacts"""
        
        if not self._ensure_authenticated():
            return
        
        # This will be implemented when we have the API client
        self._show_placeholder("Contacts", "User contacts will be shown here")
    
    def show_photo(self, params: Dict[str, Any]) -> None:
        """Show a specific photo"""
        
        photo_id = params.get('photo_id')
        photo_url = params.get('url')
        
        if not photo_url:
            self._show_error("Error", "No photo URL provided")
            return
        
        # Create a simple image viewer
        from ui.builder import FlickrUIBuilder
        
        ui_builder = FlickrUIBuilder(self.plugin_handle, self.config)
        # For now, just end the directory - photo viewing will be enhanced later
        ui_builder.finalize()
    
    def start_slideshow(self, params: Dict[str, Any]) -> None:
        """Start slideshow"""
        
        # This will be implemented with the slideshow functionality
        self._show_placeholder("Slideshow", "Slideshow functionality coming soon")
    
    def download_item(self, params: Dict[str, Any]) -> None:
        """Download a photo or photoset"""
        
        # This will be implemented with download functionality
        self._show_placeholder("Download", "Download functionality coming soon")
    
    def refresh_cache(self, params: Dict[str, Any]) -> None:
        """Refresh cache"""
        
        dialog = xbmcgui.Dialog()
        dialog.notification(
            heading="Cache",
            message="Cache refresh not yet implemented",
            icon=xbmcgui.NOTIFICATION_INFO,
            time=3000
        )
    
    def run_diagnostics(self, params: Dict[str, Any]) -> None:
        """Run diagnostic checks"""
        
        diagnostics = []
        
        # Check configuration
        diagnostics.append(f"Addon Version: {self.config.addon_version}")
        diagnostics.append(f"Configured: {'Yes' if self.config.is_configured() else 'No'}")
        diagnostics.append(f"Authenticated: {'Yes' if self.config.is_authenticated() else 'No'}")
        diagnostics.append(f"Auth Method: {self.config.get('auth_method')}")
        
        # Check network settings
        network_settings = self.config.get_network_settings()
        diagnostics.append(f"Request Timeout: {network_settings['request_timeout']}s")
        diagnostics.append(f"Retry Attempts: {network_settings['retry_attempts']}")
        
        # Check cache settings
        cache_settings = self.config.get_cache_settings()
        diagnostics.append(f"Cache Enabled: {'Yes' if cache_settings['enabled'] else 'No'}")
        diagnostics.append(f"Cache Duration: {cache_settings['duration']}s")
        
        diagnostic_text = "\\n".join(diagnostics)
        
        dialog = xbmcgui.Dialog()
        dialog.textviewer("Flickr Addon Diagnostics", diagnostic_text)
    
    def _ensure_authenticated(self) -> bool:
        """Ensure user is authenticated"""
        
        if not self.config.is_authenticated():
            dialog = xbmcgui.Dialog()
            
            if dialog.yesno(
                "Authentication Required",
                "This feature requires authentication.\\n\\nWould you like to authenticate now?"
            ):
                self.authenticate_user({})
                return self.config.is_authenticated()
            
            return False
        
        return True
    
    def _show_placeholder(self, title: str, message: str) -> None:
        """Show a placeholder message for unimplemented features"""
        
        from ui.builder import FlickrUIBuilder
        
        ui_builder = FlickrUIBuilder(self.plugin_handle, self.config)
        
        ui_builder.add_action_item(
            title=message,
            url=f"{self.plugin_url}?action=main_menu",
            description="Feature coming soon"
        )
        
        ui_builder.finalize()
    
    def _show_error(self, title: str, message: str) -> None:
        """Show error to user"""
        
        self.logger.error(f"{title}: {message}")
        
        dialog = xbmcgui.Dialog()
        dialog.ok(title, message)
        
        # End directory with error
        xbmcplugin.endOfDirectory(self.plugin_handle, succeeded=False)