import sys
from google.cloud import texttospeech

CLIENT = texttospeech.TextToSpeechClient()
VOICE = texttospeech.VoiceSelectionParams(
        language_code='de-DE',
        name='de-DE-Wavenet-B')
AUDIO_CONFIG = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3)

def tts(text, filename):
    try:
        out = open(filename, 'r')
        out.close()
    except FileNotFoundError: # only generate speech if the text is new
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = CLIENT.synthesize_speech(input=synthesis_input, voice=VOICE, audio_config=AUDIO_CONFIG)
        with open(filename, 'wb') as out:
            out.write(response.audio_content)

print(sys.argv[1], sys.argv[2])
tts(sys.argv[1], sys.argv[2])
