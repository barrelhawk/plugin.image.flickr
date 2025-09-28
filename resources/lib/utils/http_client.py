# -*- coding: utf-8 -*-
"""
HTTP Client Manager for Flickr Add-on
Provides HTTP client with timeout, retry, and error handling
"""

import asyncio
import ssl
from typing import Dict, Any, Optional, Union, AsyncContextManager
from urllib.parse import urljoin, urlparse
import logging

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    # Fallback for development
    class httpx:
        class AsyncClient:
            def __init__(self, *args, **kwargs):
                pass
        class Timeout:
            def __init__(self, *args, **kwargs):
                pass


class HTTPClientManager:
    """HTTP client manager with async support and error handling"""
    
    def __init__(self, config, logger):
        """Initialize HTTP client manager"""
        
        self.config = config
        self.logger = logger
        self.client: Optional[httpx.AsyncClient] = None
        self._is_initialized = False
        
        # Default settings
        self.base_url = "https://api.flickr.com/services"
        self.user_agent = f"Kodi Flickr Add-on/{config.addon_version}"
        
        # Network settings from config
        self.request_timeout = self.config.get_int('request_timeout', 30)
        self.retry_attempts = self.config.get_int('retry_attempts', 3)
        self.enable_ssl_verify = self.config.get_bool('verify_ssl', True)
        
    async def initialize(self) -> bool:
        """Initialize the HTTP client"""
        
        if not HTTPX_AVAILABLE:
            self.logger.error("httpx library not available - install with 'pip install httpx'")
            return False
        
        if self._is_initialized:
            return True
            
        try:
            # Create timeout configuration
            timeout = httpx.Timeout(
                connect=10.0,  # Connection timeout
                read=self.request_timeout,  # Read timeout
                write=self.request_timeout,  # Write timeout
                pool=5.0  # Pool timeout
            )
            
            # SSL context
            ssl_context = None
            if not self.enable_ssl_verify:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self.logger.warning("SSL verification disabled - use with caution")
            
            # Create client
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=timeout,
                verify=ssl_context if ssl_context else True,
                follow_redirects=True,
                headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'application/json, text/xml',
                    'Accept-Encoding': 'gzip, deflate'
                },
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=100,
                    keepalive_expiry=30
                )
            )
            
            self._is_initialized = True
            self.logger.info(f"HTTP client initialized with timeout={self.request_timeout}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize HTTP client: {e}", exc_info=True)
            return False
    
    async def close(self) -> None:
        """Close the HTTP client"""
        
        if self.client:
            await self.client.aclose()
            self.client = None
            self._is_initialized = False
            self.logger.debug("HTTP client closed")
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """Make GET request"""
        
        return await self._request(
            'GET', 
            endpoint, 
            params=params, 
            headers=headers, 
            auth=auth, 
            timeout=timeout
        )
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """Make POST request"""
        
        return await self._request(
            'POST',
            endpoint,
            params=params,
            data=data,
            json=json,
            headers=headers,
            auth=auth,
            timeout=timeout
        )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        """Make HTTP request with retry logic"""
        
        if not self._is_initialized:
            if not await self.initialize():
                raise RuntimeError("HTTP client not initialized")
        
        # Prepare request parameters
        request_kwargs = {
            'method': method,
            'url': endpoint,
            'params': params,
            'headers': headers,
            'auth': auth,
            'timeout': timeout or self.request_timeout
        }
        
        if data is not None:
            request_kwargs['data'] = data
        if json is not None:
            request_kwargs['json'] = json
        
        # Log request
        url_info = urljoin(self.base_url, endpoint)
        self.logger.debug(f"HTTP {method} {url_info}")
        if params:
            self.logger.debug(f"Request params: {params}")
        
        # Retry loop
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                response = await self.client.request(**request_kwargs)
                
                # Log response
                self.logger.debug(f"HTTP {response.status_code} - {len(response.content)} bytes")
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    self.logger.warning(f"Rate limited - retry after {retry_after}s")
                    
                    # For now, just wait a bit and retry
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(min(int(retry_after), 10))
                        continue
                
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                self.logger.warning(f"Request timeout (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
            except httpx.ConnectError as e:
                last_exception = e
                self.logger.warning(f"Connection error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
            except Exception as e:
                last_exception = e
                self.logger.error(f"Unexpected error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                    
                break  # Don't retry unexpected errors
        
        # All retries failed
        self.logger.error(f"All {self.retry_attempts} request attempts failed")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Request failed after all retry attempts")
    
    def is_available(self) -> bool:
        """Check if HTTP client is available"""
        return HTTPX_AVAILABLE and self._is_initialized
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        
        if not self.client:
            return {'status': 'not_initialized'}
        
        return {
            'status': 'initialized' if self._is_initialized else 'not_initialized',
            'base_url': str(self.client.base_url),
            'timeout': self.request_timeout,
            'retry_attempts': self.retry_attempts,
            'ssl_verify': self.enable_ssl_verify,
            'user_agent': self.user_agent
        }
    
    async def __aenter__(self) -> 'HTTPClientManager':
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        await self.close()


# Synchronous wrapper for backward compatibility
class SyncHTTPClient:
    """Synchronous wrapper for async HTTP client"""
    
    def __init__(self, http_manager: HTTPClientManager):
        """Initialize sync wrapper"""
        self.http_manager = http_manager
        self.logger = http_manager.logger
    
    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, can't use run_until_complete
                self.logger.warning("Cannot run sync HTTP request from async context")
                raise RuntimeError("Cannot make synchronous HTTP request from async context")
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(coro)
    
    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Synchronous GET request"""
        return self._run_async(self.http_manager.get(endpoint, **kwargs))
    
    def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """Synchronous POST request"""
        return self._run_async(self.http_manager.post(endpoint, **kwargs))
    
    def close(self) -> None:
        """Close the HTTP client"""
        self._run_async(self.http_manager.close())