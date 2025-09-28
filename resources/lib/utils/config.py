# -*- coding: utf-8 -*-
"""
Configuration management for Flickr Add-on
Handles addon settings with proper type conversion and validation
"""

import xbmcaddon
from typing import Union, Optional, Any, Dict
from enum import Enum
import json


class SettingType(Enum):
    """Setting type enumeration"""
    STRING = "string"
    BOOLEAN = "bool"
    INTEGER = "int"
    FLOAT = "float"
    LIST = "list"


class AddonConfig:
    """Modern configuration management for Kodi addon"""

    # Default configuration values
    DEFAULTS = {
        'auth_method': 'oauth2',
        'client_id': '',
        'client_secret': '',
        'api_key': '',
        'access_token': '',
        'refresh_token': '',
        'thumb_size': 'small',
        'display_size': 'large',
        'items_per_page': 50,
        'cache_enabled': True,
        'cache_duration': 3600,
        'auto_refresh_tokens': True,
        'slideshow_interval': 5,
        'slideshow_random': False,
        'slideshow_transition': 'fade',
        'slideshow_show_info': True,
        'enable_debug_logging': False,
        'log_level': 'info',
        'concurrent_downloads': 5,
        'request_timeout': 30,
        'retry_attempts': 3,
        'enable_download': False,
        'download_path': 'special://home/Downloads/Flickr',
        'download_quality': 'large',
        'enable_favorites': True,
        'sync_flickr_favorites': False,
        'enable_fanart': True,
        'show_photo_info': True,
        'auto_next_page': True
    }

    # Setting type mapping
    TYPES = {
        'auth_method': SettingType.STRING,
        'client_id': SettingType.STRING,
        'client_secret': SettingType.STRING,
        'api_key': SettingType.STRING,
        'access_token': SettingType.STRING,
        'refresh_token': SettingType.STRING,
        'thumb_size': SettingType.STRING,
        'display_size': SettingType.STRING,
        'items_per_page': SettingType.INTEGER,
        'cache_enabled': SettingType.BOOLEAN,
        'cache_duration': SettingType.INTEGER,
        'auto_refresh_tokens': SettingType.BOOLEAN,
        'slideshow_interval': SettingType.INTEGER,
        'slideshow_random': SettingType.BOOLEAN,
        'slideshow_transition': SettingType.STRING,
        'slideshow_show_info': SettingType.BOOLEAN,
        'enable_debug_logging': SettingType.BOOLEAN,
        'log_level': SettingType.STRING,
        'concurrent_downloads': SettingType.INTEGER,
        'request_timeout': SettingType.INTEGER,
        'retry_attempts': SettingType.INTEGER,
        'enable_download': SettingType.BOOLEAN,
        'download_path': SettingType.STRING,
        'download_quality': SettingType.STRING,
        'enable_favorites': SettingType.BOOLEAN,
        'sync_flickr_favorites': SettingType.BOOLEAN,
        'enable_fanart': SettingType.BOOLEAN,
        'show_photo_info': SettingType.BOOLEAN,
        'auto_next_page': SettingType.BOOLEAN
    }

    def __init__(self, addon: xbmcaddon.Addon):
        """Initialize configuration manager"""
        self.addon = addon
        self.addon_id = addon.getAddonInfo('id')
        self.addon_name = addon.getAddonInfo('name')
        self.addon_version = addon.getAddonInfo('version')
        self.addon_path = addon.getAddonInfo('path')
        self.addon_profile = addon.getAddonInfo('profile')

    def get(self, key: str, default: Any = None) -> str:
        """Get a setting value as string"""
        
        try:
            value = self.addon.getSetting(key)
            if value == '' and key in self.DEFAULTS:
                return str(self.DEFAULTS[key])
            return value if value != '' else (str(default) if default is not None else '')
        except Exception:
            if key in self.DEFAULTS:
                return str(self.DEFAULTS[key])
            return str(default) if default is not None else ''

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a setting value as boolean"""
        
        try:
            value = self.get(key, str(default))
            
            # Handle different boolean representations
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return bool(value)
                
        except Exception:
            if key in self.DEFAULTS:
                return bool(self.DEFAULTS[key])
            return default

    def get_int(self, key: str, default: int = 0) -> int:
        """Get a setting value as integer"""
        
        try:
            value = self.get(key, str(default))
            return int(value)
        except (ValueError, TypeError):
            if key in self.DEFAULTS:
                return int(self.DEFAULTS[key])
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a setting value as float"""
        
        try:
            value = self.get(key, str(default))
            return float(value)
        except (ValueError, TypeError):
            if key in self.DEFAULTS:
                return float(self.DEFAULTS[key])
            return default

    def get_list(self, key: str, default: list = None) -> list:
        """Get a setting value as list (from JSON string)"""
        
        if default is None:
            default = []
        
        try:
            value = self.get(key)
            if not value:
                if key in self.DEFAULTS:
                    return list(self.DEFAULTS[key])
                return default
            
            # Try to parse as JSON
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            if key in self.DEFAULTS:
                return list(self.DEFAULTS[key])
            return default

    def set(self, key: str, value: Any) -> bool:
        """Set a setting value"""
        
        try:
            # Convert value to appropriate string representation
            if isinstance(value, bool):
                str_value = 'true' if value else 'false'
            elif isinstance(value, (list, dict)):
                str_value = json.dumps(value)
            else:
                str_value = str(value)
            
            self.addon.setSetting(key, str_value)
            return True
            
        except Exception:
            return False

    def set_bool(self, key: str, value: bool) -> bool:
        """Set a boolean setting"""
        return self.set(key, value)

    def set_int(self, key: str, value: int) -> bool:
        """Set an integer setting"""
        return self.set(key, value)

    def set_float(self, key: str, value: float) -> bool:
        """Set a float setting"""
        return self.set(key, value)

    def set_list(self, key: str, value: list) -> bool:
        """Set a list setting (as JSON string)"""
        return self.set(key, value)

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values"""
        
        for key, default_value in self.DEFAULTS.items():
            self.set(key, default_value)

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary with proper types"""
        
        settings = {}
        
        for key, setting_type in self.TYPES.items():
            if setting_type == SettingType.BOOLEAN:
                settings[key] = self.get_bool(key)
            elif setting_type == SettingType.INTEGER:
                settings[key] = self.get_int(key)
            elif setting_type == SettingType.FLOAT:
                settings[key] = self.get_float(key)
            elif setting_type == SettingType.LIST:
                settings[key] = self.get_list(key)
            else:  # STRING
                settings[key] = self.get(key)
        
        return settings

    def is_configured(self) -> bool:
        """Check if addon is properly configured"""
        
        auth_method = self.get('auth_method', 'oauth2')
        
        if auth_method == 'oauth2':
            return bool(self.get('client_id'))
        elif auth_method == 'api_key':
            return bool(self.get('api_key'))
        
        return False

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        
        auth_method = self.get('auth_method', 'oauth2')
        
        if auth_method == 'oauth2':
            return bool(self.get('access_token'))
        elif auth_method == 'api_key':
            return bool(self.get('api_key'))
        
        return False

    def clear_authentication(self) -> None:
        """Clear authentication data"""
        
        self.set('access_token', '')
        self.set('refresh_token', '')

    def get_cache_settings(self) -> Dict[str, Any]:
        """Get cache-related settings"""
        
        return {
            'enabled': self.get_bool('cache_enabled', True),
            'duration': self.get_int('cache_duration', 3600),
            'path': self.addon_profile
        }

    def get_display_settings(self) -> Dict[str, Any]:
        """Get display-related settings"""
        
        return {
            'thumb_size': self.get('thumb_size', 'small'),
            'display_size': self.get('display_size', 'large'),
            'items_per_page': self.get_int('items_per_page', 50),
            'enable_fanart': self.get_bool('enable_fanart', True),
            'show_photo_info': self.get_bool('show_photo_info', True),
            'auto_next_page': self.get_bool('auto_next_page', True)
        }

    def get_slideshow_settings(self) -> Dict[str, Any]:
        """Get slideshow-related settings"""
        
        return {
            'interval': self.get_int('slideshow_interval', 5),
            'random': self.get_bool('slideshow_random', False),
            'transition': self.get('slideshow_transition', 'fade'),
            'show_info': self.get_bool('slideshow_show_info', True)
        }

    def get_network_settings(self) -> Dict[str, Any]:
        """Get network-related settings"""
        
        return {
            'concurrent_downloads': self.get_int('concurrent_downloads', 5),
            'request_timeout': self.get_int('request_timeout', 30),
            'retry_attempts': self.get_int('retry_attempts', 3)
        }

    def __str__(self) -> str:
        """String representation of configuration"""
        
        return (
            f"FlickrConfig("
            f"addon_id={self.addon_id}, "
            f"version={self.addon_version}, "
            f"configured={self.is_configured()}, "
            f"authenticated={self.is_authenticated()}"
            f")"
        )