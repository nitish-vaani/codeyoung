import os
from typing import Dict, Any
from livekit import api
from livekit.agents import (AudioConfig, BackgroundAudioPlayer, BuiltinAudioClip, 
                           AgentSession, RoomInputOptions)
from livekit.plugins import noise_cancellation
from livekit.plugins.turn_detector.english import EnglishModel
from .ai_models import get_openai_llm, get_tts, get_stt_instance, get_vad_instance
from .logging_config import get_logger
from .data_entities import UserData

logger = get_logger(__name__)

def prewarm_session(proc):
    """Prewarm function for session initialization"""
    proc.userdata["bg_audio_config"] = {
        "ambient": [AudioConfig(BuiltinAudioClip.OFFICE_AMBIENCE, volume=1)],
        "thinking": [
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.2),
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.2),
        ],
    }

def create_agent_session(userdata: UserData, config: Dict[str, Any], agent_config: Dict[str, Any]=None) -> AgentSession:
    """Create and configure an agent session with all required components for voice"""
    # Get AI model instances
    llm_instance = get_openai_llm()
    tts_instance = get_tts(config, voice_config=agent_config if agent_config else None)
    stt_instance = get_stt_instance()
    vad_instance = get_vad_instance()
    
    # Create session with all components
    session = AgentSession[UserData](
        stt=stt_instance,
        llm=llm_instance,
        tts=tts_instance,
        vad=vad_instance,
        turn_detection=EnglishModel(),
        userdata=userdata
    )
    
    logger.info("Voice agent session created successfully")
    return session

class ChatSession:
    """Chat session wrapper for chat modality"""
    
    def __init__(self, userdata: UserData, config: Dict[str, Any], agent_config: Dict[str, Any] = None):
        self.userdata = userdata
        self.config = config
        self.agent_config = agent_config
        self.llm_instance = get_openai_llm()
        self._agent = None
        self._room = None  # Store room reference
        self._event_handlers = {}
        
        logger.info("Chat session created successfully")
    
    async def start(self, room, agent, room_input_options=None):
        """Start the chat session"""
        self._room = room
        self._agent = agent
        
        # Set the room reference in the agent
        agent.set_room(room)  # We'll add this method
        
        # Set up participant handling
        @room.on("participant_connected")
        def on_participant_connected(participant):
            logger.info(f"Chat participant connected: {participant.identity}")
            agent.set_participant(participant)
        
        logger.info("Chat session started")
    
    def on(self, event_name: str, handler):
        """Register event handler"""
        self._event_handlers[event_name] = handler
        
    def emit_conversation_item(self, event):
        """Manually emit conversation item events for chat"""
        handler = self._event_handlers.get("conversation_item_added")
        if handler:
            handler(event)
        
    async def say(self, text: str):
        """Send text message in chat (equivalent to voice say)"""
        if self._agent:
            await self._agent.send_message(text, "text")
    
    async def generate_reply(self, instructions: str):
        """Generate a reply based on instructions"""
        if self._agent:
            await self._agent.send_message(f"Processing: {instructions}", "text")



def create_chat_session(userdata: UserData, config: Dict[str, Any], agent_config: Dict[str, Any] = None) -> ChatSession:
    """Create and configure a chat session"""
    session = ChatSession(userdata, config, agent_config)
    logger.info("Chat session configured successfully")
    return session

async def setup_background_audio(config: Dict[str, Any], room, session) -> BackgroundAudioPlayer:
    """Setup background audio if enabled in config (voice only)"""
    _ambient_sound = None
    _thinking_sound = None
    
    # Skip background audio for chat sessions
    if isinstance(session, ChatSession):
        logger.info("Skipping background audio for chat session")
        return None
        
    if (not config.get("bg_office_noise")) and (not config.get("bg_thinking_sound")):
        return None
    
    if config.get("bg_office_noise", False):
        _ambient_sound = AudioConfig(BuiltinAudioClip.OFFICE_AMBIENCE, volume=0.7)

    if config.get("bg_thinking_sound", False):
        _thinking_sound = [
                AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.2),
                AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.2),
            ]
        
    try:
        bg_audio = BackgroundAudioPlayer(
            # play office ambience sound looping in the background
            ambient_sound=_ambient_sound,
            # play keyboard typing sound when the agent is thinking
            thinking_sound=_thinking_sound,
        )
        await bg_audio.start(room=room, agent_session=session)
        logger.info("Background audio started successfully")
        return bg_audio
    except Exception as e:
        logger.warning(f"Failed to start background audio: {e}")
        return None

async def setup_audio_recording(config: Dict[str, Any], room_name: str):
    """Setup audio recording if enabled in config (voice only)"""
    if not config.get("record_audio", False):
        return
        
    try:
        req = api.RoomCompositeEgressRequest(
            room_name=room_name,
            layout="speaker",
            audio_only=True,
            segment_outputs=[
                api.SegmentedFileOutput(
                    filename_prefix=f"{room_name}",
                    playlist_name=f"{room_name}-playlist.m3u8",
                    live_playlist_name=f"{room_name}-live-playlist.m3u8",
                    segment_duration=5,
                    s3=api.S3Upload(
                        access_key=os.getenv("AWS_ACCESS_KEY"),
                        secret=os.getenv("AWS_SECRET_KEY"),
                        region=os.getenv("AWS_REGION"),
                        bucket=os.getenv("AWS_BUCKET"),
                    ),
                )
            ],
        )
        logger.info(f"Starting recording for room {room_name}")
        lkapi = api.LiveKitAPI()
        await lkapi.egress.start_room_composite_egress(req)
        logger.info("Audio recording started successfully")
    except Exception as e:
        logger.warning(f"Failed to start recording: {e}")

def get_room_input_options(mode: str) -> RoomInputOptions:
    """Get appropriate room input options based on mode"""
    if mode == "SIP":
        return RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
        )
    elif mode == "CHAT":
        # For chat, we don't need audio processing
        return RoomInputOptions()
    else:  # Console mode
        return RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        )