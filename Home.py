import streamlit as st
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
import scripts.text_to_speech as tts
from langchain_core.messages import HumanMessage

import os 
import time 
from components.slide_show import slideshow_swipeable
import asyncio 
import websockets  
from dotenv import load_dotenv
import json 

load_dotenv(os.path.join(os.getcwd(),'..','.env'))

def msg_to_ws_json(msg):
    return json.dumps(msg)

# def handle_dialogue(input_callback):
#     """take user input, and run the callback everytime we have new user input""" 
#     r = sr.Recognizer()
#     text = ''
#     if os.path.exists('audio.wav'):
#         try:
#             with sr.AudioFile("audio.wav") as source:
#                 audio_data = r.record(source)
#                 text = r.recognize_google(audio_data)
#         except:
#             pass 
#     try:
#         with st.chat_message("user"):
#             st.write(text)
#         success,response = input_callback(text)
#         return success,response
#     except Exception as e:
#         with st.chat_message("assistant"):
#             st.write(f"Sorry, I did not get that. Please try again.: {e}")    
#     return False,False
    

async def main():
    # print("running main")
    # audio_bytes = audio_recorder(text="")
    # if audio_bytes:
    #     with open("audio.wav", "wb") as f:
    #         f.write(audio_bytes)
    #     images = run_agent()
    #     slideshow_swipeable(images)
    st.write("Storyteller Demo")
    response = None
    prompt = st.chat_input("your response")
    previous = "_" 
    async with websockets.connect(os.getenv("WS_CONN")) as websocket:
        while not response or not response["generation"]:
            response = await websocket.recv()
            print(response)
            response = json.loads(response)
            
            with st.chat_message("ai"):
                st.write(response["response"])

            if prompt and previous != prompt:
                with st.chat_message("You"):
                    st.write(prompt)
                _ = await websocket.send(msg_to_ws_json({"response": prompt}))
                previous = prompt

    print(response)

    # with st.chat_message("ai"):
    #     st.write(response["response"])

            


    # Adding a textarea
    # Adding the first textarea
    #Pass the audio file to speech recognizer
    # audio_md = tts.generate_audio_markdown('speech.mp3')
    # st.markdown(audio_md,unsafe_allow_html=True)
    
    st.divider()
    btns = st.container()


  

#def run_agent():
    # r = sr.Recognizer()


    # while not initialized:
    #     with st.chat_message("assistant"):
    #         st.write(response['question'])
    #     initialized,response= handle_dialogue(agent.initializer_iterate)
    #     time.sleep(0.2)
    # print(response['imageDescriptions'])
    # images = agent.get_story_images(response['imageDescriptions'])
    # with st.chat_message("assistant"):
    #     st.write(' '.join(response['plotDescriptions']))
    # tts.generate_speech_audio(' '.join(response['plotDescriptions']),'speech.mp3')
    # return images
        
if __name__ == "__main__":
    asyncio.run(main())