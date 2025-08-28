# # from os import 
# import time
# import asyncio
# from livekit.agents import UserStateChangedEvent, get_job_context, AgentStateChangedEvent, SpeechCreatedEvent
# from livekit.api import DeleteRoomRequest
# from livekit.agents.stt import SpeechEvent

# # watchdog that hangs up after 10 s of silence
# IDLE_LIMIT = 40          # seconds
# CHECK_IN_LIMIT = 15       # SECONDS
# CHECK_INTERVAL = 1       # seconds


# async def hangup():
#     """Helper function to hang up the call by deleting the room"""
#     job_ctx = get_job_context()
#     await job_ctx.api.room.delete_room(
#         DeleteRoomRequest(
#             room=job_ctx.room.name,
#         )
#     )

# async def idle_call_watcher(session):
#     agent_state = "speaking"
#     stt_detected_speech = False
#     hung_up_timer_start = time.monotonic()
#     check_in_timer_start = time.monotonic()
#     confirm_user_presence = 10
#     @session.on("agent_state_changed")
#     def handle_agent_state(event: AgentStateChangedEvent):
#         nonlocal agent_state
#         nonlocal hung_up_timer_start
#         nonlocal check_in_timer_start
#         nonlocal stt_detected_speech
#         agent_state = event.new_state
#         if event.new_state == "speaking":
#             stt_detected_speech = False
#             print("👤 Agent started speaking")
#         elif event.new_state == "listening":
#             hung_up_timer_start = time.monotonic()
#             check_in_timer_start = time.monotonic()
#             print("👤 Agent stopped speaking and started listening")
#         if event.new_state == "thinking":
#             stt_detected_speech = False
#             print("👤 Agent started thinking")
#         elif event.new_state == "initializing ":
#             stt_detected_speech = False
#             print("👤 Agent initializing")

#     @session.on("stt_detects_user_speech")
#     def handle_user_speech(event: SpeechEvent):
#         nonlocal stt_detected_speech
#         stt_detected_speech = True
#         print("USER STARTED SPEAKING.........................................")

#     while True:
#         # print(f"agent_state variable is: {agent_state}")
#         # print(f"stt_detected_speech variable is: {stt_detected_speech}")
#         # print(f"hung_up_timer_start variable is: {hung_up_timer_start}")
#         # print(f"check_in_timer_start variable is: {check_in_timer_start}")
#         # print(f"Time Elapsed: {(time.monotonic() - hung_up_timer_start)}")
#         if (agent_state=="listening") and (stt_detected_speech==False):
#             if ((time.monotonic() - hung_up_timer_start) > IDLE_LIMIT):
#                 await session.say("It seems there is some connection issue, I can't hear anything. Request you to call again, have a good day!")
#                 await hangup()
#                 break

#             if ((time.monotonic() - check_in_timer_start) > CHECK_IN_LIMIT):
#                 if confirm_user_presence != 0:
#                     await session.say("Are you there? Please respond!")
#                     confirm_user_presence = confirm_user_presence - 1
#                     check_in_timer_start = time.monotonic()

#         await asyncio.sleep(CHECK_INTERVAL)
        



# /app/utils/hungup_idle_call.py - Updated version

import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("idle-watcher")

async def idle_call_watcher(session, idle_timeout: int = 15, warning_timeout: int = 10):
    """
    Monitor call for idle time and hang up if inactive too long
    Only starts counting AFTER agent finishes speaking
    
    Args:
        session: The agent session
        idle_timeout: Seconds of idle time before hanging up (after agent finishes speaking)
        warning_timeout: Seconds before warning user about inactivity (after agent finishes speaking)
    """
    try:
        logger.info(f"Started idle call watcher (timeout: {idle_timeout}s, warning: {warning_timeout}s)")
        
        last_agent_finish_time = None  # Only start timer when agent finishes
        last_user_activity = datetime.now()
        warning_sent = False
        
        def on_conversation_item(event):
            nonlocal last_agent_finish_time, last_user_activity, warning_sent
            
            if event.item.role == 'user':
                last_user_activity = datetime.now()
                warning_sent = False
                logger.debug("User spoke - reset idle timer")
                
            elif event.item.role == 'assistant':
                # Agent finished speaking - NOW we start counting idle time
                last_agent_finish_time = datetime.now()
                warning_sent = False
                logger.debug("Agent finished speaking - start counting idle time")
        
        # Monitor conversation activity
        session.on("conversation_item_added", on_conversation_item)
        
        while True:
            # Check if session is still running
            if not hasattr(session, '_started') or not session._started:
                logger.info("Session no longer running - stopping idle watcher")
                break
            
            await asyncio.sleep(1)  # Check every second
            
            # Don't count idle time until agent has spoken at least once
            if last_agent_finish_time is None:
                continue
            
            # Calculate time since agent last finished speaking
            elapsed_since_agent = (datetime.now() - last_agent_finish_time).total_seconds()
            elapsed_since_user = (datetime.now() - last_user_activity).total_seconds()
            
            # Only count idle time from when agent last finished speaking
            # AND user hasn't spoken since then
            if last_user_activity > last_agent_finish_time:
                # User spoke after agent finished - reset
                continue
            
            # Send warning if approaching timeout
            if elapsed_since_agent > warning_timeout and not warning_sent:
                try:
                    if hasattr(session, '_started') and session._started:
                        await session.say("Are you there? Please respond!")
                        warning_sent = True
                        # Reset timer since agent just spoke again
                        last_agent_finish_time = datetime.now()
                        logger.info(f"Sent idle warning to user (idle for {elapsed_since_agent:.1f}s)")
                    else:
                        logger.debug("Session not active - skipping warning")
                        break
                except Exception as e:
                    logger.warning(f"Failed to send idle warning: {e}")
                    break  # Session is likely closed
            
            # Hang up if idle too long after agent finished speaking
            if elapsed_since_agent > idle_timeout:
                try:
                    if hasattr(session, '_started') and session._started:
                        logger.info(f"Call idle for {elapsed_since_agent:.1f}s after agent finished - hanging up")
                        await session.say("Thank you for calling. Hanging up due to inactivity.")
                        await asyncio.sleep(2)  # Let message play
                        await hangup()
                    else:
                        logger.debug("Session not active - idle timeout not applicable")
                    break
                except Exception as e:
                    logger.warning(f"Failed to hang up idle call: {e}")
                    break
    
    except asyncio.CancelledError:
        logger.info("Idle call watcher cancelled")
        raise  # Re-raise to properly handle cancellation
    
    except Exception as e:
        logger.error(f"Idle call watcher error: {e}")
    
    finally:
        logger.info("Idle call watcher stopped")

async def hangup():
    """Hang up the current call"""
    try:
        # Your hangup implementation here
        logger.info("Hanging up call")
        # Add your actual hangup logic
    except Exception as e:
        logger.error(f"Failed to hang up: {e}")