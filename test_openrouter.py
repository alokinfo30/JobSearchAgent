#!/usr/bin/env python
"""
Test OpenRouter integration
Run: python test_openrouter.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_openrouter():
    """Test OpenRouter integration"""
    print("=" * 70)
    print("🤖 OPENROUTER INTEGRATION TEST")
    print("=" * 70)
    
    print("\n📋 Environment Configuration:")
    print("-" * 70)
    
    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if api_key:
        print(f"✅ OpenRouter API Key: {api_key[:10]}...{api_key[-10:]}")
    else:
        print("❌ OpenRouter API Key NOT FOUND!")
        print("\n   Get your key from: https://openrouter.ai/keys")
        return False
    
    print(f"   Base URL: {os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')}")
    print(f"   Primary Model: {os.getenv('OPENROUTER_PRIMARY_MODEL', 'openai/gpt-4o-mini')}")
    print(f"   Fallback Models: {os.getenv('OPENROUTER_FALLBACK_MODELS', 'Default fallbacks')}")
    
    print("\n🔄 Testing models...")
    print("-" * 70)
    
    try:
        from app.model_manager import model_manager
        
        results = model_manager.test_providers()
        
        print("\n📊 Model Status:")
        print("-" * 70)
        available_count = 0
        free_available = 0
        
        for model, available in results.items():
            status = "✅ AVAILABLE" if available else "❌ UNAVAILABLE"
            is_free = "🆓 FREE" if "free" in model else "💰 PAID"
            print(f"{model:40} : {status} {is_free}")
            if available:
                available_count += 1
                if "free" in model:
                    free_available += 1
        
        print("-" * 70)
        print(f"\n📈 SUMMARY:")
        print(f"   Total Models Tested: {len(results)}")
        print(f"   Available: {available_count}/{len(results)}")
        print(f"   Free Models Available: {free_available}")
        
        if available_count == 0:
            print("\n❌ No models available! Check:")
            print("   1. OpenRouter API key is valid")
            print("   2. You have internet connection")
            print("   3. Add credits if using paid models")
        else:
            print(f"\n✅ OpenRouter is working! Available models:")
            for model, available in results.items():
                if available:
                    print(f"   → {model}")
        
        print("\n" + "=" * 70)
        print("💡 Free Models Available on OpenRouter:")       
        print("   • mistralai/mixtral-8x22b-instruct:free")
        print("   • meta-llama/llama-3.1-8b-instruct:free")
        print("   • openai/gpt-4o-mini:free")       
        print("   • deepseek/deepseek-chat:free")
        print("=" * 70)
            

        return available_count > 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_openrouter()
    sys.exit(0 if success else 1)