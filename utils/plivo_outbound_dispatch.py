#!/usr/bin/env python3
"""
Outbound calling script for Plivo + LiveKit integration
Usage: python outbound_call.py --phone "+917055888820" [--name "Nitesh"] [--email "nitish@gmail.com"]
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
import uuid
import subprocess
from typing import Optional, Dict, Any

import requests
from livekit import api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
PLIVO_AUTH_ID = os.environ.get("PLIVO_AUTH_ID")
PLIVO_AUTH_TOKEN = os.environ.get("PLIVO_AUTH_TOKEN")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")

# Configuration
PLIVO_FROM_NUMBER = os.environ.get("PLIVO_FROM_NUMBER", "+918035315890")  # Your Plivo number
SERVER_BASE_URL = os.environ.get("SERVER_BASE_URL", "https://ws.vaaniresearch.com")
AGENT_NAME = "Gikagraph"  # Same as in your main script

class OutboundCallManager:
    """Manages outbound calls with optimized agent connection"""
    
    def __init__(self):
        self.lk_api = None
        self.validate_environment()
    
    def validate_environment(self):
        """Validate required environment variables"""
        required_vars = {
            "PLIVO_AUTH_ID": PLIVO_AUTH_ID,
            "PLIVO_AUTH_TOKEN": PLIVO_AUTH_TOKEN,
            "LIVEKIT_URL": LIVEKIT_URL,
            "LIVEKIT_API_KEY": LIVEKIT_API_KEY,
            "LIVEKIT_API_SECRET": LIVEKIT_API_SECRET,
        }
        
        missing = [var for var, value in required_vars.items() if not value]
        if missing:
            logger.error(f"❌ Missing required environment variables: {missing}")
            logger.error("Please set the following environment variables:")
            for var in missing:
                logger.error(f"   export {var}=your_value_here")
            sys.exit(1)
        
        logger.info("✅ All required environment variables are set")
    
    async def create_livekit_room_and_agent(self, room_name: str, metadata: Dict[str, Any]) -> bool:
        """Create LiveKit room and dispatch agent with optimized timing"""
        try:
            logger.info(f"🏠 Creating LiveKit room: {room_name}")
            
            # Initialize LiveKit API
            self.lk_api = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            
            # Step 1: Create room
            try:
                await self.lk_api.room.create_room(api.CreateRoomRequest(name=room_name))
                logger.info(f"✅ LiveKit room created: {room_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"ℹ️ Room already exists: {room_name}")
                else:
                    logger.error(f"❌ Error creating room: {e}")
                    return False
            
            # Step 2: Dispatch agent immediately (don't wait)
            logger.info(f"🤖 Dispatching agent to room: {room_name}")
            metadata_json = json.dumps(metadata)
            
            # Use subprocess.Popen for non-blocking agent dispatch
            agent_process = subprocess.Popen([
                "lk", "dispatch", "create",
                "--room", room_name,
                "--agent-name", AGENT_NAME,
                "--metadata", metadata_json
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info(f"✅ Agent dispatch initiated (PID: {agent_process.pid})")
            
            # Step 3: Wait for agent to be ready (but with timeout)
            logger.info("⏰ Waiting for agent to join room...")
            agent_ready = await self.wait_for_agent_ready(room_name, timeout=10)
            
            if agent_ready:
                logger.info("🤖 Agent is ready in room!")
                return True
            else:
                logger.warning("⚠️ Agent not detected in room, but proceeding with call...")
                return True  # Proceed anyway, agent might join during call
                
        except Exception as e:
            logger.error(f"❌ Error setting up LiveKit room and agent: {e}")
            return False
    
    async def wait_for_agent_ready(self, room_name: str, timeout: int = 10) -> bool:
        """Wait for agent to join the room"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # List participants in room
                participants = await self.lk_api.room.list_participants(
                    api.ListParticipantsRequest(room=room_name)
                )
                
                # Check if any participant looks like an agent
                for participant in participants.participants:
                    identity = participant.identity.lower()
                    if any(pattern in identity for pattern in ["agent", "mysyara", "ac_", "assistant"]):
                        logger.info(f"�� Agent found in room: {participant.identity}")
                        return True
                
                # Wait a bit before checking again
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"⚠️ Error checking room participants: {e}")
                await asyncio.sleep(1)
        
        logger.warning(f"⚠️ Timeout waiting for agent in room {room_name}")
        return False
    
    def make_plivo_call(self, to_number: str, room_name: str) -> Dict[str, Any]:
        """Initiate outbound call via Plivo API"""
        try:
            logger.info(f"📞 Initiating Plivo call: {PLIVO_FROM_NUMBER} -> {to_number}")
            
            # Plivo API endpoint
            url = f"https://api.plivo.com/v1/Account/{PLIVO_AUTH_ID}/Call/"
            
            # Call parameters
            params = {
                "from": PLIVO_FROM_NUMBER,
                "to": to_number,
                "answer_url": f"{SERVER_BASE_URL}/plivo-app/plivo.xml?room={room_name}",
                "hangup_url": f"{SERVER_BASE_URL}/plivo-app/hangup",
                "answer_method": "GET",
                "hangup_method": "POST",
                "machine_detection": "false",  # Disable AMD for faster connection
                "machine_detection_time": 5000,
                "machine_detection_url": "",
                "time_limit": 3600,  # 1 hour max call duration
                "timeout": 30,  # Ring timeout
            }
            
            # Make API request
            response = requests.post(
                url,
                json=params,
                auth=(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN),
                timeout=10
            )
            
            if response.status_code == 201:
                call_data = response.json()
                call_uuid = call_data.get("call_uuid")
                logger.info(f"✅ Call initiated successfully!")
                logger.info(f"   Call UUID: {call_uuid}")
                logger.info(f"   Room: {room_name}")
                logger.info(f"   Message: {call_data.get('message', 'N/A')}")
                return {
                    "success": True,
                    "call_uuid": call_uuid,
                    "room_name": room_name,
                    "data": call_data
                }
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"❌ Plivo API error ({response.status_code}): {error_data}")
                return {
                    "success": False,
                    "error": error_data,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            logger.error("❌ Plivo API request timeout")
            return {"success": False, "error": "API timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Plivo API request error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Unexpected error making Plivo call: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Clean up resources"""
        if self.lk_api:
            try:
                await self.lk_api.aclose()
            except Exception as e:
                logger.error(f"❌ Error cleaning up LiveKit API: {e}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Make outbound calls via Plivo + LiveKit")
    parser.add_argument("--phone", "-p", required=True, help="Phone number to call (with country code)")
    parser.add_argument("--name", "-n", help="Caller name (optional)")
    parser.add_argument("--email", "-e", help="Caller email (optional)")
    parser.add_argument("--room", "-r", help="Room name (optional, will generate if not provided)")
    
    args = parser.parse_args()
    
    # Validate phone number format
    phone = args.phone.strip()
    if not phone.startswith("+"):
        logger.error("❌ Phone number must include country code (e.g., +917055888820)")
        sys.exit(1)
    
    # Generate room name if not provided
    room_name = args.room or f"outbound-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    
    # Prepare metadata
    metadata = {
        "call_type": "outbound",
        "phone": phone,
        "timestamp": int(time.time()),
        "room": room_name
    }
    
    if args.name:
        metadata["name"] = args.name
    if args.email:
        metadata["email"] = args.email
    
    logger.info("🚀 Starting outbound call process...")
    logger.info("=" * 60)
    logger.info(f"📞 Phone: {phone}")
    logger.info(f"👤 Name: {args.name or 'Not provided'}")
    logger.info(f"📧 Email: {args.email or 'Not provided'}")
    logger.info(f"🏠 Room: {room_name}")
    logger.info("=" * 60)
    
    call_manager = OutboundCallManager()
    
    try:
        # Step 1: Create room and dispatch agent (optimized)
        logger.info("🏗️ Setting up LiveKit room and agent...")
        room_ready = await call_manager.create_livekit_room_and_agent(room_name, metadata)
        
        if not room_ready:
            logger.error("❌ Failed to set up LiveKit room and agent")
            sys.exit(1)
        
        # Step 2: Make the call (agent should already be joining)
        logger.info("📞 Making outbound call...")
        call_result = call_manager.make_plivo_call(phone, room_name)
        
        if call_result["success"]:
            logger.info("✅ Outbound call process completed successfully!")
            logger.info(f"🏠 Room: {room_name}")
            logger.info(f"📞 Call UUID: {call_result['call_uuid']}")
            logger.info("🎯 Agent should connect automatically when call is answered")
            
            # Optional: Monitor call status
            logger.info("💡 You can monitor the call progress in your server logs")
            logger.info(f"💡 WebSocket URL: ws://sbi.vaaniresearch.com:8765/?room={room_name}")
            
        else:
            logger.error("❌ Failed to initiate outbound call")
            logger.error(f"Error: {call_result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await call_manager.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
