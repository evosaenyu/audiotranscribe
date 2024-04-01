import streamlit as st
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
import threading
from clients import openai_client as client 
import text_to_speech as tts

messages = [
            {"role": "system", 
		"content": "You are a children's storyteller embodied in a device that shows images while telling the story. Be creative and come up with interesting plots that teach kids a moral lesson or two." }]
   
def send_query(messages):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
    )
    returnMessage = completion.choices[0].message.content
    return {"role":completion.choices[0].message.role, "content":returnMessage} 

def main():

    audio_bytes = audio_recorder(text="")
    if audio_bytes:
        with open("audio.wav", "wb") as f:
            f.write(audio_bytes)
    st.write("Storytime")
    # Adding a textarea
    # Adding the first textarea
    user_input1 = st.text_area("Enter your text here:")
    #Pass the audio file to speech recognizer
    r = sr.Recognizer()
    with sr.AudioFile("audio.wav") as source:
        audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data)
            #write the text into the user_input1
            # Display the text
            with st.chat_message("user"):
                st.write(text)
            messages.append({"role": "user", "content": text})
            response = send_query(messages)
            with st.chat_message("assistant"):
                st.write(response["content"])
            messages.append({"role":response["role"], "content":response["content"]})
            tts.generate_speech_audio(response["content"], "speech.mp3")
            #Play speech audio on streamlit webapp
            tts.play_speech_audio("speech.mp3")

        except Exception as e:
            with st.chat_message("assistant"):
                st.write("Sorry, I did not get that. Please try again.")


    st.divider()

    btns = st.container()
        
if __name__ == "__main__":
    main()