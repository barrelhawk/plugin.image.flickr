# -*- coding: utf-8 -*-
"""
HTTP Client Manager for Flickr Add-on - Kodi Compatible
Provides HTTP client with timeout, retry, and error handling using standard libraries
"""

import time
import logging
import json
import gzip
from io import BytesIO
from typing import Dict, Any, Optional, Union, Tuple, List
from urllib.parse import urljoin, urlparse, urlencode
from urllib.request import Request, urlopen, build_opener, install_opener, HTTPSHandler, HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler
from urllib.error import URLError, HTTPError
import ssl
import http.client


class Response:
    """Simple response object to mimic requests.Response"""
    
    def __init__(self, status_code: int, headers: Dict, content: bytes, url: str):
        self.status_code = status_code
        self.headers = headers
        self._content = content
        self.url = url
        self._text = None
        self._json = None
        
    @property
    def content(self) -> bytes:
        """Get raw content"""
        return self._content
        
    @property
    def text(self) -> str:
        """Get text content"""
        if self._text is None:
            # Try to decode as utf-8, fallback to latin-1
            try:
                self._text = self._content.decode('utf-8')
            except UnicodeDecodeError:
                self._text = self._content.decode('latin-1')
        return self._text
        
    def json(self) -> Any:
        """Parse JSON content"""
        if self._json is None:
            self._json = json.loads(self.text)
        return self._json
        
    def raise_for_status(self):
        """Raise exception for bad status codes"""
        if 400 <= self.status_code < 600:
            raise HTTPError(self.url, self.status_code, "HTTP Error", self.headers, None)
            
    @property
    def ok(self) -> bool:
        """Check if status code is success"""
        return 200 <= self.status_code < 300


class HTTPClientManager:
    """HTTP client manager for API requests using standard library"""
    
    def __init__(self, base_url: str = "", timeout: int = 30, max_retries: int = 3):
        """Initialize HTTP client manager
        
        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._headers = {
            'User-Agent': 'Kodi Flickr Addon/2.0.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        self._auth = None
        self._is_initialized = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        
    def initialize(self) -> bool:
        """Initialize HTTP client
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Create SSL context that validates certificates
            context = ssl.create_default_context()
            
            # Create and install opener
            opener = build_opener(HTTPSHandler(context=context))
            install_opener(opener)
            
            self._is_initialized = True
            self.logger.debug("HTTP client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize HTTP client: {e}")
            return False
    
    def close(self):
        """Close HTTP client and cleanup resources"""
        # Nothing to close with urllib
        self._is_initialized = False
        self.logger.debug("HTTP client closed")
    
    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Optional[Response]:
        """Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Additional headers
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            Response object or None on error
        """
        if not self._is_initialized:
            self.logger.error("HTTP client not initialized")
            return None
            
        # Build full URL
        if self.base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url + '/', url.lstrip('/'))
            
        # Add query parameters
        if params:
            # Check if URL already has query parameters
            if '?' in url:
                url += '&' + urlencode(params)
            else:
                url += '?' + urlencode(params)
                
        # Use provided timeout or default
        request_timeout = timeout or self.timeout
        
        # Prepare request body
        body = None
        content_type = None
        
        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            content_type = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                body = urlencode(data).encode('utf-8')
                content_type = 'application/x-www-form-urlencoded'
            else:
                body = data
                
        # Prepare headers
        request_headers = self._headers.copy()
        if headers:
            request_headers.update(headers)
            
        # Set content type if not already set
        if body and content_type and 'Content-Type' not in request_headers:
            request_headers['Content-Type'] = content_type
            
        # Manual retry logic
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                # Create request object
                req = Request(
                    url=url,
                    data=body,
                    headers=request_headers,
                    method=method
                )
                
                # Make request
                with urlopen(req, timeout=request_timeout) as response:
                    # Get response headers as dictionary
                    headers_dict = dict(response.getheaders())
                    
                    # Get response content
                    content = response.read()
                    
                    # Handle gzip encoding
                    if headers_dict.get('Content-Encoding', '').lower() == 'gzip':
                        content = gzip.GzipFile(fileobj=BytesIO(content)).read()
                        
                    # Create response object
                    resp = Response(
                        status_code=response.status,
                        headers=headers_dict,
                        content=content,
                        url=url
                    )
                    
                    self.logger.debug(f"Response: {resp.status_code}")
                    return resp
                    
            except HTTPError as e:
                # Handle rate limiting
                if e.code == 429 and attempt < self.max_retries:
                    retry_after = int(e.headers.get('Retry-After', 2))
                    self.logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                    
                # Handle server errors
                elif 500 <= e.code < 600 and attempt < self.max_retries:
                    self.logger.warning(f"Server error {e.code}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
                # Create response object for error
                headers_dict = dict(e.headers.items())
                content = e.read() if hasattr(e, 'read') else b''
                
                # Handle gzip encoding
                if headers_dict.get('Content-Encoding', '').lower() == 'gzip':
                    content = gzip.GzipFile(fileobj=BytesIO(content)).read()
                    
                resp = Response(
                    status_code=e.code,
                    headers=headers_dict,
                    content=content,
                    url=url
                )
                
                self.logger.error(f"HTTP error {e.code}: {e.reason}")
                return resp
                
            except URLError as e:
                if attempt < self.max_retries:
                    self.logger.warning(f"URL error on attempt {attempt + 1}, retrying: {e.reason}")
                    time.sleep(2 ** attempt)
                    continue
                self.logger.error(f"URL error after {self.max_retries + 1} attempts: {e.reason}")
                return None
                
            except TimeoutError:
                if attempt < self.max_retries:
                    self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                self.logger.error(f"Request timeout after {self.max_retries + 1} attempts")
                return None
                
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return None
        
        return None
    
    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[Response]:
        """Make GET request
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional arguments
            
        Returns:
            Response object or None on error
        """
        return self._make_request('GET', url, params=params, headers=headers, **kwargs)
    
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[Response]:
        """Make POST request
        
        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Additional headers
            **kwargs: Additional arguments
            
        Returns:
            Response object or None on error
        """
        return self._make_request('POST', url, data=data, json_data=json, headers=headers, **kwargs)
    
    def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[Response]:
        """Make PUT request
        
        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Additional headers
            **kwargs: Additional arguments
            
        Returns:
            Response object or None on error
        """
        return self._make_request('PUT', url, data=data, json_data=json, headers=headers, **kwargs)
    
    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[Response]:
        """Make DELETE request
        
        Args:
            url: Request URL
            headers: Additional headers
            **kwargs: Additional arguments
            
        Returns:
            Response object or None on error
        """
        return self._make_request('DELETE', url, headers=headers, **kwargs)
    
    def is_available(self) -> bool:
        """Check if HTTP client is available and initialized
        
        Returns:
            bool: True if available and ready
        """
        return self._is_initialized
    
    def set_headers(self, headers: Dict[str, str]):
        """Set default headers for all requests
        
        Args:
            headers: Dictionary of headers
        """
        if headers:
            self._headers.update(headers)
    
    def set_auth(self, username: str, password: str):
        """Set basic authentication for requests
        
        Args:
            username: Authentication username
            password: Authentication password
        """
        # Create password manager
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        
        # Add credentials
        if self.base_url:
            password_mgr.add_password(None, self.base_url, username, password)
        
        # Create and install opener with authentication handler
        auth_handler = HTTPBasicAuthHandler(password_mgr)
        opener = build_opener(auth_handler)
        install_opener(opener)


class HTTPBasicAuth:
    """Basic authentication for compatibility with requests"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


# Convenience functions for backward compatibility
def create_http_client(base_url: str = "", **kwargs) -> HTTPClientManager:
    """Create and initialize HTTP client
    
    Args:
        base_url: Base URL for requests
        **kwargs: Additional arguments for HTTPClientManager
        
    Returns:
        Initialized HTTPClientManager instance
    """
    client = HTTPClientManager(base_url=base_url, **kwargs)
    client.initialize()
    return client


def get_sync(url: str, **kwargs) -> Optional[Response]:
    """Make synchronous GET request
    
    Args:
        url: Request URL
        **kwargs: Additional arguments
        
    Returns:
        Response object or None on error
    """
    with create_http_client() as client:
        return client.get(url, **kwargs)


def post_sync(url: str, **kwargs) -> Optional[Response]:
    """Make synchronous POST request
    
    Args:
        url: Request URL
        **kwargs: Additional arguments
        
    Returns:
        Response object or None on error
    """
    with create_http_client() as client:
        return client.post(url, **kwargs)