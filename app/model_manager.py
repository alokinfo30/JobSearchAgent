import os
import logging
import random
from typing import List, Dict, Optional, Any
from enum import Enum
import time
import json
from openai import OpenAI

logger = logging.getLogger(__name__)

class FallbackStrategy(Enum):
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"

class ModelProvider:
    OPENROUTER = "openrouter"

class ProviderConfig:
    """Configuration for OpenRouter with free tier models"""
    
    # Free models available on OpenRouter (No cost!)
    FREE_MODELS = [       
        "mistralai/mixtral-8x22b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "openai/gpt-4o-mini:free",
        "deepseek/deepseek-chat:free"
    ]

    
    # Paid models (cost per million tokens)
    PAID_MODELS = {
        "openai/gpt-4o-mini": {"cost_per_1m": 0.15, "quality": 8},
        "openai/gpt-4o": {"cost_per_1m": 5.00, "quality": 10},
        "anthropic/claude-3.5-sonnet": {"cost_per_1m": 3.00, "quality": 9},
        "meta-llama/llama-3.1-70b-instruct": {"cost_per_1m": 0.90, "quality": 7}
    }

class OpenRouterManager:
    """
    Manages OpenRouter API with intelligent model routing and fallback
    No daily limits - pay-as-you-go with free tier support
    """
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables!")
        
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.app_url = os.getenv('OPENROUTER_APP_URL', 'http://localhost:5000')
        self.app_name = os.getenv('OPENROUTER_APP_NAME', 'JobSearchAgent')
        
        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": self.app_url,
                "X-Title": self.app_name
            }
        )
        
        # Model configuration
        self.primary_model = os.getenv('OPENROUTER_PRIMARY_MODEL', 'openai/gpt-4o-mini')
        self.fallback_models = self._get_fallback_models()
        
        # Agent-specific models
        self.agent_models = {
            'job_searcher': os.getenv('JOB_SEARCHER_MODEL', self.primary_model),
            'resume_customizer': os.getenv('RESUME_CUSTOMIZER_MODEL', self.primary_model),
            'email_drafter': os.getenv('EMAIL_DRAFTER_MODEL', self.primary_model)
        }
        
        # Strategy
        strategy_name = os.getenv('MODEL_FALLBACK_STRATEGY', 'sequential')
        try:
            self.strategy = FallbackStrategy(strategy_name.lower())
        except ValueError:
            self.strategy = FallbackStrategy.SEQUENTIAL
        
        self._round_robin_counter = 0
        self._model_cache = {}
        self._last_test_time = 0
        self._cache_duration = 300  # 5 minutes
        
        logger.info("🚀 OpenRouter Manager initialized")
        logger.info(f"  Primary Model: {self.primary_model}")
        logger.info(f"  Fallback Models: {self.fallback_models}")
        logger.info(f"  Free Models Available: {ProviderConfig.FREE_MODELS}")
        
        # Test connection
        self._test_connection()
    
    def _get_fallback_models(self) -> List[str]:
        """Get fallback models from env or use defaults"""
        fallbacks = os.getenv('OPENROUTER_FALLBACK_MODELS', '')
        if fallbacks:
            return [m.strip() for m in fallbacks.split(',')]
        
        # Default fallbacks (mix of free and paid)
        return [
            "mistralai/mixtral-8x22b-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "openai/gpt-4o-mini:free",           
            "deepseek/deepseek-chat:free"
            
        ]
    
    def _test_connection(self):
        """Test OpenRouter connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            logger.info("✅ OpenRouter connection successful")
        except Exception as e:
            logger.warning(f"⚠️ OpenRouter connection test failed: {str(e)}")
            logger.info("  Trying fallback models...")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models (use cache for performance)"""
        current_time = time.time()
        
        if current_time - self._last_test_time < self._cache_duration:
            if self._model_cache:
                return self._model_cache
        
        # Test each model
        all_models = [self.primary_model] + self.fallback_models
        available = []
        
        for model in all_models:
            if self._test_model(model):
                available.append(model)
        
        self._model_cache = available
        self._last_test_time = current_time
        
        return available
    
    def _test_model(self, model: str) -> bool:
        """Test if a model is available"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5,
                timeout=60
            )
            return True
        except Exception as e:
            logger.debug(f"Model {model} unavailable: {str(e)}")
            return False
    
    def get_next_model(self, preferred: Optional[str] = None) -> str:
        """Get the next available model based on strategy"""
        available = self.get_available_models()
        
        if not available:
            logger.warning("No available models, using primary model")
            return self.primary_model
        
        # Try preferred model first
        if preferred and preferred in available:
            return preferred
        
        # Apply strategy
        if self.strategy == FallbackStrategy.SEQUENTIAL:
            return available[0]
        elif self.strategy == FallbackStrategy.RANDOM:
            return random.choice(available)
        elif self.strategy == FallbackStrategy.ROUND_ROBIN:
            model = available[self._round_robin_counter % len(available)]
            self._round_robin_counter += 1
            return model
        else:
            return available[0]
    
    def get_model_config(self, agent_type: str) -> Dict[str, Any]:
        """Get model configuration for an agent"""
        preferred = self.agent_models.get(agent_type, self.primary_model)
        chosen_model = self.get_next_model(preferred)
        
        logger.info(f"Agent {agent_type} using model: {chosen_model}")
        
        # Check if model is free
        is_free = any(free_model in chosen_model for free_model in ProviderConfig.FREE_MODELS)
        
        return {
            'provider': ModelProvider.OPENROUTER,
            'model': chosen_model,
            'is_free': is_free,
            'temperature': self._get_agent_temperature(agent_type),
            'client': self.client,
            'base_url': self.base_url
        }
    
    def _get_agent_temperature(self, agent_type: str) -> float:
        temperatures = {
            'job_searcher': 0.3,
            'resume_customizer': 0.4,
            'email_drafter': 0.7
        }
        return temperatures.get(agent_type.lower(), 0.5)
    
    def test_providers(self) -> Dict[str, bool]:
        """Test all configured models with strict timeout to prevent hanging"""
        results = {}
        all_models = [self.primary_model] + self.fallback_models
        
        for model in all_models:
            try:
                logger.info(f"Testing {model}...")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=10,
                    timeout=15
                )
                results[model] = True
                logger.info(f"✅ {model} is available")
            except Exception as e:
                results[model] = False
                logger.warning(f"❌ {model} unavailable: {str(e)}")
        
        return results
    
    def get_daily_limits(self) -> Dict[str, Dict]:
        """Get usage information (no daily limits with OpenRouter)"""
        return {
            'openrouter': {
                'provider': 'OpenRouter',
                'daily_limit': 'Unlimited (pay-as-you-go)',
                'free_models': ProviderConfig.FREE_MODELS,
                'primary_model': self.primary_model,
                'fallback_models': self.fallback_models
            }
        }
    
    def get_cost_estimate(self, model: str, tokens: int) -> float:
        """Estimate cost for a model"""
        if any(free_model in model for free_model in ProviderConfig.FREE_MODELS):
            return 0.0
        
        for paid_model, info in ProviderConfig.PAID_MODELS.items():
            if paid_model in model:
                return (tokens / 1_000_000) * info.get('cost_per_1m', 0)
        
        return 0.01  # Default small cost

# Singleton instance
model_manager = OpenRouterManager()