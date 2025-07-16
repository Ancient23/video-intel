"""
Factory for creating video analysis providers.

This factory pattern allows for easy addition of new providers
and consistent provider instantiation across the application.
"""

from typing import Dict, Type, Optional
from .base_analyzer import BaseAnalyzer
from .providers.aws_rekognition import AWSRekognitionAnalyzer as AWSRekognitionProvider
from .providers.nvidia_vila import NvidiaVilaAnalyzer as NvidiaVilaProvider
import logging

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating video analysis providers."""
    
    # Registry of available providers
    _providers: Dict[str, Type[BaseAnalyzer]] = {
        'aws_rekognition': AWSRekognitionProvider,
        'nvidia_vila': NvidiaVilaProvider,
    }
    
    # Provider configuration
    _provider_config = {
        'aws_rekognition': {
            'cost_per_frame': 0.001,
            'max_chunk_duration': 300,  # 5 minutes
            'supported_features': [
                'object_detection',
                'face_detection',
                'text_detection',
                'custom_labels',
                'scene_detection'
            ]
        },
        'nvidia_vila': {
            'cost_per_frame': 0.0035,
            'max_chunk_duration': 180,  # 3 minutes
            'supported_features': [
                'activity_recognition',
                'scene_understanding',
                'audio_analysis',
                'multimodal_analysis'
            ]
        }
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, config: Optional[Dict] = None) -> BaseAnalyzer:
        """
        Create a provider instance.
        
        Args:
            provider_name: Name of the provider to create
            config: Optional provider-specific configuration
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider name is not recognized
        """
        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available providers: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name]
        provider_config = cls._provider_config.get(provider_name, {})
        
        # Merge default config with provided config
        if config:
            provider_config = {**provider_config, **config}
        
        logger.info(f"Creating provider: {provider_name}")
        return provider_class(**provider_config)
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseAnalyzer], config: Optional[Dict] = None):
        """
        Register a new provider.
        
        Args:
            name: Name for the provider
            provider_class: Provider class (must inherit from BaseAnalyzer)
            config: Default configuration for the provider
        """
        if not issubclass(provider_class, BaseAnalyzer):
            raise TypeError(f"{provider_class} must inherit from BaseAnalyzer")
        
        cls._providers[name] = provider_class
        if config:
            cls._provider_config[name] = config
        
        logger.info(f"Registered provider: {name}")
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, Dict]:
        """
        Get information about available providers.
        
        Returns:
            Dictionary of provider information
        """
        return {
            name: {
                'class': cls._providers[name].__name__,
                'config': cls._provider_config.get(name, {}),
                'module': cls._providers[name].__module__
            }
            for name in cls._providers
        }
    
    @classmethod
    def get_provider_features(cls, provider_name: str) -> list[str]:
        """
        Get supported features for a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            List of supported features
        """
        if provider_name not in cls._provider_config:
            return []
        
        return cls._provider_config[provider_name].get('supported_features', [])
    
    @classmethod
    def get_provider_cost(cls, provider_name: str) -> float:
        """
        Get cost per frame for a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Cost per frame in USD
        """
        if provider_name not in cls._provider_config:
            return 0.0
        
        return cls._provider_config[provider_name].get('cost_per_frame', 0.0)
    
    @classmethod
    def select_providers_for_features(cls, required_features: list[str]) -> list[str]:
        """
        Select providers that support required features.
        
        Args:
            required_features: List of required features
            
        Returns:
            List of provider names that support all required features
        """
        suitable_providers = []
        
        for provider_name, config in cls._provider_config.items():
            supported = set(config.get('supported_features', []))
            if all(feature in supported for feature in required_features):
                suitable_providers.append(provider_name)
        
        # Sort by cost (cheapest first)
        suitable_providers.sort(key=lambda p: cls.get_provider_cost(p))
        
        return suitable_providers