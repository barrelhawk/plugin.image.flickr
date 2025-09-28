# -*- coding: utf-8 -*-
"""
Logging utilities for Flickr Add-on
Provides standardized logging with Kodi integration
"""

import logging
import sys
import os
from typing import Optional

try:
    import xbmc
    KODI_AVAILABLE = True
except ImportError:
    KODI_AVAILABLE = False


class KodiLogHandler(logging.Handler):
    """Custom log handler that outputs to Kodi's log"""
    
    # Map Python log levels to Kodi log levels
    LEVEL_MAP = {
        logging.DEBUG: 0,      # LOGDEBUG
        logging.INFO: 1,       # LOGINFO  
        logging.WARNING: 2,    # LOGWARNING
        logging.ERROR: 3,      # LOGERROR
        logging.CRITICAL: 3    # LOGERROR (Kodi doesn't have LOGCRITICAL)
    }
    
    def __init__(self, addon_id: str):
        super().__init__()
        self.addon_id = addon_id
    
    def emit(self, record):
        """Emit a log record to Kodi's log"""
        
        if not KODI_AVAILABLE:
            return
        
        try:
            # Format the message
            msg = self.format(record)
            
            # Get Kodi log level
            kodi_level = self.LEVEL_MAP.get(record.levelno, 1)  # Default to INFO
            
            # Add addon prefix
            formatted_msg = f"[{self.addon_id}] {msg}"
            
            # Log to Kodi
            xbmc.log(formatted_msg, kodi_level)
            
        except Exception:
            # If logging fails, we can't really do much about it
            pass


class FlickrLogger:
    """Enhanced logger for Flickr addon"""
    
    def __init__(self, name: str, addon_id: str, debug_enabled: bool = False, 
                 log_level: str = 'info'):
        self.name = name
        self.addon_id = addon_id
        self.debug_enabled = debug_enabled
        
        # Create logger
        self.logger = logging.getLogger(name)
        
        # Set log level
        level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }
        
        if debug_enabled:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(level_map.get(log_level.lower(), logging.INFO))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add Kodi handler
        if KODI_AVAILABLE:
            kodi_handler = KodiLogHandler(addon_id)
            formatter = logging.Formatter(
                '%(name)s - %(levelname)s - %(message)s'
            )
            kodi_handler.setFormatter(formatter)
            self.logger.addHandler(kodi_handler)
        else:
            # Fallback to console for development
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message"""
        if self.debug_enabled:
            self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(msg, *args, **kwargs)
    
    def warn(self, msg: str, *args, **kwargs):
        """Alias for warning"""
        self.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, exc_info=True, **kwargs):
        """Log exception with traceback"""
        self.logger.error(msg, *args, exc_info=exc_info, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(msg, *args, **kwargs)


def setup_logging(addon_id: str, debug_enabled: bool = False, 
                  log_level: str = 'info') -> FlickrLogger:
    """Set up logging for the addon"""
    
    logger_name = f"{addon_id}.main"
    return FlickrLogger(
        name=logger_name,
        addon_id=addon_id,
        debug_enabled=debug_enabled,
        log_level=log_level
    )


def get_logger(name: str, addon_id: str, debug_enabled: bool = False,
               log_level: str = 'info') -> FlickrLogger:
    """Get a logger for a specific module"""
    
    logger_name = f"{addon_id}.{name}"
    return FlickrLogger(
        name=logger_name,
        addon_id=addon_id,
        debug_enabled=debug_enabled,
        log_level=log_level
    )