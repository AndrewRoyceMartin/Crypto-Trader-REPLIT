"""
Configuration management module.
Handles loading and accessing configuration parameters from config.ini
and environment variables.
"""

import configparser
import os
import logging
from typing import Any, Optional


class Config:
    """Configuration manager class."""
    
    def __init__(self, config_file: str = "config.ini"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.warning(f"Configuration file {self.config_file} not found. Using defaults.")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        Get configuration value with environment variable override.
        
        Args:
            section: Configuration section
            key: Configuration key
            fallback: Default value if not found
            
        Returns:
            Configuration value
        """
        # Check environment variable first
        env_key = f"{section.upper()}_{key.upper()}"
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            return env_value
        
        # Check config file
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value."""
        value = self.get(section, key, str(fallback))
        try:
            return float(value)
        except (ValueError, TypeError):
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value."""
        value = self.get(section, key, str(fallback))
        try:
            return int(value)
        except (ValueError, TypeError):
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(section, key, str(fallback))
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', 'yes', '1', 'on')
    
    def get_exchange_config(self, exchange: str) -> dict:
        """
        Get exchange configuration.
        
        Args:
            exchange: Exchange name (okx, kraken)
            
        Returns:
            Exchange configuration dictionary
        """
        if exchange == 'okx':
            return {
                'apiKey': os.getenv('OKX_API_KEY', self.get('exchanges', 'okx_api_key', '')),
                'secret': os.getenv('OKX_SECRET_KEY', self.get('exchanges', 'okx_secret_key', '')),
                'password': os.getenv('OKX_PASSPHRASE', self.get('exchanges', 'okx_passphrase', '')),
                'sandbox': False
            }
        elif exchange == 'kraken':
            return {
                'apiKey': os.getenv('KRAKEN_API_KEY', self.get('exchanges', 'kraken_api_key', '')),
                'secret': os.getenv('KRAKEN_SECRET', self.get('exchanges', 'kraken_secret', '')),
                'sandbox': False
            }
        else:
            raise ValueError(f"Unknown exchange: {exchange}")
