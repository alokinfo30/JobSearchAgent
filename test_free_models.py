#!/usr/bin/env python
"""
Test all free providers
Run: python test_free_models.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_providers():
    """Test all configured free providers"""
    print("=" * 70)
    print("🤖 FREE MULTI-PROVIDER TEST")
    print("=" * 70)
    
    print("\n📋 Environment Configuration:")
    print("-" * 70)
    
    # Check each provider key
    providers_check = [
        ('GITHUB_TOKEN', 'GitHub Models', '1,000/day', 'https://github.com/settings/tokens'),
        ('GEMINI_API_KEY', 'Google Gemini', '1,500/day', 'https://ai.google.dev/'),
        ('GROQ_API_KEY', 'Groq', '1,000/day', 'https://console.groq.com/'),
        ('CEREBRAS_API_KEY', 'Cerebras', '1M tokens/day', 'https://cerebras.ai/inference'),
        ('OPENAI_API_KEY', 'OpenAI (fallback)', 'Quota dependent', 'https://platform.openai.com/api-keys')
    ]
    
    for key, name, limit, url in providers_check:
        exists = bool(os.getenv(key))
        status = "✅ Set" if exists else "❌ Missing"
        print(f"{name:25} : {status} (Limit: {limit})")
        if not exists and key != 'OPENAI_API_KEY':
            print(f"   → Get key from: {url}")
    
    print("-" * 70)
    
    try:
        from app.model_manager import model_manager
        
        # Show provider limits
        print("\n📊 Provider Daily Limits:")
        print("-" * 70)
        limits = model_manager.get_daily_limits()
        for provider, info in limits.items():
            print(f"{info.get('provider', provider):15} : {info.get('daily_limit', '?')} req/day | {info.get('model', 'N/A')}")
        
        print("\n🔄 Testing all providers...")
        print("-" * 70)
        
        results = model_manager.test_providers()
        
        print("\n📊 Provider Status:")
        print("-" * 70)
        available_count = 0
        unavailable_list = []
        
        for provider, available in results.items():
            info = model_manager.providers.get(provider, {})
            name = info.get('provider_name', provider)
            status = "✅ AVAILABLE" if available else "❌ UNAVAILABLE"
            print(f"{name:20} : {status}")
            if available:
                available_count += 1
            else:
                unavailable_list.append(name)
        
        total_count = len(results)
        print("-" * 70)
        print(f"\n📈 SUMMARY: {available_count}/{total_count} providers available")
        
        if available_count == 0:
            print("\n⚠️  No providers available! Please add API keys to your .env file:")
            print("   1. GEMINI_API_KEY - Get from: https://ai.google.dev/")
            print("   2. GROQ_API_KEY - Get from: https://console.groq.com/")
            print("   3. GITHUB_TOKEN - Get from: https://github.com/settings/tokens (with read:models scope)")
            print("   4. CEREBRAS_API_KEY - Get from: https://cerebras.ai/inference")
        
        if unavailable_list:
            print(f"\n⚠️  Unavailable providers: {', '.join(unavailable_list)}")
            print("   Check your API keys and internet connection.")
        
        print("\n" + "=" * 70)
        print("💡 Provider Recommendations:")
        print("   • Gemini: Best for search and analysis (1,500 req/day)")
        print("   • Groq: Best for fast processing (1,000 req/day, 30 RPM)")
        print("   • GitHub: Best for writing tasks (1,000 req/day)")
        print("   • Cerebras: Best for batch processing (1M tokens/day)")
        print("=" * 70)
        
        return available_count > 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_providers()
    sys.exit(0 if success else 1)