#!/usr/bin/env python3
"""
Debug script to check LLMStream constructor signature
"""

try:
    from livekit.agents import llm
    import inspect
    
    print("🔍 Checking LLMStream constructor...")
    
    # Check LLMStream constructor signature
    sig = inspect.signature(llm.LLMStream.__init__)
    print(f"LLMStream.__init__ signature: {sig}")
    
    # Check what methods it has
    print(f"\nLLMStream methods:")
    for attr in sorted(dir(llm.LLMStream)):
        if not attr.startswith('_'):
            obj = getattr(llm.LLMStream, attr)
            print(f"  - {attr}: {type(obj)}")

except ImportError as e:
    print(f"❌ Failed to import: {e}")