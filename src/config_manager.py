"""
Configuration Manager for LBW Decision System
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from loguru import logger


class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Set default config path
        if config_path is None:
            config_path = os.getenv('CONFIG_PATH', 'config/config.yaml')
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # Load configuration
        self.load_config()
        
        # Override with environment variables
        self._apply_env_overrides()
        
        # Validate configuration
        self.validate_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {self.config_path}")
        
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _apply_env_overrides(self) -> None:
        """Override configuration with environment variables"""
        # Video source
        if os.getenv('VIDEO_SOURCE'):
            video_source = os.getenv('VIDEO_SOURCE')
            self.config['video']['source'] = int(video_source) if video_source.isdigit() else video_source
        
        # Device (GPU/CPU)
        if os.getenv('DEVICE'):
            self.config['detection']['device'] = os.getenv('DEVICE')
        
        if os.getenv('USE_GPU'):
            self.config['processing']['use_gpu'] = os.getenv('USE_GPU').lower() == 'true'
        
        # Model path
        if os.getenv('MODEL_PATH'):
            self.config['detection']['model_path'] = os.getenv('MODEL_PATH')
        
        # Output settings
        if os.getenv('OUTPUT_DIR'):
            self.config['output']['output_path'] = os.getenv('OUTPUT_DIR')
        
        if os.getenv('LOG_DIR'):
            self.config['output']['log_path'] = os.getenv('LOG_DIR')
        
        if os.getenv('SAVE_VIDEO'):
            self.config['output']['save_video'] = os.getenv('SAVE_VIDEO').lower() == 'true'
        
        # Debug mode
        if os.getenv('DEBUG'):
            debug = os.getenv('DEBUG').lower() == 'true'
            self.config['output']['log_level'] = 'DEBUG' if debug else 'INFO'
    
    def validate_config(self) -> None:
        """Validate configuration values"""
        required_sections = ['video', 'detection', 'tracking', 'trajectory', 'lbw', 'output']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate video settings
        if self.config['video']['fps'] <= 0:
            raise ValueError("Video FPS must be positive")
        
        # Validate detection settings
        if not (0 <= self.config['detection']['confidence_threshold'] <= 1):
            raise ValueError("Confidence threshold must be between 0 and 1")
        
        # Validate device
        device = self.config['detection']['device']
        if device not in ['cuda', 'cpu']:
            logger.warning(f"Invalid device '{device}', defaulting to 'cpu'")
            self.config['detection']['device'] = 'cpu'
        
        logger.info("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'video.fps')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'video.fps')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """
        Save current configuration to file
        
        Args:
            output_path: Path to save configuration (defaults to original path)
        """
        if output_path is None:
            output_path = self.config_path
        
        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {output_path}")
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting"""
        self.set(key, value)
