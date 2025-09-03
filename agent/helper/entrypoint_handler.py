import asyncio
import json
import os
from datetime import datetime
from typing import Any

from livekit import rtc
from livekit.agents import JobContext
from utils.hungup_idle_call import idle_call_watcher

from .config_manager import config_manager
from .logging_config import setup_logging, get_logger
from .call_handlers import CallState, handle_outbound_sip_call, handle_inbound_call, get_disconnect_reason
from .database_helpers import insert_call_end_async
from .session_helpers import (create_agent_session, setup_background_audio, 
                             setup_audio_recording, get_room_input_options,
                             create_chat_session)
from .transcript_manager import transcript_manager
from .agent_class import (create_voice_service_agent, create_chat_service_agent, 
                             VoiceServiceAgent, ChatServiceAgent)
from .data_entities import UserData

# Initialize logging
logger, transcript_logger = setup_logging()

# Constants
OUTBOUND_AGENT_NAME = "Outbound Service Agent"
INBOUND_AGENT_NAME = "Inbound Service Agent"
CHAT_AGENT_NAME = "Chat Service Agent"
CALLING_NUMBER = 00000000000

# Load configuration
config = config_manager.config

async def setup_event_handlers(ctx: JobContext, session_state: CallState, agent, task_refs: dict, modality: str):
    """Setup all event handlers for the session"""
    
    async def record_session_end_once(end_reason: str):
        """Ensure session end is only recorded once"""
        if not session_state.call_end_recorded and session_state.call_started:
            await agent.record_session_end(end_reason)

    # Enhanced participant disconnect handler with task cleanup
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant_obj: rtc.RemoteParticipant):
        if participant_obj.identity == session_state.participant_identity:
            logger.info(f"Participant {participant_obj.identity} disconnected. Reason: {participant_obj.disconnect_reason}")
            
            # Cancel idle watcher when participant disconnects
            if task_refs["idle_watcher"] and not task_refs["idle_watcher"].done():
                logger.debug("Cancelling idle watcher due to participant disconnect")
                task_refs["idle_watcher"].cancel()
            
            disconnect_reason = get_disconnect_reason(participant_obj, session_state)
            asyncio.create_task(record_session_end_once(disconnect_reason))

    # Room disconnect handler
    @ctx.room.on("disconnected")
    def on_room_disconnected():
        logger.info("Room disconnected")
        if task_refs["idle_watcher"] and not task_refs["idle_watcher"].done():
            task_refs["idle_watcher"].cancel()
        asyncio.create_task(record_session_end_once("Room disconnected"))

    # Chat-specific data handler
    if modality == "chat" and isinstance(agent, ChatServiceAgent):

        @ctx.room.on("data_received")
        def on_data_received(*args):
            # Handle both old and new signatures
            if len(args) >= 1:
                data_packet = args[0]
                asyncio.create_task(agent.on_data_received(data_packet))

async def setup_cleanup_callback(ctx: JobContext, session_state: CallState, task_refs: dict):
    """Setup cleanup callback for shutdown"""
    async def cleanup_on_shutdown():
        logger.info("Cleanup on shutdown triggered")
        
        # Cancel idle watcher task first
        if task_refs["idle_watcher"] and not task_refs["idle_watcher"].done():
            logger.info("Cancelling idle call watcher")
            task_refs["idle_watcher"].cancel()
            try:
                await task_refs["idle_watcher"]
            except asyncio.CancelledError:
                logger.debug("Idle watcher cancelled successfully")
            except Exception as e:
                logger.warning(f"Error cancelling idle watcher: {e}")
        
        if session_state.call_started and not session_state.call_end_recorded:
            logger.info("Recording session end during shutdown")
            try:
                session_state.call_end_recorded = True
                operation_id = await insert_call_end_async(
                    session_state.room_name,
                    "System shutdown"
                )
                logger.info(f"Queued shutdown session end: {operation_id}")
            except Exception as e:
                logger.error(f"Failed to queue session end during shutdown: {e}")

    ctx.add_shutdown_callback(cleanup_on_shutdown)

async def handle_sip_mode(ctx: JobContext, contact_info: dict, agent_name: str, session_state: CallState, 
                         required_fields: list = None) -> rtc.RemoteParticipant:
    """Handle SIP mode calls (both inbound and outbound)"""
    if required_fields:  # Outbound call
        phone_number = contact_info["phone"]
        participant_identity = phone_number
        session_state.participant_identity = participant_identity
        
        participant = await handle_outbound_sip_call(
            ctx, phone_number, participant_identity, 
            contact_info, agent_name, session_state
        )
        
        if not participant:  # Call failed
            return None
    else:  # Inbound call
        participant = await handle_inbound_call(ctx, agent_name, session_state)
    
    return participant

async def handle_console_mode(session_state: CallState):
    """Handle console mode for testing"""
    session_state.call_started = True
    session_state.start_time = datetime.now()

async def handle_chat_mode(ctx: JobContext, session_state: CallState, agent_name: str):
    """Handle chat mode sessions"""
    logger.info("Setting up chat mode session")
    session_state.call_started = True
    session_state.start_time = datetime.now()
    session_state.participant_identity = "chat_user"
    return None  # No participant needed for chat initially

async def parse_job_metadata(ctx: JobContext):
    """Parse and validate job metadata with modality support"""
    try:
        logger.info(f"🔍 Raw job metadata: '{ctx.job.metadata}'")
        logger.info(f"🔍 Metadata type: {type(ctx.job.metadata)}")
        
        if ctx.job.metadata is None or ctx.job.metadata == "":
            # Inbound call (legacy - no metadata)
            logger.info("Handling inbound call")
            return {
                "contact_info": {"phone": "unknown"},
                "required_fields": None,
                "agent_name": INBOUND_AGENT_NAME,
                "metadata": {},
                "modality": "voice"
            }
        else:
            # Parse metadata to determine call type and modality
            metadata = json.loads(ctx.job.metadata)
            logger.info(f"Parsed metadata: {metadata}")
            
            # Check modality (default to voice for backward compatibility)
            modality = metadata.get("modality", "voice")
            
            if modality == "chat":
                logger.info("Handling chat session")
                return {
                    "contact_info": {"phone": metadata.get("phone", "chat_session")},
                    "required_fields": None,
                    "agent_name": CHAT_AGENT_NAME,
                    "metadata": metadata,
                    "modality": "chat"
                }
            
            # Check if this is an inbound call with metadata
            elif metadata.get("call_type") == "inbound" or metadata.get("direction") == "inbound":
                logger.info("Handling inbound call")
                caller_phone = metadata.get("phone", "unknown")
                return {
                    "contact_info": {"phone": caller_phone},
                    "required_fields": None,
                    "agent_name": INBOUND_AGENT_NAME,
                    "metadata": metadata,
                    "modality": "voice"
                }
            else:
                # Outbound call
                logger.info("Handling outbound call")
                contact_info = metadata
                required_fields = ["phone"]
                
                missing_fields = [field for field in required_fields if field not in contact_info]
                if missing_fields:
                    raise ValueError(f"Missing required fields in metadata: {missing_fields}")
                    
                return {
                    "contact_info": contact_info,
                    "required_fields": required_fields,
                    "agent_name": OUTBOUND_AGENT_NAME,
                    "metadata": contact_info,
                    "modality": "voice"
                }
                
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse job metadata as JSON: {e}")
        raise ValueError(f"Invalid JSON in job metadata: {e}")
    except Exception as e:
        logger.error(f"Error processing job metadata: {e}")
        raise

async def create_agent_based_on_modality(modality: str, agent_name: str, appointment_time: str, 
                                        contact_info: dict, session_state: CallState, prompt_path: str):
    """Create appropriate agent based on modality"""
    if modality == "chat":
        agent = create_chat_service_agent(
            agent_name=agent_name,
            appointment_time=appointment_time,
            contact_info=contact_info,
            session_state=session_state,
            prompt_path=prompt_path
        )
        logger.info("Created chat service agent")
    else:
        agent = create_voice_service_agent(
            agent_name=agent_name,
            appointment_time=appointment_time,
            contact_info=contact_info,
            session_state=session_state,
            prompt_path=prompt_path
        )
        logger.info("Created voice service agent")
    
    return agent

async def handle_entrypoint(ctx: JobContext):
    """Handle the main entrypoint logic with modality support"""
    await ctx.connect()
    
    # Initialize session state
    session_state = CallState()
    session_state.room_name = ctx.room.name
    
    task_refs = {"idle_watcher": None}

    # Parse job metadata
    job_data = await parse_job_metadata(ctx)
    required_fields = job_data["required_fields"]
    agent_name = job_data["agent_name"]
    metadata = job_data["metadata"]
    contact_info = job_data["contact_info"]
    modality = job_data["modality"]
    
    logger.info(f"Session modality: {modality}")
    logger.info(f"Job metadata parsed: {job_data}")

    # Initialize user data
    userdata = UserData(ctx=ctx)
    agent_config = metadata
    logger.info(f"Agent config from metadata: {agent_config}")

    # Create agent based on modality
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "incoming_call.yaml")
    agent = await create_agent_based_on_modality(
        modality=modality,
        agent_name="Service Assistant",
        appointment_time="next available slot", 
        contact_info=contact_info,
        session_state=session_state,
        prompt_path=prompt_path
    )

    # Setup event handlers and cleanup
    await setup_event_handlers(ctx, session_state, agent, task_refs, modality)
    await setup_cleanup_callback(ctx, session_state, task_refs)

    # Handle different modes and modalities
    if config["mode"] == "SIP":
        
        if modality == "chat":
            # Chat mode with LiveKit
            participant = await handle_chat_mode(ctx, session_state, agent_name)
            
            # Create chat session
            session = create_chat_session(userdata, config, agent_config)
            
            # Set the session in the agent BEFORE starting
            agent.set_session(session)
            
            # Start session for chat - this will call agent.set_room()
            room_input_options = get_room_input_options("CHAT")
            await session.start(
                room=ctx.room,
                agent=agent,
                room_input_options=room_input_options,
            )
            
            # Agent joins and sends welcome message
            await agent.on_enter()


        else:
            # Voice mode
            participant = await handle_sip_mode(ctx, contact_info, agent_name, session_state, required_fields)
            if not participant and required_fields:  # Outbound call failed
                return

            # Create voice session
            session = create_agent_session(userdata, config, agent_config)
            
            # Start agent session
            room_input_options = get_room_input_options(config["mode"])
            await session.start(
                agent=agent,
                room=ctx.room,
                room_input_options=room_input_options,
            )
            
            if participant:
                agent.set_participant(participant)

    elif config["mode"] == 'CONSOLE':
        # Console mode for testing
        await handle_console_mode(session_state)
        
        if modality == "chat":
            session = create_chat_session(userdata, config, agent_config)
            agent.set_session(session)
            room_input_options = get_room_input_options("CHAT")
        else:
            session = create_agent_session(userdata, config, agent_config)
            room_input_options = get_room_input_options(config["mode"])
            
        await session.start(
            room=ctx.room,
            agent=agent,
            room_input_options=room_input_options,
        )

    # Setup transcript persistence AFTER session is created (skip for chat for now)
    if config["store_transcription"]['switch'] and modality == "voice":
        finish_queue = transcript_manager.setup_transcript_persistence(
            session, ctx.room.name, config  # Now session is available
        )
        if finish_queue:
            ctx.add_shutdown_callback(finish_queue)
    
    # Setup background audio if enabled (voice only)
    if modality == "voice":
        await setup_background_audio(config, ctx.room, session)
        await setup_audio_recording(config, ctx.room.name)

    # Setup idle call monitoring if enabled - AFTER session is started
    if config.get("idle_call_hungup", False) and modality == "voice":
        task_refs["idle_watcher"] = asyncio.create_task(
            idle_call_watcher(session)
        )

    # Setup conversation tracking (transcript persistence was set up earlier)
    if hasattr(session, 'on'):
        conversation_handler = transcript_manager.create_conversation_handler()
        session.on("conversation_item_added", conversation_handler)