import time
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
import queryDALLE
import url_to_image
import threading
import cv2
from matplotlib import pyplot as plt
from text_to_speech import say_something

from scripts.agents import get_story_chain 



storyDict = [
        {"theme": ""}
        ]

def demo():
    chain = get_story_chain()
    response = chain.invoke(storyDict)
    tell_story(response)

def tell_story(response):

    story_length = len(response["imageDescriptions"])
    global image_arr 
    image_arr = [None]*story_length
    image_read_thread = threading.Thread(target=populate_image_arr,args=[response["imageDescriptions"]])
    image_read_thread.start()

    for i in range(story_length):
        while image_arr[i] is None:
            time.sleep(0.4)
        #render
        render(image_arr[i])
        print(response["plotDescriptions"][i])
        read(response["plotDescriptions"][i])

def populate_image_arr(image_prompts):
    prompt = f"""Each of the following descriptions represents a scene in a story. 
    Generate an image for each of the following descriptions. 
    Make sure the images are cohesive in style and that characters look consistent. 
    Return the images in the same order as the scene they are meant to correspond with.
    Scenes: {[f"\nScene: " + p for p in image_prompts]}"""
    print([p for p in image_prompts])
    urls = queryDALLE.generate_image(prompt, len(image_prompts))
    for i in range(len(urls)):
        image_arr[i] = url_to_image.download_img(urls[i])


def render(image):
    # Show image
    cv2.imshow('background', image)
    cv2.waitKey(1)

def read(plot):
    say_something(plot)

demo()