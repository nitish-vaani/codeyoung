"""
AI model configuration and initialization.
Handles LLM, TTS, and other AI model setup.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass
from livekit.plugins import elevenlabs, deepgram, openai, cartesia, aws, silero
from .config_manager import config_manager
from .logging_config import get_logger

logger = get_logger(__name__)
config = config_manager.config
def get_openai_llm():
    """Get properly configured OpenAI LLM"""
    api_key = config_manager.get_openai_api_key()
    
    try:
        # For project-specific keys, we might need to handle differently
        if api_key.startswith("sk-proj-"):
            logger.info("Using project-specific OpenAI API key")
        
        # Use basic configuration without unsupported parameters
        llm_instance = openai.LLM(
            # model="gpt-3.5-turbo",  # More reliable and supported model
            model="gpt-4o-mini",  # Use gpt-4o for better performance
            api_key=api_key
        )
        
        logger.info("Successfully created OpenAI LLM instance")
        return llm_instance
        
    except Exception as e:
        logger.error(f"Failed to create OpenAI LLM: {e}")
        raise

def get_tts(config: Dict[str, Any], voice_config: Dict[str, Any] = None):
    """Get configured TTS instance based on config"""
    which_tts = config["TTS"]
    which_voice=voice_config.get("voice", "Default") if voice_config else "Default"


    if which_tts == "cartesia":
        harry = "3dcaa773-fb1a-47f7-82a4-1bf756c4e1fb"
        carson = "4df027cb-2920-4a1f-8c34-f21529d5c3fe"
        happy_carson = "96c64eb5-a945-448f-9710-980abe7a514c"
        orion = "701a96e1-7fdd-4a6c-a81e-a4a450403599"
        polite_man = "ee7ea9f8-c0c1-498c-9279-764d6b56d189"
        american_voiceover_man = "7fe6faca-172f-4fd9-a193-25642b8fdb07"
        david = "da69d796-4603-4419-8a95-293bfc5679eb"
        ayush="791d5162-d5eb-40f0-8189-f19db44611d8"
        help_desk = "39b376fc-488e-4d0c-8b37-e00b72059fdd"
        customer_service = "2a4d065a-ac91-4203-a015-eb3fc3ee3365"
        devansh = "1259b7e3-cb8a-43df-9446-30971a46b8b0"
        customer_support_lady = "829ccd10-f8b3-43cd-b8a0-4aeaa81f3b30"
        sarah = "bf0a246a-8642-498a-9950-80c35e9276b5"
        savannah = "78ab82d5-25be-4f7d-82b3-7ad64e5b85b2"
        janvi = "7ea5e9c2-b719-4dc3-b870-5ba5f14d31d8"

        def get_voice(voice_name: str):
            voices = {
                "English US(M)-1": david,
                "English US(M)-2": help_desk,
                "English US(M)-3": customer_service,
                "English Indian(M)-1": devansh,
                "English US(F)-1": sarah,
                "English US(F)-2": savannah,
                "English US(F)-2": customer_support_lady,
                "English Indian(F)-1": janvi,
                "Default": help_desk,
            }
            return voices.get(voice_name, sarah)

        def manipulate_speed(list_view):
            import random
            # choose a random value from the list and return it
            if not list_view:   # handle empty list safely
                return None
            return random.choice(list_view)

        return cartesia.TTS(
            model="sonic-2-2025-03-07",
            voice=get_voice(which_voice),
            speed=-0.25,
            language="hi",
            emotion=["positivity:highest", "curiosity:highest"],
        )
    
    if which_tts == "aws":
        return aws.TTS()

    if which_tts == "elevenlabs":
        
        #Male Voices
        eric = "9T9vSqRrPPxIs5wpyZfK"
        indian_male_1 = "3gsg3cxXyFLcGIfNbM6C"
        american_male_1 = "MXGyTMlsvQgQ4BL0emIa"
        american_male_2 = "scOwDtmlUjD3prqpp97I"

        #Female Voices
        indian_female_1 = "MwUMLXurEzSN7bIfIdXF"
        american_female_1 = "56AoDkrOh6qfVPDXZ7Pt"
        american_female_2 = "NHRgOEwqx5WZNClv5sat"
        monika = "2bNrEsM0omyhLiEyOwqY"

        def get_voice(voice_name: str):
            voices = {
                "English US(M)-1": american_male_1,
                "English US(M)-2": american_male_2,
                "English US(M)-3": eric,
                "English Indian(M)-1": indian_male_1,
                "English US(F)-1": american_female_1,
                "English US(F)-2": american_female_2,
                "English US(F)-2": customer_support_lady,
                "English Indian(F)-1": indian_female_1,
                "Default": monika,
            }
            return voices.get(voice_name.lower(), devansh)



        @dataclass
        class VoiceSettings:
            stability: float
            similarity_boost: float
            style: float | None = None
            speed: float | None = 1.0
            use_speaker_boost: bool | None = False

        voice_setting = VoiceSettings(
            stability=0.5,
            speed=1.0,
            similarity_boost=0.6,
            style=0.0,
            use_speaker_boost=True,
        )
        eric_voice_id = "cjVigY5qzO86Huf0OWal"
        chinmay_voice_id = "xnx6sPTtvU635ocDt2j7"
        return elevenlabs.TTS(
            model="eleven_flash_v2_5", 
            voice_settings=voice_setting, 
            voice_id=chinmay_voice_id
        )

    if which_tts == "deepgram":
        return deepgram.TTS()

def get_stt_instance():
    """Get configured STT instance"""
    # from ..prompts.boosted_keywords import keywords_to_boost
    return deepgram.STT(
        model="nova-3", 
        language="multi"
    )

def get_vad_instance():
    """Get configured VAD instance"""
    return silero.VAD.load()