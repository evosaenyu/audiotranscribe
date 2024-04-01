
import time 
from pygame import mixer


def play_speech_audio(file_path, interrupted, recognizer=None):
    if recognizer:
        recognizer.energy_threshold = recognizer.energy_threshold*2
        print(recognizer.energy_threshold)
    mixer.init()
    # Load the speech audio file
    mixer.music.load(file_path)
    
    # Play the speech audio file
    mixer.music.play()
    
    # Check periodically if playback should be interrupted
    while mixer.music.get_busy():
        if interrupted.is_set():
            mixer.music.stop()
            break
        time.sleep(0.1)  # Adjust the sleep time as needed
    mixer.music.unload()
    if recognizer:
        recognizer.energy_threshold = recognizer.energy_threshold//2
