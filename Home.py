import streamlit as st
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
import threading
from scripts.clients import openai_client as client 
import scripts.text_to_speech as tts
from scripts.agents import StoryAgent 
import os 
import time 
from elements.slide_show import slideshow_swipeable

def handle_dialogue(input_callback):
    """take user input, and run the callback everytime we have new user input"""
    r = sr.Recognizer()
    text = ''
    if os.path.exists('audio.wav'):
        try:
            with sr.AudioFile("audio.wav") as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
        except:
            pass 
    try:
        with st.chat_message("user"):
            st.write(text)
        success,response = input_callback(text)
        return success,response
    except Exception as e:
        with st.chat_message("assistant"):
            st.write(f"Sorry, I did not get that. Please try again.: {e}")    
    return False,False
    

def main():

    audio_bytes = audio_recorder(text="")
    if audio_bytes:
        with open("audio.wav", "wb") as f:
            f.write(audio_bytes)
    st.write("give me a theme to write a story about")
    # Adding a textarea
    # Adding the first textarea
    #Pass the audio file to speech recognizer
    r = sr.Recognizer()
    agent = StoryAgent()
    initialized,response= handle_dialogue(agent.initializer_iterate)
    while not initialized:
        with st.chat_message("assistant"):
            st.write(response['question'])
        initialized,response= handle_dialogue(agent.initializer_iterate)
        time.sleep(0.2)

    images = agent.get_story_images(response['imageDescriptions'])
    slideshow_swipeable(images)
    with st.chat_message("assistant"):
        st.write(' '.join(response['plotDescriptions']))

    tts.generate_speech_audio(' '.join(response['plotDescriptions']),'speech.mp3')
    audio_md = tts.generate_audio_markdown('speech.mp3')
    st.markdown(audio_md,unsafe_allow_html=True)




    st.divider()

    btns = st.container()
        
if __name__ == "__main__":
    main()