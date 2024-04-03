import time

from pathlib import Path

from pygame import mixer

from scripts.clients import openai_client as client 
import base64

import os

def wait_for_unused_file(file_path):
    while True:
        try:
            with open(file_path, 'w') as f:
                # If the file can be opened successfully, it means it's unused
                return
        except PermissionError:
            # If the file is being used by another process, wait for a short duration
            time.sleep(0.1)

def generate_speech_audio(text, file_path):
    # Generate the speech audio file
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        speed=1,
        input=text
    )

    # Wait until the file is unused by another process
    #wait_for_unused_file(file_path)

    # Stream the audio response to the file path
    response.write_to_file(file_path)

def play_speech_audio(file_path):
    mixer.init()

    # Load the speech audio file
    mixer.music.load(file_path)

    # Play the speech audio file
    mixer.music.play()

    # Wait for the speech to finish playing
    while mixer.music.get_busy():
        continue
    mixer.music.unload()

def say_something(text,file_path = os.path.join(Path(__file__).parent, "speech.mp3")):
    # Set up the file path for the MP3 file
    

    generate_speech_audio(text, file_path)

    play_speech_audio(file_path)


def generate_audio_markdown(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        return md 
