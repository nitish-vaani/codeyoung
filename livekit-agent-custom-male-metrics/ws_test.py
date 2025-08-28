#!/usr/bin/env python3
"""
Test script for WebSocket LLM integration - Compatible with LiveKit 1.1.4
"""

import asyncio
import logging
from custom_websocket_llm import CustomWebSocketLLM
from livekit.agents import llm

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_websocket_llm():
    """Test the WebSocket LLM implementation"""
    
    # Initialize WebSocket LLM
    ws_url = "wss://e169be5b3dce.ngrok-free.app/llm-websocket"
    call_id = "test-call-12345"
    
    websocket_llm = CustomWebSocketLLM(
        ws_url=ws_url,
        call_id=call_id,
        connection_timeout=10.0,
        response_timeout=30.0
    )
    
    try:
        # Create a test chat context with proper ChatMessage format
        # Use add_message with keyword arguments (all params must be keyword-only)
        chat_ctx = llm.ChatContext()
        chat_ctx.add_message(role="user", content=["Hello, can you tell me a joke?"])
        print("✅ Created ChatContext with add_message")
        
        print("🚀 Starting WebSocket LLM test...")
        print(f"📡 Connecting to: {ws_url}/{call_id}")
        
        # Get response from WebSocket LLM
        llm_stream = await websocket_llm.chat(chat_ctx=chat_ctx)
        
        print("💬 LLM Response:")
        full_response = ""
        async for chunk in llm_stream:
            content = chunk.delta.content
            if content:
                print(content, end="", flush=True)
                full_response += content
        
        print(f"\n\n✅ Test completed successfully!")
        print(f"📝 Full response: {full_response}")
        
        # Test a follow-up message
        print("\n🔄 Testing follow-up message...")
        
        # Create follow-up ChatContext with conversation history
        chat_ctx2 = llm.ChatContext()
        chat_ctx2.add_message(role="user", content=["Hello, can you tell me a joke?"])
        chat_ctx2.add_message(role="assistant", content=[full_response])
        chat_ctx2.add_message(role="user", content=["That's funny! Can you tell me another one?"])
        print("✅ Created follow-up ChatContext")
        
        llm_stream2 = await websocket_llm.chat(chat_ctx=chat_ctx2)
        
        print("💬 Follow-up Response:")
        full_response2 = ""
        async for chunk in llm_stream2:
            content = chunk.delta.content
            if content:
                print(content, end="", flush=True)
                full_response2 += content
        
        print(f"\n\n✅ Follow-up test completed!")
        print(f"📝 Follow-up response: {full_response2}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.exception("Full error details:")
    
    finally:
        # Clean up
        await websocket_llm.close()
        print("🧹 WebSocket connection closed")

async def test_simple_message_creation():
    """Test creating ChatMessage with different formats"""
    print("🧪 Testing ChatMessage and ChatContext creation...")
    
    # Test ChatContext with add_message
    try:
        ctx = llm.ChatContext()
        ctx.add_message(role="user", content=["Hello"])
        print(f"  ✅ ChatContext.add_message works: {len(ctx.items)} item(s)")
    except Exception as e:
        print(f"  ❌ ChatContext.add_message failed: {e}")

if __name__ == "__main__":
    print("🧪 WebSocket LLM Test Script - LiveKit 1.1.4 Compatible")
    print("=" * 60)
    
    # First test message creation
    asyncio.run(test_simple_message_creation())
    
    print("\n" + "=" * 60)
    
    # Then run the main test
    asyncio.run(test_websocket_llm())