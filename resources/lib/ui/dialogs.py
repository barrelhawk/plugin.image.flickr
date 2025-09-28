# -*- coding: utf-8 -*-
"""
Dialog utilities for Flickr Add-on
Handles user interaction dialogs and input forms
"""

from typing import Optional, Dict, Any, List, Union
import xbmcgui
import xbmcaddon


class FlickrDialogs:
    """Dialog utilities for user interaction"""
    
    def __init__(self, addon: xbmcaddon.Addon):
        """Initialize dialogs"""
        self.addon = addon
    
    def show_search_dialog(self) -> Optional[Dict[str, Any]]:
        """Show search configuration dialog"""
        
        dialog = xbmcgui.Dialog()
        
        # Get search text
        search_text = dialog.input(
            heading="Search Photos",
            type=xbmcgui.INPUT_ALPHANUM
        )
        
        if not search_text:
            return None
        
        # Get search scope
        scope_options = [
            "All Photos",
            "My Photos", 
            "My Contacts' Photos",
            "Specific User"
        ]
        
        scope_index = dialog.select("Search Scope", scope_options)
        if scope_index == -1:
            return None
        
        scope_map = {
            0: 'all',
            1: 'mine',
            2: 'contacts',
            3: 'user'
        }
        
        scope = scope_map[scope_index]
        user_id = ""
        
        # If specific user selected, get user ID
        if scope == 'user':
            user_id = dialog.input(
                heading="Enter Flickr User ID or Username",
                type=xbmcgui.INPUT_ALPHANUM
            )
            
            if not user_id:
                return None
        
        return {
            'text': search_text,
            'scope': scope,
            'user_id': user_id
        }
    
    def show_download_dialog(
        self,
        title: str,
        available_sizes: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Show download options dialog"""
        
        dialog = xbmcgui.Dialog()
        
        # Show size selection
        size_labels = [f"{size['label']} ({size['width']}x{size['height']})" 
                      for size in available_sizes]
        
        size_index = dialog.select("Select Image Size", size_labels)
        if size_index == -1:
            return None
        
        selected_size = available_sizes[size_index]
        
        # Get download location
        download_path = dialog.browse(
            type=0,  # ShowAndGetDirectory
            heading="Select Download Location",
            shares='files',
            defaultt=self.addon.getSetting('download_path') or ''
        )
        
        if not download_path:
            return None
        
        return {
            'size': selected_size,
            'path': download_path,
            'title': title
        }
    
    def show_slideshow_options(self) -> Optional[Dict[str, Any]]:
        """Show slideshow configuration dialog"""
        
        dialog = xbmcgui.Dialog()
        
        # Get slideshow interval
        interval_options = ["3 seconds", "5 seconds", "10 seconds", "15 seconds", "30 seconds"]
        interval_values = [3, 5, 10, 15, 30]
        
        interval_index = dialog.select("Slideshow Interval", interval_options)
        if interval_index == -1:
            return None
        
        # Get transition effect
        effect_options = ["None", "Fade", "Slide"]
        effect_index = dialog.select("Transition Effect", effect_options)
        if effect_index == -1:
            effect_index = 0
        
        # Get shuffle option
        shuffle = dialog.yesno("Slideshow Options", "Shuffle photos?")
        
        return {
            'interval': interval_values[interval_index],
            'effect': effect_options[effect_index].lower(),
            'shuffle': shuffle
        }
    
    def show_authentication_dialog(self) -> Optional[str]:
        """Show authentication setup dialog"""

        # Get localized strings (use hardcoded strings for now)
        title = "Flickr Authentication"
        message = "Choose authentication method"

        # Show selection dialog
        options = [
            "OAuth 2.0 (Recommended)",
            "API Key Only"
        ]

        dialog = xbmcgui.Dialog()
        choice = dialog.select(title, options)

        if choice == 0:
            return self._setup_oauth2()
        elif choice == 1:
            return self._setup_api_key()
        else:
            return None

    def _setup_oauth2(self) -> Optional[str]:
        """Setup OAuth 2.0 authentication"""

        dialog = xbmcgui.Dialog()

        # Get client credentials
        client_id = dialog.input(
            heading="Enter Client ID",
            type=xbmcgui.INPUT_ALPHANUM
        )

        if not client_id:
            return None

        client_secret = dialog.input(
            heading="Enter Client Secret",
            type=xbmcgui.INPUT_ALPHANUM,
            option=xbmcgui.ALPHANUM_HIDE_INPUT
        )

        if not client_secret:
            return None

        # Save credentials
        self.addon.setSetting('auth_method', 'oauth2')
        self.addon.setSetting('client_id', client_id)
        self.addon.setSetting('client_secret', client_secret)

        # Show next steps
        dialog.ok(
            "Authentication Setup",
            "Credentials saved. Please authorize from the main menu."
        )

        return 'oauth2'

    def _setup_api_key(self) -> Optional[str]:
        """Setup API key authentication"""

        dialog = xbmcgui.Dialog()

        api_key = dialog.input(
            heading="Enter API Key",
            type=xbmcgui.INPUT_ALPHANUM
        )

        if api_key:
            self.addon.setSetting('auth_method', 'api_key')
            self.addon.setSetting('api_key', api_key)
            return 'api_key'

        return None

    def show_photo_info(self, photo) -> None:
        """Show detailed photo information dialog"""
        
        # Build info text (handle both dict and model objects)
        info_lines = []
        
        if hasattr(photo, 'title'):
            info_lines.append(f"Title: {photo.title}")
            info_lines.append(f"ID: {photo.id}")
        elif isinstance(photo, dict):
            info_lines.append(f"Title: {photo.get('title', 'Unknown')}")
            info_lines.append(f"ID: {photo.get('id', 'Unknown')}")
        
        # Add description
        description = None
        if hasattr(photo, 'description'):
            description = photo.description
        elif isinstance(photo, dict):
            description = photo.get('description')
        
        if description:
            info_lines.append(f"Description: {description}")

        # Add upload date
        if hasattr(photo, 'date_upload') and photo.date_upload:
            info_lines.append(f"Uploaded: {photo.date_upload.strftime('%Y-%m-%d %H:%M')}")
        elif isinstance(photo, dict) and photo.get('date_upload'):
            info_lines.append(f"Uploaded: {photo['date_upload']}")

        # Add owner
        owner_name = None
        if hasattr(photo, 'owner_name'):
            owner_name = photo.owner_name
        elif isinstance(photo, dict):
            owner_name = photo.get('owner_name')
        
        if owner_name:
            info_lines.append(f"Owner: {owner_name}")

        # Add tags
        tags = None
        if hasattr(photo, 'tags'):
            tags = photo.tags
        elif isinstance(photo, dict):
            tags = photo.get('tags', [])
            
        if tags:
            info_lines.append(f"Tags: {', '.join(tags)}")

        # Add views
        views = None
        if hasattr(photo, 'views'):
            views = photo.views
        elif isinstance(photo, dict):
            views = photo.get('views')
            
        if views:
            info_lines.append(f"Views: {views}")

        info_text = '\n'.join(info_lines)

        dialog = xbmcgui.Dialog()
        dialog.textviewer(
            heading="Photo Information",
            text=info_text
        )

    def show_search_dialog(self) -> Optional[Dict[str, Any]]:
        """Show enhanced search configuration dialog"""

        dialog = xbmcgui.Dialog()

        # Get search text
        search_text = dialog.input(
            heading="Search Photos",
            type=xbmcgui.INPUT_ALPHANUM
        )

        if not search_text:
            return None

        # Search options
        options = [
            "All Photos",
            "My Photos Only",
            "Specific User"
        ]

        search_scope = dialog.select(
            "Search Scope",
            options
        )

        search_config = {
            'text': search_text,
            'scope': ['all', 'mine', 'user'][search_scope] if search_scope >= 0 else 'all'
        }

        # If user search, get user ID
        if search_config['scope'] == 'user':
            user_id = dialog.input(
                heading="Enter User ID or Email",
                type=xbmcgui.INPUT_ALPHANUM
            )

            if user_id:
                search_config['user_id'] = user_id
            else:
                return None

        return search_config

    def show_progress_dialog(self, title: str, message: str = '') -> xbmcgui.DialogProgress:
        """Show progress dialog for long operations"""

        progress = xbmcgui.DialogProgress()
        progress.create(title, message)
        return progress

    def confirm_download(self, item_name: str, size_estimate: str = '') -> bool:
        """Confirm download operation"""

        dialog = xbmcgui.Dialog()

        message = f"Download {item_name}?"
        if size_estimate:
            message += f"\nEstimated size: {size_estimate}"

        return dialog.yesno(
            "Confirm Download",
            message
        )

    def show_error(self, title: str, message: str, details: str = '') -> None:
        """Show error dialog with optional details"""

        dialog = xbmcgui.Dialog()

        if details:
            # Show with details button
            if dialog.yesno(
                title,
                message,
                yeslabel="Show Details",
                nolabel="OK"
            ):
                dialog.textviewer(
                    heading="Error Details",
                    text=details
                )
        else:
            dialog.ok(title, message)
    
    def show_error_dialog(self, title: str, message: str, details: Optional[str] = None) -> None:
        """Show error dialog with optional details"""
        
        dialog = xbmcgui.Dialog()
        
        if details:
            # Show basic error first
            dialog.ok(title, message)
            
            # Offer to show details
            if dialog.yesno("Error Details", "Would you like to see detailed error information?"):
                dialog.textviewer("Error Details", details)
        else:
            dialog.ok(title, message)
    
    def show_progress_dialog(
        self,
        title: str,
        message: str = "",
        can_cancel: bool = True
    ) -> xbmcgui.DialogProgress:
        """Create and show a progress dialog"""
        
        progress = xbmcgui.DialogProgress()
        progress.create(title, message)
        
        return progress
    
    def show_busy_dialog(self) -> xbmcgui.DialogProgress:
        """Show busy dialog"""
        
        busy = xbmcgui.DialogProgress()
        busy.create("Flickr", "Loading...")
        
        return busy
    
    def show_info_dialog(self, title: str, info: Dict[str, Any]) -> None:
        """Show information dialog with key-value pairs"""
        
        info_lines = []
        
        for key, value in info.items():
            if value is not None and value != "":
                # Format key nicely
                formatted_key = key.replace('_', ' ').title()
                
                # Handle different value types
                if isinstance(value, (list, tuple)):
                    formatted_value = ", ".join(str(v) for v in value)
                elif isinstance(value, bool):
                    formatted_value = "Yes" if value else "No"
                else:
                    formatted_value = str(value)
                
                info_lines.append(f"{formatted_key}: {formatted_value}")
        
        info_text = "\\n".join(info_lines)
        
        dialog = xbmcgui.Dialog()
        dialog.textviewer(title, info_text)
    
    def show_multiselect_dialog(
        self,
        title: str,
        options: List[str],
        preselected: Optional[List[int]] = None
    ) -> Optional[List[int]]:
        """Show multi-select dialog"""
        
        dialog = xbmcgui.Dialog()
        
        selected = dialog.multiselect(
            title,
            options,
            preselect=preselected or []
        )
        
        return selected
    
    def show_numeric_dialog(
        self,
        title: str,
        default_value: Union[int, float] = 0,
        input_type: str = 'integer'
    ) -> Optional[Union[int, float]]:
        """Show numeric input dialog"""
        
        dialog = xbmcgui.Dialog()
        
        if input_type == 'integer':
            input_type_kodi = xbmcgui.INPUT_NUMERIC
        else:
            input_type_kodi = xbmcgui.INPUT_NUMERIC
        
        result = dialog.input(
            heading=title,
            defaultt=str(default_value),
            type=input_type_kodi
        )
        
        if result:
            try:
                if input_type == 'integer':
                    return int(result)
                else:
                    return float(result)
            except ValueError:
                pass
        
        return None
    
    def show_text_dialog(
        self,
        title: str,
        default_text: str = "",
        hidden: bool = False
    ) -> Optional[str]:
        """Show text input dialog"""
        
        dialog = xbmcgui.Dialog()
        
        input_type = xbmcgui.INPUT_PASSWORD if hidden else xbmcgui.INPUT_ALPHANUM
        
        result = dialog.input(
            heading=title,
            defaultt=default_text,
            type=input_type
        )
        
        return result if result else None
    
    def show_browse_dialog(
        self,
        browse_type: str,
        title: str,
        default_path: str = "",
        file_mask: str = ""
    ) -> Optional[str]:
        """Show file/folder browse dialog"""
        
        dialog = xbmcgui.Dialog()
        
        # Map browse types
        type_map = {
            'file': 1,           # ShowAndGetFile
            'files': 1,          # ShowAndGetFile (multiple)
            'folder': 0,         # ShowAndGetDirectory
            'image': 2,          # ShowAndGetImage
            'writable_folder': 3  # ShowAndGetWriteableDirectory
        }
        
        browse_type_code = type_map.get(browse_type, 0)
        
        result = dialog.browse(
            type=browse_type_code,
            heading=title,
            shares='files',
            mask=file_mask,
            useThumbs=browse_type in ['image', 'files'],
            treatAsFolder=browse_type == 'folder',
            defaultt=default_path
        )
        
        return result if result else None
    
    def show_notification(
        self,
        message: str,
        title: str = "Flickr Add-on",
        icon: str = "",
        time_ms: int = 3000,
        sound: bool = True
    ) -> None:
        """Show notification"""
        
        dialog = xbmcgui.Dialog()
        
        # Default to info icon if none specified
        if not icon:
            icon = xbmcgui.NOTIFICATION_INFO
        
        dialog.notification(
            heading=title,
            message=message,
            icon=icon,
            time=time_ms,
            sound=sound
        )
    
    def confirm_action(
        self,
        title: str,
        message: str,
        yes_label: str = "Yes",
        no_label: str = "No"
    ) -> bool:
        """Show confirmation dialog"""
        
        dialog = xbmcgui.Dialog()
        
        return dialog.yesno(
            title,
            message,
            yeslabel=yes_label,
            nolabel=no_label
        )
    
    def show_context_menu(self, options: List[str]) -> Optional[int]:
        """Show context menu"""
        
        dialog = xbmcgui.Dialog()
        
        selected = dialog.contextmenu(options)
        return selected if selected >= 0 else None


class FlickrNotifications:
    """Enhanced notification system"""

    def __init__(self, addon: xbmcaddon.Addon):
        self.addon = addon
        self.icon = addon.getAddonInfo('icon')

    def show_success(self, message: str, duration: int = 5000) -> None:
        """Show success notification"""

        xbmcgui.Dialog().notification(
            heading=self.addon.getAddonInfo('name'),
            message=message,
            icon=self.icon,
            time=duration,
            sound=False
        )

    def show_error(self, message: str, duration: int = 8000) -> None:
        """Show error notification"""

        xbmcgui.Dialog().notification(
            heading=self.addon.getAddonInfo('name'),
            message=message,
            icon=xbmcgui.NOTIFICATION_ERROR,
            time=duration,
            sound=True
        )

    def show_info(self, message: str, duration: int = 5000) -> None:
        """Show info notification"""

        xbmcgui.Dialog().notification(
            heading=self.addon.getAddonInfo('name'),
            message=message,
            icon=xbmcgui.NOTIFICATION_INFO,
            time=duration,
            sound=False
        )

    def show_warning(self, message: str, duration: int = 6000) -> None:
        """Show warning notification"""

        xbmcgui.Dialog().notification(
            heading=self.addon.getAddonInfo('name'),
            message=message,
            icon=xbmcgui.NOTIFICATION_WARNING,
            time=duration,
            sound=False
        )


class FlickrImageViewer:
    """Enhanced image viewer with zoom and pan capabilities"""

    def __init__(self, config):
        self.config = config

    def show_image(self, photo, photos: List = None) -> None:
        """Show image with enhanced viewer"""
        
        # For now, use Kodi's built-in image viewer
        import xbmc
        
        if hasattr(photo, 'get_display_url'):
            image_url = photo.get_display_url()
        elif isinstance(photo, dict):
            image_url = photo.get('url', '')
        else:
            return
        
        # Show the image using Kodi's built-in viewer
        xbmc.executebuiltin(f'ShowPicture({image_url})')

    def start_slideshow_from_photos(self, photos: List) -> None:
        """Start a slideshow from a list of photos"""
        
        import xbmc
        import json
        import tempfile
        import os
        
        # Create a temporary playlist
        playlist_items = []
        
        for photo in photos:
            if hasattr(photo, 'get_display_url'):
                url = photo.get_display_url()
                title = photo.title if hasattr(photo, 'title') else 'Photo'
            elif isinstance(photo, dict):
                url = photo.get('url', '')
                title = photo.get('title', 'Photo')
            else:
                continue
                
            playlist_items.append({
                'file': url,
                'title': title
            })
        
        if not playlist_items:
            return
        
        # Create temporary M3U playlist
        temp_dir = tempfile.gettempdir()
        playlist_path = os.path.join(temp_dir, 'flickr_slideshow.m3u')
        
        with open(playlist_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for item in playlist_items:
                f.write(f"#EXTINF:-1,{item['title']}\n")
                f.write(f"{item['file']}\n")
        
        # Start slideshow
        xbmc.executebuiltin(f'SlideShow({playlist_path})')


class FlickrMediaPlayer:
    """Enhanced media player for photos with additional features"""
    
    def __init__(self, config):
        self.config = config
    
    def play_photo(self, photo, playlist: List = None) -> None:
        """Play a photo with enhanced features"""
        
        # Create a ListItem for the photo
        list_item = xbmcgui.ListItem()
        
        if hasattr(photo, 'title'):
            list_item.setLabel(photo.title)
            
        if hasattr(photo, 'get_display_url'):
            url = photo.get_display_url()
        elif isinstance(photo, dict):
            url = photo.get('url', '')
        else:
            return
            
        # Set art
        list_item.setArt({
            'thumb': url,
            'poster': url,
            'fanart': url
        })
        
        # Set info
        if hasattr(photo, 'description') and photo.description:
            list_item.setInfo('pictures', {'plot': photo.description})
        
        # Play the image
        import xbmc
        player = xbmc.Player()
        
        if playlist:
            # Create playlist with all photos
            xbmc_playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)  # Using music playlist for images
            xbmc_playlist.clear()
            
            for p in playlist:
                item = xbmcgui.ListItem()
                if hasattr(p, 'title'):
                    item.setLabel(p.title)
                    
                if hasattr(p, 'get_display_url'):
                    p_url = p.get_display_url()
                elif isinstance(p, dict):
                    p_url = p.get('url', '')
                else:
                    continue
                    
                xbmc_playlist.add(p_url, item)
            
            player.play(xbmc_playlist)
        else:
            player.play(url, list_item)