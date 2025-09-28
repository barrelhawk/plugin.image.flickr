# -*- coding: utf-8 -*-
"""
OAuth 2.0 Authentication for Flickr API
Modern OAuth 2.0 with PKCE flow using httpx
"""

import json
import secrets
import hashlib
import base64
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse
from utils.http_client import HTTPClientManager


class FlickrOAuth2Manager:
    """OAuth 2.0 authentication manager for Flickr API"""
    
    def __init__(self, client_id: str, client_secret: str, config, logger):
        """Initialize OAuth 2.0 manager"""
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.config = config
        self.logger = logger
        
        # OAuth 2.0 endpoints
        self.auth_endpoint = "https://www.flickr.com/services/oauth/authorize"
        self.token_endpoint = "https://www.flickr.com/services/oauth/access_token"
        
        # OAuth 2.0 settings
        self.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # Out-of-band for desktop apps
        self.scope = self.config.get('oauth_scope', 'read')
        
        # PKCE settings
        self.code_verifier = None
        self.code_challenge = None
        self.state = None
        
        # HTTP client
        self.http_client = HTTPClientManager(config, logger)
    
    def is_authenticated(self) -> bool:
        """Check if user has valid authentication"""
        
        access_token = self.config.get('oauth_access_token')
        refresh_token = self.config.get('oauth_refresh_token')
        
        # Check if we have any token
        if not (access_token or refresh_token):
            return False
        
        # Check if access token is expired
        expires_at = self.config.get_int('oauth_expires_at', 0)
        if expires_at > 0:
            import time
            current_time = int(time.time())
            if current_time >= expires_at:
                self.logger.debug("Access token expired")
                # Try to refresh if we have a refresh token
                if refresh_token:
                    return self._refresh_access_token_sync()
                else:
                    return False
        
        return True
    
    def clear_authentication(self) -> None:
        """Clear all authentication data"""
        
        self.logger.info("Clearing authentication data")
        
        # Clear OAuth 2.0 tokens
        self.config.set('oauth_access_token', '')
        self.config.set('oauth_refresh_token', '')
        self.config.set('oauth_token_type', '')
        self.config.set('oauth_expires_in', '')
        self.config.set('oauth_expires_at', '')
        self.config.set('oauth_user_id', '')
        self.config.set('oauth_username', '')
        self.config.set('oauth_user_nsid', '')
        
        # Clear legacy OAuth 1.0 tokens if present
        self.config.set('oauth_token', '')
        self.config.set('oauth_token_secret', '')
        
        # Update auth method
        self.config.set('auth_method', 'oauth2')
        
        # Clear PKCE data
        self.code_verifier = None
        self.code_challenge = None
        self.state = None
    
    def authenticate(self) -> bool:
        """Start OAuth 2.0 authentication flow"""
        
        self.logger.info("Starting OAuth 2.0 authentication with PKCE")
        
        try:
            # Generate PKCE parameters
            self._generate_pkce_parameters()
            
            # Build authorization URL
            auth_url = self._build_authorization_url()
            
            # Show authorization URL to user
            auth_code = self._show_authorization_dialog(auth_url)
            
            if not auth_code:
                self.logger.info("User cancelled authentication")
                return False
            
            # Exchange code for tokens (sync wrapper)
            return self._exchange_code_for_tokens_sync(auth_code.strip())
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}", exc_info=True)
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token"""
        
        if not self.is_authenticated():
            return None
        
        return self.config.get('oauth_access_token')
    
    def _generate_pkce_parameters(self) -> None:
        """Generate PKCE code verifier and challenge"""
        
        # Generate code verifier (43-128 chars, URL safe)
        self.code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        self.code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        # Generate state parameter for CSRF protection
        self.state = secrets.token_urlsafe(32)
        
        self.logger.debug("Generated PKCE parameters")
    
    def _build_authorization_url(self) -> str:
        """Build OAuth 2.0 authorization URL"""
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': self.state,
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256',
            # Flickr-specific parameters
            'perms': self.scope  # Flickr uses 'perms' for permissions
        }
        
        query_string = urlencode(params)
        auth_url = f"{self.auth_endpoint}?{query_string}"
        
        self.logger.debug(f"Built authorization URL")
        return auth_url
    
    def _show_authorization_dialog(self, auth_url: str) -> Optional[str]:
        """Show authorization URL to user and get code"""
        
        try:
            import xbmcgui
            
            dialog = xbmcgui.Dialog()
            
            # Show instructions with copyable URL
            instructions = [
                "Flickr OAuth 2.0 Authentication",
                "",
                "1. Copy the URL below and open it in your web browser:",
                "",
                auth_url,
                "",
                "2. Sign in to Flickr and authorize this application",
                "3. Copy the authorization code from the page",
                "4. Enter it in the next dialog"
            ]
            
            # Show URL in text viewer for easy copying
            dialog.textviewer("Flickr Authorization", "\\n".join(instructions))
            
            # Get authorization code from user
            auth_code = dialog.input(
                heading="Enter Authorization Code",
                type=xbmcgui.INPUT_ALPHANUM
            )
            
            return auth_code
            
        except ImportError:
            # Fallback for development/testing
            self.logger.info(f"Authorization URL: {auth_url}")
            return input("Enter authorization code: ")
    
    async def _exchange_code_for_tokens(self, authorization_code: str) -> bool:
        """Exchange authorization code for access tokens"""
        
        self.logger.info("Exchanging authorization code for tokens")
        
        try:
            # Prepare token request
            token_data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'code_verifier': self.code_verifier
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Make token request
            async with self.http_client as client:
                response = await client.post(
                    self.token_endpoint,
                    data=token_data,
                    headers=headers
                )
            
            if response.status_code == 200:
                return self._process_token_response(response)
            else:
                self.logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Token exchange error: {e}", exc_info=True)
            return False
    
    def _exchange_code_for_tokens_sync(self, authorization_code: str) -> bool:
        """Synchronous wrapper for token exchange"""
        try:
            return asyncio.run(self._exchange_code_for_tokens(authorization_code))
        except Exception as e:
            self.logger.error(f"Sync token exchange error: {e}")
            return False
    
    def _process_token_response(self, response) -> bool:
        """Process token response and save tokens"""
        
        try:
            # Parse response
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                token_data = response.json()
            else:
                # Flickr might return URL-encoded data
                token_data = dict(parse_qs(response.text))
                # Convert lists to single values
                token_data = {k: v[0] if isinstance(v, list) and v else v 
                             for k, v in token_data.items()}
            
            # Extract token information
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            token_type = token_data.get('token_type', 'bearer')
            expires_in = token_data.get('expires_in')
            
            # Flickr-specific user information
            user_nsid = token_data.get('user_nsid')
            username = token_data.get('username')
            fullname = token_data.get('fullname')
            
            if not access_token:
                self.logger.error("No access token in response")
                return False
            
            # Calculate expiration time
            expires_at = 0
            if expires_in:
                try:
                    import time
                    expires_at = int(time.time()) + int(expires_in)
                except (ValueError, TypeError):
                    pass
            
            # Store tokens
            self.config.set('oauth_access_token', access_token)
            self.config.set('oauth_refresh_token', refresh_token or '')
            self.config.set('oauth_token_type', token_type)
            self.config.set('oauth_expires_in', str(expires_in or ''))
            self.config.set('oauth_expires_at', str(expires_at))
            self.config.set('oauth_user_nsid', user_nsid or '')
            self.config.set('oauth_username', username or '')
            self.config.set('oauth_fullname', fullname or '')
            self.config.set('auth_method', 'oauth2')
            
            self.logger.info(f"OAuth 2.0 authentication successful for user: {username or user_nsid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing token response: {e}", exc_info=True)
            return False
    
    async def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        
        refresh_token = self.config.get('oauth_refresh_token')
        
        if not refresh_token:
            self.logger.warning("No refresh token available")
            return False
        
        self.logger.info("Refreshing access token")
        
        try:
            # Prepare refresh request
            refresh_data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Make refresh request
            async with self.http_client as client:
                response = await client.post(
                    self.token_endpoint,
                    data=refresh_data,
                    headers=headers
                )
            
            if response.status_code == 200:
                return self._process_token_response(response)
            else:
                self.logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                # Clear auth if refresh failed
                self.clear_authentication()
                return False
                
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}", exc_info=True)
            return False
    
    def _refresh_access_token_sync(self) -> bool:
        """Synchronous wrapper for token refresh"""
        try:
            return asyncio.run(self._refresh_access_token())
        except Exception as e:
            self.logger.error(f"Sync token refresh error: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        
        access_token = self.get_access_token()
        
        if access_token:
            return {
                'Authorization': f'Bearer {access_token}'
            }
        else:
            return {}
    
    def handle_auth_error(self, error_response: Dict[str, Any]) -> bool:
        """Handle authentication errors from API"""
        
        error_code = error_response.get('code')
        error_msg = error_response.get('message', 'Unknown error')
        
        self.logger.warning(f"Authentication error: {error_code} - {error_msg}")
        
        # Common Flickr error codes for invalid tokens
        if error_code in ['98', '99', '100', '108']:
            self.logger.info("Token appears invalid, attempting refresh")
            
            if self._refresh_access_token_sync():
                return True
            else:
                # Refresh failed, clear auth and require re-authentication
                self.clear_authentication()
                return False
        
        return False
    
    async def close(self) -> None:
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.close()