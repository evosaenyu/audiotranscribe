import argparse
import os
import numpy as np
import speech_recognition as sr
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform
from pydub import AudioSegment
import threading 
from langchain_core.messages import HumanMessage, AIMessage


import queryGPT
def main(messages):
    parser = argparse.ArgumentParser()
    parser.add_argument("--energy_threshold", default=1000, help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=10, help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=4, help="How much empty space between recordings before we consider it a new line in the transcription.", type=float)
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse', help="Default microphone name for SpeechRecognition. Run this with 'list' to view available Microphones.", type=str)
    args = parser.parse_args()

    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = args.energy_threshold

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    if 'linux' in platform:
        mic_name = args.default_microphone
        if not mic_name or mic_name == 'list':
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")
            return
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        source = sr.Microphone(sample_rate=16000)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = ['']

    with source as mic:
        recognizer.adjust_for_ambient_noise(mic)
        
        # messages = [
        #     {"role": "system", 
		# "content": 
        # """
        # You are a children's storyteller embodied in a device that shows images while telling the story. 
        # Be creative and come up with interesting plots that teach kids a moral lesson or two. 
        # Formulate the story in the following format: 
        # - Image Description: your description of the image here
        # - Plot Description: your narration here
        # Generate a story in the form of the above bullet point pairs, and instruct the user to say 'next' to continue the story.
        # Your response will be parsed by a function, so make sure it adheres to the above-mentioned standard.
        # """ }
        # ]

        while True:
            try:
                now = datetime.utcnow()
                # Record audio from the microphone
                audio = recognizer.listen(mic, timeout=record_timeout, phrase_time_limit=phrase_timeout)

                # If audio is detected, process it
                if audio:
                    phrase_complete = True

                    # Convert audio data to text
                    text=""
                    try:
                        text = recognizer.recognize_google(audio)
                    except:
                        continue

                    # If we detected a pause between recordings, add a new item to our transcription.
                    # Otherwise, edit the existing one.
                    if phrase_complete:
                        transcription.append(text)
                    else:
                        transcription[-1] = text

                    # Clear the console to reprint the updated transcription.
                    os.system('cls' if os.name == 'nt' else 'clear')
                    for line in transcription:
                        print(line)
                    return transcription[-1]
                    # messages.append(queryGPT.send_query(messages))
                    # # Flush stdout.
                    # print('', end='', flush=True)
                else:
                    # Infinite loops are bad for processors, must sleep.
                    sleep(0.25)
            except KeyboardInterrupt:
                break
        

    print("\n\nTranscription:")
    for line in transcription:
        print(line)

if __name__ == "__main__":
    main()
