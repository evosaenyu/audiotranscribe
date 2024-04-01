import argparse
import os
from sys import platform
import threading
import speech_recognition as sr
from clients import openai_client as client 
import time
from pathlib import Path

from utils import play_speech_audio
global messages
global isRead
global audio_queue
messages = [
            {"role": "system", 
		"content": "You are an advanced AI game companion designed to play a wide range of games with users via an audio interface. Your role is to provide a dynamic, engaging, and interactive gaming experience, adapting to the user's preferences and game choices. You can play board games, trivia, word games, puzzles, and more. When a game is selected, you will explain the rules, manage game flow, and interact with the user as the game progresses. Use clear, descriptive language to convey visual elements and game states audibly. Encourage the user, provide hints if requested, and ensure a friendly, competitive spirit. Keep responses under three sentences when possible." }]
    
isRead = [True]
audio_queue = []
def generate_speech_audio(text, file_path):
    # Generate the speech audio file
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text
    )

    # Stream the audio response to the file path
    response.write_to_file(file_path)


def say_something(m_index, interrupted,recognizer,file_path=Path(__file__).parent / "speech.mp3", ):
    # Set up the file path for the MP3 file
    generate_speech_audio(messages[m_index]["content"], file_path)
    play_speech_audio(file_path, interrupted, recognizer)
    isRead[m_index] = True

def speech_recognition_thread(recognizer, microphone, interrupted, args):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            if not interrupted.is_set():
                try:
                    print("Listening for audio input...")
                    audio = recognizer.listen(source, timeout=args.record_timeout, phrase_time_limit=args.phrase_timeout)
                    if audio:
                        interrupted.set()  # Signal that new audio input was detected
                        text = recognizer.recognize_google(audio)
                        print(f"Recognized: {text}")
                        audio_queue.append(text)
                        # Add more logic here if needed to process the recognized text
                except Exception as e:
                    print(f"Could not process audio input: {str(e)}")
            time.sleep(0.2)

def query_thread():
    while True:
        if len(audio_queue):
            #Pop audio queries to the messages
            messages.append({"role": "user", "content": audio_queue.pop(0)})
            isRead.append(True)
            response = send_query(messages)
            messages.append(response)
            isRead.append(False)
            print("audio queue",audio_queue)
        time.sleep(0.5)
        

def send_query(messages):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
    )
    returnMessage = completion.choices[0].message.content
    return {"role":completion.choices[0].message.role, "content":returnMessage}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--default_microphone", default=None, help="Default microphone name for SpeechRecognition.", type=str)
    parser.add_argument("--energy_threshold", default=1000, help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=10, help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=4, help="How much empty space between recordings before we consider it a new line in the transcription.", type=float)
    args = parser.parse_args()

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = args.energy_threshold
    recognizer.dynamic_energy_threshold = False
    microphone = sr.Microphone()
    interrupted = threading.Event()
    # Start the speech recognition thread
    recognition_thread = threading.Thread(target=speech_recognition_thread, args=(recognizer, microphone, interrupted, args))
    recognition_thread.start()
    audio_queue_thread = threading.Thread(target=query_thread)
    audio_queue_thread.start()

    try:
        while True:
            # Example usage
            if not interrupted.is_set():
                if not isRead[-1]:
                    say_something(-1, interrupted, recognizer)
                else:
                    interrupted.clear()
                time.sleep(0.2)  # Pause between TTS playback, adjust as needed
            else:
                # Process new audio input or handle interruption
                interrupted.clear()  # Reset the flag for further listening
                # Further logic here to handle the interruption
                
    except KeyboardInterrupt:
        print("Exiting...")
    
    recognition_thread.join()
    audio_queue_thread.join()

if __name__ == "__main__":
    main()