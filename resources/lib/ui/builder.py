# -*- coding: utf-8 -*-
"""
UI Builder for Flickr Add-on
Handles building lists, menus, and navigation items with modern Kodi features
"""

from typing import Optional, Dict, Any, List
import urllib.parse
import xbmcgui
import xbmcplugin
from api.models import FlickrPhoto, FlickrPhotoset
from utils.config import AddonConfig


class FlickrUIBuilder:
    """Builder for creating Kodi UI elements"""
    
    def __init__(self, addon_handle: int, config: AddonConfig):
        """Initialize modern UI builder with enhanced features"""
        
        self.addon_handle = addon_handle
        self.config = config
        self.items: List[tuple] = []
        
        # View settings
        self.content_type = 'files'
        self.sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED]
        self.cache_to_disk = True
        
        # Default thumbnails
        self.default_folder_icon = "DefaultFolder.png"
        self.default_photo_icon = "DefaultPicture.png"
        self.default_action_icon = "DefaultProgram.png"
    
    def set_content_type(self, content_type: str) -> 'FlickrUIBuilder':
        """Set content type for the view"""
        self.content_type = content_type
        return self
    
    def set_sort_methods(self, sort_methods: List[int]) -> 'FlickrUIBuilder':
        """Set allowed sort methods"""
        self.sort_methods = sort_methods
        return self
    
    def set_cache_to_disk(self, cache: bool) -> 'FlickrUIBuilder':
        """Set cache to disk option"""
        self.cache_to_disk = cache
        return self
    
    def add_folder(
        self,
        title: str,
        url: str,
        thumbnail: Optional[str] = None,
        fanart: Optional[str] = None,
        description: Optional[str] = None,
        info_labels: Optional[Dict[str, Any]] = None,
        context_menu: Optional[List[tuple]] = None,
        properties: Optional[Dict[str, str]] = None
    ) -> 'FlickrUIBuilder':
        """Add a folder item to the list"""
        
        # Create list item
        list_item = xbmcgui.ListItem(label=title)
        
        # Set thumbnail
        if thumbnail:
            list_item.setArt({
                'thumb': thumbnail,
                'icon': thumbnail,
                'poster': thumbnail
            })
        else:
            list_item.setArt({'thumb': self.default_folder_icon})
        
        # Set fanart
        if fanart:
            list_item.setArt({'fanart': fanart})
        
        # Set info labels
        if info_labels:
            list_item.setInfo('pictures', info_labels)
        elif description:
            list_item.setInfo('pictures', {'plot': description})
        
        # Set context menu
        if context_menu:
            list_item.addContextMenuItems(context_menu)
        
        # Set properties
        if properties:
            for key, value in properties.items():
                list_item.setProperty(key, value)
        
        # Add to items list
        self.items.append((url, list_item, True))
        return self
    
    def add_photo(
        self,
        title: str,
        url: str,
        thumbnail: Optional[str] = None,
        fanart: Optional[str] = None,
        info_labels: Optional[Dict[str, Any]] = None,
        context_menu: Optional[List[tuple]] = None,
        properties: Optional[Dict[str, str]] = None,
        is_playable: bool = False
    ) -> 'FlickrUIBuilder':
        """Add a photo item to the list"""
        
        # Create list item
        list_item = xbmcgui.ListItem(label=title)
        
        # Set thumbnail
        if thumbnail:
            list_item.setArt({
                'thumb': thumbnail,
                'icon': thumbnail,
                'poster': thumbnail
            })
        else:
            list_item.setArt({'thumb': self.default_photo_icon})
        
        # Set fanart
        if fanart:
            list_item.setArt({'fanart': fanart})
        
        # Set info labels
        if info_labels:
            list_item.setInfo('pictures', info_labels)
        
        # Set context menu
        if context_menu:
            list_item.addContextMenuItems(context_menu)
        
        # Set properties
        if properties:
            for key, value in properties.items():
                list_item.setProperty(key, value)
        
        # Set playable if needed
        if is_playable:
            list_item.setProperty('IsPlayable', 'true')
        
        # Add to items list
        self.items.append((url, list_item, False))
        return self
    
    def add_photo_model(self, photo: FlickrPhoto, context_menu: Optional[List] = None) -> 'FlickrUIBuilder':
        """Add a photo using the FlickrPhoto model with modern ListItem properties"""

        # Create ListItem with comprehensive info
        list_item = xbmcgui.ListItem(label=photo.title)

        # Set modern art properties
        art_dict = {
            'thumb': photo.get_thumbnail_url(),
            'poster': photo.get_display_url(),
            'fanart': photo.get_display_url(),
            'landscape': photo.get_display_url()
        }
        list_item.setArt(art_dict)

        # Set detailed info
        info_dict = {
            'mediatype': 'picture',
            'title': photo.title,
            'plot': photo.description or f"Flickr photo: {photo.title}",
            'plotoutline': photo.description or photo.title,
            'date': photo.date_upload.strftime('%d.%m.%Y') if photo.date_upload else '',
            'dateadded': photo.date_upload.isoformat() if photo.date_upload else '',
            'picturepath': photo.get_display_url()
        }

        # Add photographer info if available
        if photo.owner_name:
            info_dict['director'] = photo.owner_name  # Using 'director' field for photographer

        # Add tags if available
        if photo.tags:
            info_dict['tag'] = photo.tags

        # Add view count
        if photo.views:
            info_dict['playcount'] = photo.views

        list_item.setInfo('pictures', info_dict)

        # Set properties for enhanced display
        list_item.setProperty('IsPlayable', 'false')
        list_item.setProperty('FlickrID', photo.id)
        list_item.setProperty('FlickrURL', photo.get_flickr_url())

        # Add context menu if provided
        if context_menu:
            list_item.addContextMenuItems(context_menu)

        # Create URL for photo display
        url = self._build_photo_url(photo)

        self.items.append((url, list_item, False))  # False = not a folder
        return self

    def add_photoset_model(self, photoset: FlickrPhotoset, context_menu: Optional[List] = None) -> 'FlickrUIBuilder':
        """Add a photoset using the FlickrPhotoset model with modern properties"""

        list_item = xbmcgui.ListItem(label=photoset.title)

        # Set folder art
        art_dict = {
            'thumb': photoset.get_thumbnail_url(),
            'poster': photoset.get_thumbnail_url(),
            'fanart': photoset.get_thumbnail_url(),
            'folder': photoset.get_thumbnail_url()
        }
        list_item.setArt(art_dict)

        # Set folder info
        info_dict = {
            'mediatype': 'set',
            'title': photoset.title,
            'plot': photoset.description or f"Photoset with {photoset.photos} photos",
            'plotoutline': f"{photoset.photos} photos",
            'count': photoset.photos,
            'size': photoset.photos
        }
        list_item.setInfo('pictures', info_dict)

        # Set folder properties
        list_item.setProperty('IsPlayable', 'false')
        list_item.setProperty('FlickrPhotosetID', photoset.id)
        list_item.setProperty('PhotoCount', str(photoset.photos))

        # Add context menu
        if context_menu:
            list_item.addContextMenuItems(context_menu)

        # Create URL for photoset browsing
        url = self._build_photoset_url(photoset)

        self.items.append((url, list_item, True))  # True = is a folder
        return self

    def _build_photo_url(self, photo: FlickrPhoto) -> str:
        """Build URL for photo display"""
        
        params = {
            'action': 'show_photo',
            'photo_id': photo.id,
            'title': photo.title,
            'url': photo.get_display_url()
        }

        return f"plugin://plugin.image.flickr/?{urllib.parse.urlencode(params)}"

    def _build_photoset_url(self, photoset: FlickrPhotoset) -> str:
        """Build URL for photoset browsing"""
        
        params = {
            'action': 'browse_photoset',
            'photoset_id': photoset.id,
            'title': photoset.title
        }

        return f"plugin://plugin.image.flickr/?{urllib.parse.urlencode(params)}"

    def add_action_item(
        self,
        title: str,
        url: str,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        context_menu: Optional[List[tuple]] = None
    ) -> 'FlickrUIBuilder':
        """Add an action item (non-folder, non-photo) to the list"""
        
        # Create list item
        list_item = xbmcgui.ListItem(label=title)
        
        # Set icon
        if icon:
            list_item.setArt({
                'thumb': icon,
                'icon': icon
            })
        else:
            list_item.setArt({'thumb': self.default_action_icon})
        
        # Set description
        if description:
            list_item.setInfo('pictures', {'plot': description})
        
        # Set context menu
        if context_menu:
            list_item.addContextMenuItems(context_menu)
        
        # Add to items list
        self.items.append((url, list_item, False))
        return self
    
    def add_separator(self, title: str = "---") -> 'FlickrUIBuilder':
        """Add a visual separator"""
        
        list_item = xbmcgui.ListItem(label=title)
        list_item.setProperty('IsPlayable', 'false')
        
        # Use empty URL for separator
        self.items.append(("", list_item, False))
        return self
    
    def add_back_item(self, url: str, title: str = ".. Back") -> 'FlickrUIBuilder':
        """Add a back navigation item"""
        
        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'thumb': 'DefaultFolderBack.png'})
        
        self.items.append((url, list_item, True))
        return self
    
    def build_photo_context_menu(
        self,
        photo_id: str,
        photo_url: str,
        photo_title: str,
        base_url: str
    ) -> List[tuple]:
        """Build context menu for a photo item"""
        
        context_menu = []
        
        # View photo info
        info_url = f"{base_url}?action=photo_info&photo_id={urllib.parse.quote(photo_id)}"
        context_menu.append(("View Info", f"RunPlugin({info_url})"))
        
        # Add to favorites (if authenticated)
        if self.config.is_authenticated():
            fav_url = f"{base_url}?action=add_favorite&photo_id={urllib.parse.quote(photo_id)}"
            context_menu.append(("Add to Favorites", f"RunPlugin({fav_url})"))
        
        # Download photo (if enabled)
        if self.config.get_bool('enable_download'):
            download_url = f"{base_url}?action=download&url={urllib.parse.quote(photo_url)}&title={urllib.parse.quote(photo_title)}"
            context_menu.append(("Download", f"RunPlugin({download_url})"))
        
        # Set as wallpaper
        wallpaper_url = f"{base_url}?action=set_wallpaper&url={urllib.parse.quote(photo_url)}"
        context_menu.append(("Set as Wallpaper", f"RunPlugin({wallpaper_url})"))
        
        # Share
        share_url = f"{base_url}?action=share&photo_id={urllib.parse.quote(photo_id)}&title={urllib.parse.quote(photo_title)}"
        context_menu.append(("Share", f"RunPlugin({share_url})"))
        
        return context_menu
    
    def build_photoset_context_menu(
        self,
        photoset_id: str,
        photoset_title: str,
        base_url: str
    ) -> List[tuple]:
        """Build context menu for a photoset item"""
        
        context_menu = []
        
        # View photoset info
        info_url = f"{base_url}?action=photoset_info&photoset_id={urllib.parse.quote(photoset_id)}"
        context_menu.append(("View Info", f"RunPlugin({info_url})"))
        
        # Download photoset (if enabled)
        if self.config.get_bool('enable_download'):
            download_url = f"{base_url}?action=download_photoset&photoset_id={urllib.parse.quote(photoset_id)}&title={urllib.parse.quote(photoset_title)}"
            context_menu.append(("Download Photoset", f"RunPlugin({download_url})"))
        
        # Start slideshow
        slideshow_url = f"{base_url}?action=slideshow&photoset_id={urllib.parse.quote(photoset_id)}"
        context_menu.append(("Start Slideshow", f"RunPlugin({slideshow_url})"))
        
        return context_menu
    
    def build_user_context_menu(
        self,
        user_id: str,
        username: str,
        base_url: str
    ) -> List[tuple]:
        """Build context menu for a user/contact item"""
        
        context_menu = []
        
        # View user's photostream
        stream_url = f"{base_url}?action=user_photostream&user_id={urllib.parse.quote(user_id)}"
        context_menu.append(("View Photostream", f"Container.Update({stream_url})"))
        
        # View user's photosets
        sets_url = f"{base_url}?action=user_photosets&user_id={urllib.parse.quote(user_id)}"
        context_menu.append(("View Photosets", f"Container.Update({sets_url})"))
        
        # View user's favorites
        favs_url = f"{base_url}?action=user_favorites&user_id={urllib.parse.quote(user_id)}"
        context_menu.append(("View Favorites", f"Container.Update({favs_url})"))
        
        return context_menu
    
    def set_photo_info_labels(
        self,
        title: str,
        description: Optional[str] = None,
        date_taken: Optional[str] = None,
        username: Optional[str] = None,
        views: Optional[int] = None,
        size: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create info labels for a photo"""
        
        info_labels = {
            'title': title,
            'originaltitle': title
        }
        
        if description:
            info_labels['plot'] = description
            info_labels['plotoutline'] = description[:200] + "..." if len(description) > 200 else description
        
        if date_taken:
            info_labels['dateadded'] = date_taken
            info_labels['date'] = date_taken
        
        if username:
            info_labels['studio'] = username
            info_labels['director'] = username
        
        if views is not None:
            info_labels['playcount'] = views
        
        if size:
            info_labels['size'] = size
        
        if tags:
            info_labels['tag'] = tags
            info_labels['genre'] = ", ".join(tags[:5])  # Limit to first 5 tags
        
        return info_labels
    
    def finalize(self, succeeded: bool = True, update_listing: bool = False) -> None:
        """Finalize the directory listing"""
        
        # Set content type
        xbmcplugin.setContent(self.addon_handle, self.content_type)
        
        # Add sort methods
        for sort_method in self.sort_methods:
            xbmcplugin.addSortMethod(self.addon_handle, sort_method)
        
        # Add all items to the directory
        if self.items:
            xbmcplugin.addDirectoryItems(
                self.addon_handle, 
                self.items, 
                len(self.items)
            )
        
        # End directory
        xbmcplugin.endOfDirectory(
            self.addon_handle,
            succeeded=succeeded,
            updateListing=update_listing,
            cacheToDisc=self.cache_to_disk
        )
    
    def clear(self) -> 'FlickrUIBuilder':
        """Clear all items"""
        self.items.clear()
        return self


class FlickrViewModes:
    """Predefined view modes for different content types"""
    
    # Content types
    CONTENT_FILES = 'files'
    CONTENT_IMAGES = 'images'
    CONTENT_ALBUMS = 'albums'
    
    # Sort methods for photos
    PHOTO_SORT_METHODS = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_LABEL,
        xbmcplugin.SORT_METHOD_DATE,
        xbmcplugin.SORT_METHOD_SIZE
    ]
    
    # Sort methods for albums/photosets
    ALBUM_SORT_METHODS = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_LABEL,
        xbmcplugin.SORT_METHOD_DATE
    ]
    
    # Sort methods for general folders
    FOLDER_SORT_METHODS = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_LABEL
    ]
    
    @staticmethod
    def get_photo_view_settings() -> Dict[str, Any]:
        """Get settings for photo view"""
        return {
            'content_type': FlickrViewModes.CONTENT_IMAGES,
            'sort_methods': FlickrViewModes.PHOTO_SORT_METHODS,
            'cache_to_disk': True
        }
    
    @staticmethod
    def get_album_view_settings() -> Dict[str, Any]:
        """Get settings for album view"""
        return {
            'content_type': FlickrViewModes.CONTENT_ALBUMS,
            'sort_methods': FlickrViewModes.ALBUM_SORT_METHODS,
            'cache_to_disk': True
        }
    
    @staticmethod
    def get_folder_view_settings() -> Dict[str, Any]:
        """Get settings for folder view"""
        return {
            'content_type': FlickrViewModes.CONTENT_FILES,
            'sort_methods': FlickrViewModes.FOLDER_SORT_METHODS,
            'cache_to_disk': False
        }


class FlickrContextMenu:
    """Context menu builder for Flickr items"""

    def __init__(self, config: AddonConfig):
        self.config = config

    def get_photo_context_menu(self, photo: FlickrPhoto) -> List[tuple]:
        """Get context menu for a photo"""

        menu_items = []

        # Add to favorites
        menu_items.append((
            'Add to Favorites',
            f'RunPlugin(plugin://plugin.image.flickr/?action=add_favorite&photo_id={photo.id})'
        ))

        # Download photo
        if self.config.get_bool('enable_download', False):
            menu_items.append((
                'Download Photo',
                f'RunPlugin(plugin://plugin.image.flickr/?action=download&photo_id={photo.id})'
            ))

        # View on Flickr
        menu_items.append((
            'View on Flickr',
            f'RunPlugin(plugin://plugin.image.flickr/?action=open_url&url={photo.get_flickr_url()})'
        ))

        # Photo info
        menu_items.append((
            'Photo Information',
            f'RunPlugin(plugin://plugin.image.flickr/?action=show_info&photo_id={photo.id})'
        ))

        return menu_items

    def get_photoset_context_menu(self, photoset: FlickrPhotoset) -> List[tuple]:
        """Get context menu for a photoset"""

        menu_items = []

        # Start slideshow
        menu_items.append((
            'Start Slideshow',
            f'RunPlugin(plugin://plugin.image.flickr/?action=slideshow&photoset_id={photoset.id})'
        ))

        # Download all
        if self.config.get_bool('enable_download', False):
            menu_items.append((
                'Download All Photos',
                f'RunPlugin(plugin://plugin.image.flickr/?action=download_photoset&photoset_id={photoset.id})'
            ))

        # Refresh
        menu_items.append((
            'Refresh Photoset',
            f'RunPlugin(plugin://plugin.image.flickr/?action=refresh_cache&photoset_id={photoset.id})'
        ))

        return menu_items


class FlickrSlideshow:
    """Enhanced slideshow functionality"""

    def __init__(self, config: AddonConfig):
        self.config = config

    def create_slideshow_playlist(self, photos: List[FlickrPhoto]) -> str:
        """Create a slideshow playlist file"""

        import json
        import tempfile
        
        # Create temporary playlist
        playlist_data = {
            'version': '1.0',
            'type': 'flickr_slideshow',
            'photos': []
        }

        for photo in photos:
            photo_entry = {
                'id': photo.id,
                'title': photo.title,
                'url': photo.get_display_url(),
                'duration': self.config.get_int('slideshow_duration', 5),
                'description': photo.description or ''
            }
            playlist_data['photos'].append(photo_entry)

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(playlist_data, temp_file, indent=2)
        temp_file.close()

        return temp_file.name

    def start_slideshow(self, photos: List[FlickrPhoto]) -> None:
        """Start slideshow with enhanced features"""

        import xbmc

        # Create playlist
        playlist_file = self.create_slideshow_playlist(photos)

        # Configure slideshow settings
        slideshow_settings = {
            'randomize': self.config.get_bool('slideshow_random', False),
            'duration': self.config.get_int('slideshow_duration', 5),
            'transition': self.config.get('slideshow_transition', 'fade'),
            'show_info': self.config.get_bool('slideshow_show_info', True)
        }

        # Start Kodi slideshow
        xbmc.executebuiltin(f'SlideShow({playlist_file})')

        # Apply slideshow settings via JSON-RPC if needed
        self._configure_slideshow_settings(slideshow_settings)

    def _configure_slideshow_settings(self, settings: Dict[str, Any]) -> None:
        """Configure slideshow settings via JSON-RPC"""

        import xbmc

        # Set slideshow duration
        if 'duration' in settings:
            xbmc.executebuiltin(f'SetProperty(slideshow.duration,{settings["duration"]})')

        # Set randomize
        if 'randomize' in settings:
            xbmc.executebuiltin(f'SetProperty(slideshow.random,{str(settings["randomize"]).lower()})')