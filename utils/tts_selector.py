from livekit.plugins import (  # playai, azure; neuphonic,
    aws,
    cartesia,
    deepgram,
    elevenlabs,
    google,
    openai,
)

def __get_tts(config):
    which_tts = config["TTS"]
    if which_tts == "elevenlabs":
        from dataclasses import dataclass

        @dataclass
        class VoiceSettings:
            stability: float  # [0.0 - 1.0]
            similarity_boost: float  # [0.0 - 1.0]
            style: float | None = None  # [0.0 - 1.0]
            speed: float | None = 1.0  # [0.8 - 1.2]
            use_speaker_boost: bool | None = False

        @dataclass
        class Voice:
            id: str
            name: str
            category: str
            settings: VoiceSettings | None = None

        male_voice = Voice(
            id="1qZOLVpd1TVic43MSkFY",
            name="Amritanshu Professional voice",
            category="professional",
            settings=VoiceSettings(
                stability=0.5,
                speed=1.0,
                similarity_boost=0.6,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        male_voice = Voice(
            id="xnx6sPTtvU635ocDt2j7",
            name="Chinmay",
            category="professional",
            settings=VoiceSettings(
                stability=0.5,
                speed=1.0,
                similarity_boost=0.6,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        female_voice = male_voice
        # female_voice = Voice(
        #     id="ZUrEGyu8GFMwnHbvLhv2",
        #     name="Monika",
        #     category="professional",
        #     settings=VoiceSettings(
        #         stability=0.4,
        #         speed=1,
        #         similarity_boost=0.6,
        #         style=0,
        #         use_speaker_boost=False,
        #     ),
        # )

        return elevenlabs.TTS(model="eleven_flash_v2_5", voice=female_voice)
        