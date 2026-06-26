import os
import logging
import random
from typing import List, Dict, Optional, Any
from enum import Enum
import time
import json

# Import providers
import google.generativeai as genai
from groq import Groq
import openai
from openai import OpenAI as OpenAIClient
import requests

logger = logging.getLogger(__name__)

class FallbackStrategy(Enum):
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"

class ModelProvider:
    GITHUB = "github"
    GEMINI = "gemini"
    GROQ = "groq"
    CEREBRAS = "cerebras"
    OPENAI = "openai"

class ProviderConfig:
    """Configuration for each provider with free tier limits"""
    
    PROVIDERS = {
        ModelProvider.GITHUB: {
            'name': 'GitHub Models',
            'daily_limit': 1000,
            'rpm': 15,
            'models': ['gpt-4o-mini', 'gpt-4o', 'meta-llama-3.1-8b', 'mistral-large']
        },
        ModelProvider.GEMINI: {
            'name': 'Google Gemini',
            'daily_limit': 1500,
            'rpm': 15,
            'models': ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
        },
        ModelProvider.GROQ: {
            'name': 'Groq',
            'daily_limit': 1000,
            'rpm': 30,
            'models': ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it']
        },
        ModelProvider.CEREBRAS: {
            'name': 'Cerebras',
            'daily_limit': 1000000,  # 1M tokens
            'rpm': 30,
            'models': ['llama3.3-70b', 'llama3-70b']
        },
        ModelProvider.OPENAI: {
            'name': 'OpenAI',
            'daily_limit': 50,
            'rpm': 5,
            'models': ['gpt-3.5-turbo', 'gpt-4-turbo']
        }
    }

class MultiProviderManager:
    """Manages multiple AI providers with free tiers"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.provider_list = list(self.providers.keys())
        self._round_robin_counter = 0
        self._usage_count = {provider: 0 for provider in self.providers.keys()}
        
        strategy_name = os.getenv('MODEL_FALLBACK_STRATEGY', 'sequential')
        try:
            self.strategy = FallbackStrategy(strategy_name.lower())
        except ValueError:
            self.strategy = FallbackStrategy.SEQUENTIAL
        
        logger.info(f"🚀 MultiProviderManager initialized with {len(self.providers)} providers")
        for provider, config in self.providers.items():
            info = ProviderConfig.PROVIDERS.get(provider, {})
            logger.info(f"  ✓ {info.get('name', provider)}: {config.get('model', 'N/A')} ({info.get('daily_limit', '?')} req/day)")
    
    def _initialize_providers(self) -> Dict:
        """Initialize all configured providers"""
        providers = {}
        
        # 1. GitHub Models (1000 requests/day)
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            try:
                providers['github'] = {
                    'client': OpenAIClient(
                        base_url="https://models.github.ai/inference/chat/completions",
                        api_key=github_token
                    ),
                    'model': os.getenv('GITHUB_MODEL', 'gpt-4o-mini'),
                    'type': ModelProvider.GITHUB,
                    'provider_name': 'GitHub Models'
                }
                logger.info("✅ GitHub Models initialized")
            except Exception as e:
                logger.warning(f"❌ GitHub init failed: {str(e)}")
        
        # 2. Google Gemini (1500 requests/day)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                providers['gemini'] = {
                    'client': genai,
                    'model': os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
                    'type': ModelProvider.GEMINI,
                    'provider_name': 'Google Gemini'
                }
                logger.info("✅ Gemini initialized")
            except Exception as e:
                logger.warning(f"❌ Gemini init failed: {str(e)}")
        
        # 3. Groq (1000 requests/day)
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            try:
                providers['groq'] = {
                    'client': Groq(api_key=groq_key),
                    'model': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
                    'type': ModelProvider.GROQ,
                    'provider_name': 'Groq'
                }
                logger.info("✅ Groq initialized")
            except Exception as e:
                logger.warning(f"❌ Groq init failed: {str(e)}")
        
        # 4. Cerebras (1M tokens/day)
        cerebras_key = os.getenv('CEREBRAS_API_KEY')
        if cerebras_key:
            try:
                # Cerebras uses OpenAI-compatible API
                providers['cerebras'] = {
                    'client': OpenAIClient(
                        base_url="https://api.cerebras.ai/v1",
                        api_key=cerebras_key
                    ),
                    'model': os.getenv('CEREBRAS_MODEL', 'llama3.3-70b'),
                    'type': ModelProvider.CEREBRAS,
                    'provider_name': 'Cerebras'
                }
                logger.info("✅ Cerebras initialized")
            except Exception as e:
                logger.warning(f"❌ Cerebras init failed: {str(e)}")
        
        # 5. OpenAI fallback
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                providers['openai'] = {
                    'client': OpenAIClient(api_key=openai_key),
                    'model': os.getenv('OPENAI_MODEL_NAME', 'gpt-3.5-turbo'),
                    'type': ModelProvider.OPENAI,
                    'provider_name': 'OpenAI'
                }
                logger.info("✅ OpenAI initialized")
            except Exception as e:
                logger.warning(f"❌ OpenAI init failed: {str(e)}")
        
        return providers
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_for_agent(self, agent_type: str) -> str:
        """Get the preferred provider for an agent type"""
        # Map agent types to providers
        provider_map = {
            'job_searcher': os.getenv('JOB_SEARCHER_PROVIDER', 'gemini'),
            'resume_customizer': os.getenv('RESUME_CUSTOMIZER_PROVIDER', 'groq'),
            'email_drafter': os.getenv('EMAIL_DRAFTER_PROVIDER', 'github')
        }
        return provider_map.get(agent_type.lower(), 'gemini')
    
    def get_next_provider(self, preferred: Optional[str] = None) -> str:
        """Get the next available provider based on strategy"""
        available = self.get_available_providers()
        
        if not available:
            raise ValueError("❌ No providers available!")
        
        # Try preferred provider first
        if preferred and preferred in available:
            return preferred
        
        # Apply strategy
        if self.strategy == FallbackStrategy.SEQUENTIAL:
            return available[0]
        elif self.strategy == FallbackStrategy.RANDOM:
            return random.choice(available)
        elif self.strategy == FallbackStrategy.ROUND_ROBIN:
            provider = available[self._round_robin_counter % len(available)]
            self._round_robin_counter += 1
            return provider
        else:
            return available[0]
    
    def get_model_config(self, agent_type: str) -> Dict[str, Any]:
        """Get model configuration for an agent"""
        preferred = self.get_provider_for_agent(agent_type)
        provider_name = self.get_next_provider(preferred)
        provider = self.providers.get(provider_name)
        
        if not provider:
            # Fallback to any available provider
            available = self.get_available_providers()
            if available:
                provider_name = available[0]
                provider = self.providers[provider_name]
            else:
                raise ValueError("No providers available!")
        
        logger.info(f"Agent {agent_type} using {provider.get('provider_name', provider_name)}")
        
        return {
            'provider': provider_name,
            'model': provider['model'],
            'type': provider['type'],
            'temperature': self._get_agent_temperature(agent_type),
            'client': provider['client']
        }
    
    def _get_agent_temperature(self, agent_type: str) -> float:
        temperatures = {
            'job_searcher': 0.3,
            'resume_customizer': 0.4,
            'email_drafter': 0.7
        }
        return temperatures.get(agent_type.lower(), 0.5)
    
    def test_providers(self) -> Dict[str, bool]:
        """Test all providers with a simple completion"""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                logger.info(f"Testing {provider.get('provider_name', name)}...")
                
                if provider['type'] == ModelProvider.GEMINI:
                    model = provider['client'].GenerativeModel(provider['model'])
                    response = model.generate_content("Say 'OK'")
                    results[name] = bool(response and response.text)
                    
                elif provider['type'] == ModelProvider.GROQ:
                    response = provider['client'].chat.completions.create(
                        model=provider['model'],
                        messages=[{"role": "user", "content": "Say OK"}],
                        max_tokens=10
                    )
                    results[name] = bool(response and response.choices)
                    
                elif provider['type'] == ModelProvider.GITHUB:
                    response = provider['client'].chat.completions.create(
                        model=provider['model'],
                        messages=[{"role": "user", "content": "Say OK"}],
                        max_tokens=10
                    )
                    results[name] = bool(response and response.choices)
                    
                elif provider['type'] == ModelProvider.CEREBRAS:
                    response = provider['client'].chat.completions.create(
                        model=provider['model'],
                        messages=[{"role": "user", "content": "Say OK"}],
                        max_tokens=10
                    )
                    results[name] = bool(response and response.choices)
                    
                elif provider['type'] == ModelProvider.OPENAI:
                    response = provider['client'].chat.completions.create(
                        model=provider['model'],
                        messages=[{"role": "user", "content": "Say OK"}],
                        max_tokens=10
                    )
                    results[name] = bool(response and response.choices)
                else:
                    results[name] = False
                
                if results[name]:
                    logger.info(f"✅ {provider.get('provider_name', name)} is available")
                else:
                    logger.warning(f"❌ {provider.get('provider_name', name)} returned empty response")
                    
            except Exception as e:
                results[name] = False
                logger.warning(f"❌ {provider.get('provider_name', name)} unavailable: {str(e)}")
        
        return results
    
    def get_daily_limits(self) -> Dict[str, Dict]:
        """Get daily limits for all providers"""
        limits = {}
        for provider_name, config in self.providers.items():
            info = ProviderConfig.PROVIDERS.get(provider_name, {})
            limits[provider_name] = {
                'provider': config.get('provider_name', provider_name),
                'daily_limit': info.get('daily_limit', 'Unknown'),
                'rpm': info.get('rpm', 'Unknown'),
                'model': config.get('model', 'N/A')
            }
        return limits

# Singleton instance
model_manager = MultiProviderManager()