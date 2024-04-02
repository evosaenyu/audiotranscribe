import streamlit as st
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
import threading
from scripts.clients import openai_client as client 
import scripts.text_to_speech as tts
from scripts.agents import StoryAgent 


def send_query(messages):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
    )
    returnMessage = completion.choices[0].message.content
    return {"role":completion.choices[0].message.role, "content":returnMessage} 

def handle_dialogue(input_callback):
    """take user input, and run the callback everytime we have new user input"""
    r = sr.Recognizer()
    with sr.AudioFile("audio.wav") as source:
        audio_data = r.record(source)
    try:
        text = r.recognize_google(audio_data)
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
    initialized = False 
    while not initialized:
        initialized,response= handle_dialogue(agent.initializer_iterate)

    with st.chat_message("assistant"):
        st.write(' '.join(response['plotDescriptions']))

    tts.generate_speech_audio(' '.join(response['plotDescriptions']),'speech.mp3')
    audio_md = tts.generate_audio_markdown('speech.mp3')
    st.markdown(audio_md,unsafe_allow_html=True)




    st.divider()

    btns = st.container()
        
if __name__ == "__main__":
    main()