"""
Chat session timeout manager following the idle call watcher pattern.
Monitors chat sessions for inactivity and handles cleanup.
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from .config_manager import config_manager

logger = logging.getLogger("chat-session-watcher")

class ChatSessionTimeoutManager:
    """Simple chat session timeout manager following idle call watcher pattern"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.config = config_manager.config.get("chat_session_timeouts", {})
        
        # Timeout settings (similar to idle call watcher)
        self.inactivity_timeout = self.config.get("inactivity_timeout", 1800)  # 30 minutes
        self.warning_timeout = self.config.get("warning_before_timeout", 300)  # 5 minutes before timeout
        self.check_interval = 5  # Check every 5 seconds (like idle call watcher)
        
        logger.info(f"Chat session timeout manager initialized: timeout={self.inactivity_timeout}s, warning={self.warning_timeout}s")
    
    def register_session(self, session_id: str, user_id: str, agent_instance=None):
        """Register a new chat session"""
        current_time = time.monotonic()
        
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "agent_instance": agent_instance,
            "last_activity": current_time,
            "warning_sent": False,
            "status": "active"
        }
        
        logger.info(f"Registered chat session {session_id} for user {user_id}")
    
    def update_activity(self, session_id: str):
        """Update last activity time (like user speech detection in idle call watcher)"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = time.monotonic()
            self.active_sessions[session_id]["warning_sent"] = False  # Reset warning flag
            logger.debug(f"Updated activity for session {session_id}")
    
    def unregister_session(self, session_id: str):
        """Remove session from tracking"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Unregistered session {session_id}")
    
    async def session_timeout_watcher(self, session_id: str):
        """
        Watch a single session for timeout (similar to idle_call_watcher)
        This runs as a background task for each session
        """
        try:
            logger.info(f"Started timeout watcher for session {session_id}")
            
            while session_id in self.active_sessions:
                session_info = self.active_sessions[session_id]
                current_time = time.monotonic()
                
                # Calculate time since last activity
                time_since_activity = current_time - session_info["last_activity"]
                time_until_timeout = self.inactivity_timeout - time_since_activity
                
                # Send warning if approaching timeout (like idle call watcher warning)
                if (time_since_activity > (self.inactivity_timeout - self.warning_timeout) and 
                    not session_info["warning_sent"]):
                    
                    await self._send_timeout_warning(session_id)
                    session_info["warning_sent"] = True
                
                # Timeout if inactive too long
                if time_since_activity > self.inactivity_timeout:
                    logger.info(f"Session {session_id} timed out after {time_since_activity:.1f}s of inactivity")
                    await self._timeout_session(session_id, "Session timed out due to inactivity")
                    break
                
                # Sleep before next check (like idle call watcher)
                await asyncio.sleep(self.check_interval)
        
        except asyncio.CancelledError:
            logger.info(f"Timeout watcher for session {session_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in timeout watcher for session {session_id}: {e}")
        finally:
            logger.info(f"Timeout watcher for session {session_id} stopped")
    
    async def _send_timeout_warning(self, session_id: str):
        """Send timeout warning (like idle call watcher warning)"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return
        
        try:
            agent = session_info.get("agent_instance")
            if agent and hasattr(agent, 'send_message'):
                warning_msg = (
                    f"⚠️ Your chat session will end in {self.warning_timeout // 60} minutes "
                    f"due to inactivity. Send a message to keep the session active."
                )
                await agent.send_message(warning_msg, "system")
                logger.info(f"Sent timeout warning to session {session_id}")
        except Exception as e:
            logger.error(f"Error sending timeout warning to session {session_id}: {e}")
    
    # async def _timeout_session(self, session_id: str, reason: str):
    #     """End session due to timeout (like hangup in idle call watcher)"""
    #     session_info = self.active_sessions.get(session_id)
    #     if not session_info:
    #         return
        
    #     try:
    #         agent = session_info.get("agent_instance")
    #         if agent:
    #             # Send final message
    #             if hasattr(agent, 'send_message'):
    #                 await agent.send_message("Chat session ended due to inactivity. Thank you!", "system")
    #                 await asyncio.sleep(1)  # Let message send
                
    #             # End the session
    #             if hasattr(agent, 'end_session') and hasattr(agent, 'session'):
    #                 await agent.end_session(agent.session)
            
    #         # Remove from tracking
    #         self.unregister_session(session_id)
    #         logger.info(f"Session {session_id} ended: {reason}")
            
    #     except Exception as e:
    #         logger.error(f"Error ending session {session_id}: {e}")

    # In chat_session_manager.py
    async def _timeout_session(self, session_id: str, reason: str):
        """End session due to timeout (like hangup in idle call watcher)"""
        session_info = self.active_sessions.get(session_id)
        if not session_info:
            return
        
        try:
            agent = session_info.get("agent_instance")
            if agent:
                # Send final message
                if hasattr(agent, 'send_message'):
                    await agent.send_message("Chat session ended due to inactivity. Thank you!", "system")
                    await asyncio.sleep(1)  # Let message send
                
                # FORCE DISCONNECT THE ROOM
                if hasattr(agent, 'room') and agent.room:
                    await agent.room.disconnect()
                    logger.info(f"Disconnected room for session {session_id}")
            
            # Remove from tracking
            self.unregister_session(session_id)
            logger.info(f"Session {session_id} ended: {reason}")
            
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}")

# Global timeout manager instance
chat_timeout_manager = ChatSessionTimeoutManager()

async def start_chat_timeout_watcher(session_id: str, user_id: str, agent_instance=None):
    """Start timeout monitoring for a chat session (like starting idle_call_watcher)"""
    # Register the session
    chat_timeout_manager.register_session(session_id, user_id, agent_instance)
    
    # Start the timeout watcher task
    timeout_task = asyncio.create_task(
        chat_timeout_manager.session_timeout_watcher(session_id)
    )
    
    logger.info(f"Started chat timeout watcher for session {session_id}")
    return timeout_task

def update_chat_activity(session_id: str):
    """Update activity for a chat session (like detecting user speech)"""
    chat_timeout_manager.update_activity(session_id)