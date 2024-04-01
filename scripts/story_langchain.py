import time
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import queryDALLE
import url_to_image
import threading
import cv2
from matplotlib import pyplot as plt
from text_to_speech import say_something
import speech_recognizing_script
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os 

load_dotenv() 

def analyze_story(story):
    messages = []
    chat = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0.2,api_key=os.getenv('OPENAI_API_KEY'))
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""
                You are a helpful answering agent. Your job is to wait for the user to ask questions about the following story and then answer them. Limit your responses to under three sentences: \n{story}.\n 
                """,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    chain = prompt | chat
    while True:
        try:
            response = chain.invoke(
                {
                    "messages": messages
                }
            )
            print(response.content)
            say_something(response.content)
            messages.append(HumanMessage(content=speech_recognizing_script.main(messages=response)))
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    analyze_story("""
Once upon a time, in a magical land, there lived a young girl named Lily. She had curly red hair and a heart full of curiosity.
Lily loved to spend her days exploring the meadow near her home, filled with colorful flowers and buzzing bees. One day, as she was playing, she noticed a mischievous fox watching her from behind a tree.
The fox, named Finn, was intrigued by Lily's adventurous spirit and decided to approach her. They quickly became friends and spent many days playing together in the meadow.
As the days turned into nights, Lily and Finn would sit under the starry sky, sharing stories and dreams. Their friendship blossomed, and they became inseparable.""")