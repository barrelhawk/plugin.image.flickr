# -*- coding: utf-8 -*-
"""
Flickr API Client
Modern HTTP client for Flickr API with OAuth 2.0 support
"""

import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlencode
from .auth import FlickrOAuth2Manager
from utils.http_client import HTTPClientManager
from cache.manager import CacheManager, APICache


class FlickrAPIClient:
    """Modern Flickr API client with OAuth 2.0 and API key support"""
    
    # Flickr API constants
    API_BASE_URL = "https://api.flickr.com/services"
    REST_ENDPOINT = "/rest"
    UPLOAD_ENDPOINT = "/upload"
    
    # Common method parameters
    FORMAT = 'json'
    NO_JSON_CALLBACK = '1'
    
    def __init__(self, client_id: str, client_secret: str, config, logger):
        """Initialize the API client"""
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.config = config
        self.logger = logger
        
        # Check if this is API key mode (for backwards compatibility)
        self._api_key_mode = not bool(client_secret)
        
        # Initialize auth manager (only for OAuth 2.0)
        if not self._api_key_mode:
            self.auth = FlickrOAuth2Manager(
                client_id=client_id,
                client_secret=client_secret,
                config=config,
                logger=logger
            )
        else:
            self.auth = None
            self.logger.info("API client initialized in API key mode")
        
        # HTTP client
        self.http_client = HTTPClientManager(config, logger)
        
        # Cache system
        cache_dir = None
        try:
            import os
            cache_dir = os.path.join(config.addon_profile, 'cache')
        except:
            pass  # Cache will work in memory only
        
        self.cache_manager = CacheManager(config, logger, cache_dir)
        self.api_cache = APICache(self.cache_manager)
    
    async def initialize(self) -> bool:
        """Initialize the API client"""
        
        try:
            # Initialize HTTP client
            success = await self.http_client.initialize()
            
            if not success:
                self.logger.error("Failed to initialize HTTP client")
                return False
            
            # Test connection with a simple API call
            test_result = await self.test_echo()
            if test_result.get('stat') != 'ok':
                self.logger.warning("API test call failed")
            
            self.logger.info("API client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API client: {e}", exc_info=True)
            return False
    
    async def close(self) -> None:
        """Close the API client"""
        
        if self.http_client:
            await self.http_client.close()
        
        if self.auth:
            await self.auth.close()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if self._api_key_mode:
            # In API key mode, we're always \"authenticated\" if we have a key
            return bool(self.client_id)
        elif self.auth:
            return self.auth.is_authenticated()
        else:
            return False
    
    def authenticate(self) -> bool:
        """Authenticate user with OAuth 2.0"""
        if self._api_key_mode:
            self.logger.info("Using API key authentication - no OAuth flow needed")
            return bool(self.client_id)
        elif self.auth:
            return self.auth.authenticate()
        else:
            self.logger.error("No authentication method available")
            return False
    
    def clear_authentication(self) -> None:
        """Clear authentication data"""
        if self.auth:
            self.auth.clear_authentication()
        elif self._api_key_mode:
            self.logger.info("API key mode - no stored authentication to clear")
    
    async def call_method(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        auth_required: bool = True,
        use_post: bool = False,
        use_cache: bool = True,
        cache_ttl: int = 300
    ) -> Dict[str, Any]:
        """Call Flickr API method"""
        
        # Check cache first (for GET requests)
        cache_key = None
        if use_cache and not use_post:
            cache_params = params.copy() if params else {}
            cache_params['method'] = method
            cached_result = self.api_cache.get_photos(method, cache_params)
            if cached_result:
                self.logger.debug(f"Cache hit for {method}")
                return cached_result
        
        # Prepare parameters
        api_params = {
            'method': method,
            'format': self.FORMAT,
            'nojsoncallback': self.NO_JSON_CALLBACK
        }
        
        if params:
            api_params.update(params)
        
        # Add authentication
        if auth_required:
            if self._api_key_mode:
                api_params['api_key'] = self.client_id
            elif self.auth and self.auth.is_authenticated():
                # OAuth 2.0 - will be handled in headers
                pass
            else:
                raise ValueError("Authentication required but not available")
        else:
            # For public methods, use API key if available
            if self.client_id:
                api_params['api_key'] = self.client_id
        
        # Make request
        try:
            if use_post:
                response = await self._post_request(self.REST_ENDPOINT, api_params, auth_required)
            else:
                response = await self._get_request(self.REST_ENDPOINT, api_params, auth_required)
            
            result = self._parse_response(response)
            
            # Cache successful results (for GET requests)
            if use_cache and not use_post and result.get('stat') == 'ok':
                cache_params = params.copy() if params else {}
                cache_params['method'] = method
                self.api_cache.set_photos(method, cache_params, result, cache_ttl)
            
            return result
            
        except Exception as e:
            self.logger.error(f"API call failed for {method}: {e}")
            return {'stat': 'fail', 'message': str(e)}
    
    async def _get_request(self, endpoint: str, params: Dict[str, Any], auth_required: bool = False) -> Any:
        """Make GET request to API"""
        
        headers = {}
        if auth_required and not self._api_key_mode and self.auth:
            headers.update(self.auth.get_auth_headers())
        
        response = await self.http_client.get(
            endpoint,
            params=params,
            headers=headers if headers else None
        )
        
        return response
    
    async def _post_request(self, endpoint: str, data: Dict[str, Any], auth_required: bool = False) -> Any:
        """Make POST request to API"""
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        if auth_required and not self._api_key_mode and self.auth:
            headers.update(self.auth.get_auth_headers())
        
        response = await self.http_client.post(
            endpoint,
            data=data,
            headers=headers
        )
        
        return response
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """Parse API response"""
        
        try:
            if response.status_code != 200:
                return {
                    'stat': 'fail',
                    'code': response.status_code,
                    'message': f'HTTP {response.status_code}: {response.reason_phrase}'
                }
            
            # Parse JSON response
            data = response.json()
            
            # Check for API error
            if data.get('stat') == 'fail':
                error_code = data.get('code')
                error_msg = data.get('message', 'Unknown error')
                
                # Handle authentication errors
                if self.auth and error_code in ['98', '99', '100', '108']:
                    if self.auth.handle_auth_error(data):
                        # Auth was refreshed, should retry the request
                        return {'stat': 'auth_refreshed'}
                
                self.logger.warning(f"API error {error_code}: {error_msg}")
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response: {e}")
            return {
                'stat': 'fail',
                'message': f'Invalid JSON response: {e}'
            }
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            return {
                'stat': 'fail',
                'message': str(e)
            }
    
    # Synchronous wrappers for common operations
    def call_method_sync(self, method: str, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for call_method"""
        try:
            return asyncio.run(self.call_method(method, **kwargs))
        except Exception as e:
            self.logger.error(f"Sync API call failed: {e}")
            return {'stat': 'fail', 'message': str(e)}
    
    # API method implementations
    async def test_echo(self, echo_text: str = "test") -> Dict[str, Any]:
        """Test API connectivity"""
        return await self.call_method(
            'flickr.test.echo',
            params={'echo_text': echo_text},
            auth_required=False
        )
    
    async def test_login(self) -> Dict[str, Any]:
        """Test authentication"""
        return await self.call_method(
            'flickr.test.login',
            auth_required=True
        )
    
    async def get_photostream(
        self,
        user_id: str = 'me',
        page: int = 1,
        per_page: int = 50,
        extras: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's photostream"""
        
        params = {
            'user_id': user_id,
            'page': str(page),
            'per_page': str(per_page)
        }
        
        if extras:
            params['extras'] = extras
        
        return await self.call_method(
            'flickr.people.getPhotos',
            params=params,
            auth_required=(user_id == 'me')
        )
    
    async def get_photosets(self, user_id: str = 'me', page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get user's photosets"""
        
        params = {
            'user_id': user_id,
            'page': str(page),
            'per_page': str(per_page)
        }
        
        return await self.call_method(
            'flickr.photosets.getList',
            params=params,
            auth_required=(user_id == 'me')
        )
    
    async def get_photoset_photos(
        self,
        photoset_id: str,
        page: int = 1,
        per_page: int = 50,
        extras: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get photos from a photoset"""
        
        params = {
            'photoset_id': photoset_id,
            'page': str(page),
            'per_page': str(per_page)
        }
        
        if extras:
            params['extras'] = extras
        
        return await self.call_method(
            'flickr.photosets.getPhotos',
            params=params
        )
    
    async def search_photos(
        self,
        text: Optional[str] = None,
        tags: Optional[str] = None,
        user_id: Optional[str] = None,
        sort: str = 'relevance',
        page: int = 1,
        per_page: int = 50,
        extras: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Search for photos"""
        
        params = {
            'sort': sort,
            'page': str(page),
            'per_page': str(per_page)
        }
        
        if text:
            params['text'] = text
        if tags:
            params['tags'] = tags
        if user_id:
            params['user_id'] = user_id
        if extras:
            params['extras'] = extras
        
        # Add any additional search parameters
        params.update(kwargs)
        
        return await self.call_method(
            'flickr.photos.search',
            params=params,
            auth_required=False
        )
    
    async def get_favorites(
        self,
        user_id: str = 'me',
        page: int = 1,
        per_page: int = 50,
        extras: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's favorites"""
        
        params = {
            'user_id': user_id,
            'page': str(page),
            'per_page': str(per_page)
        }
        
        if extras:
            params['extras'] = extras
        
        return await self.call_method(
            'flickr.favorites.getList',
            params=params,
            auth_required=(user_id == 'me')
        )
    
    async def get_contacts(
        self,
        filter: str = 'all',
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Get user's contacts"""
        
        params = {
            'filter': filter,
            'page': str(page),
            'per_page': str(per_page)
        }
        
        return await self.call_method(
            'flickr.contacts.getList',
            params=params,
            auth_required=True
        )
    
    async def get_photo_info(self, photo_id: str) -> Dict[str, Any]:
        """Get photo information"""
        
        params = {'photo_id': photo_id}
        
        return await self.call_method(
            'flickr.photos.getInfo',
            params=params,
            auth_required=False
        )
    
    async def get_photo_sizes(self, photo_id: str) -> Dict[str, Any]:
        """Get available sizes for a photo"""
        
        params = {'photo_id': photo_id}
        
        return await self.call_method(
            'flickr.photos.getSizes',
            params=params,
            auth_required=False
        )
    
    def get_photo_url(
        self,
        photo: Dict[str, Any],
        size: str = 'medium'
    ) -> str:
        """Get photo URL for specified size"""
        
        # Photo URL construction based on Flickr's URL format
        # https://www.flickr.com/services/api/misc.urls.html
        
        farm = photo.get('farm', '1')
        server = photo.get('server', '1')
        photo_id = photo.get('id', '0')
        secret = photo.get('secret', 'default')
        
        # Size suffixes
        size_map = {
            'square': '_s',      # 75x75
            'thumbnail': '_t',   # 100 on longest side
            'small': '_m',       # 240 on longest side
            'medium': '',        # 500 on longest side (default)
            'medium_640': '_z',  # 640 on longest side
            'large': '_b',       # 1024 on longest side
            'original': '_o'     # Original size
        }
        
        size_suffix = size_map.get(size, '')
        
        return f"https://farm{farm}.staticflickr.com/{server}/{photo_id}_{secret}{size_suffix}.jpg"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        
        stats = {
            'client_id': self.client_id[:10] + '...' if self.client_id else None,
            'api_key_mode': self._api_key_mode,
            'authenticated': self.is_authenticated(),
            'http_client': self.http_client.get_stats() if self.http_client else None
        }
        
        if self.auth:
            stats['auth_method'] = 'oauth2'
        
        return stats