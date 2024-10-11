from elevenlabs import ElevenLabs, VoiceSettings
from config import ELEVENLABS_API_KEY
from io import BytesIO

# Initialize ElevenLabs client
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def text_to_speech_stream(text, voice_id):
    """
    Convert text to speech using ElevenLabs API and return an audio stream.
    """
    response = eleven_client.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.5,
            use_speaker_boost=True,
        ),
    )
    audio_stream = BytesIO()
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)
    audio_stream.seek(0)
    return audio_stream
