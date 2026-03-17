"""
Configuration Module
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """
    Configuration manager
    """
    
    def __init__(self, config_file: str = "config/settings.yaml"):
        """
        Initialize configuration
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        
        try:
            self._load_config()
        except Exception as e:
            print(f"Warning: Failed to load configuration: {e}")
            self.config = self._get_default_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent.parent / self.config_file
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'version': '0.1.0',
            'models': {
                'macro': {
                    'type': 'arima',
                    'forecast_horizon': 12,
                    'confidence_level': 0.95
                }
            },
            'risk': {
                'levels': {
                    'low': {'max_volatility': 0.15, 'max_drawdown': 0.15},
                    'moderate': {'max_volatility': 0.25, 'max_drawdown': 0.25},
                    'high': {'max_volatility': 0.35, 'max_drawdown': 0.35}
                }
            }
        }
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key (e.g., "models.macro.type")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        parts = key.split('.')
        value = self.config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: New value
        """
        parts = key.split('.')
        config = self.config
        
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
        
        config[parts[-1]] = value
    
    def save(self) -> None:
        """Save configuration to file"""
        config_path = Path(__file__).parent.parent / self.config_file
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dict syntax"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value using dict syntax"""
        self.set(key, value)
