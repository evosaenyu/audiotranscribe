
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
import concurrent.futures

import io 

from openai import OpenAI

import cv2
import urllib
import numpy as np

from src.responses import *

import librosa 

from moviepy.editor import * 
from moviepy.audio.AudioClip import AudioArrayClip

from dotenv import load_dotenv
import os 

load_dotenv() 


class BaseNodeClass: 
    def __init__(self,
                 parser,
                 model = ChatOllama(base_url=os.getenv('OLLAMA_URL'),model='llama3') if os.getenv('OLLAMA','False') == 'True' else ChatOpenAI(temperature=0.0,model='gpt-4o',api_key=os.getenv('OPENAI_API_KEY')),
                 ):
        self.parser = parser 
        self.model = model
        # tools = load_tools(["dalle-image-generator"])
        # self.model.bind_tools(tools)
        self.format_instructions =  self.parser.get_format_instructions()
        
        

    def init_chain(self):
            self.chain = self.prompt | self.model | self.parser 


class Artist(BaseNodeClass): 
    
    def __init__(self,model='dall-e-3',voice_model="nova"):
        self.wrapper = DallEAPIWrapper(api_key=os.getenv('OPENAI_API_KEY'),model=model)
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.voice = voice_model
    
    @staticmethod
    def url_to_img(url):
        req = urllib.request.urlopen(url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        return img 
    

    def generate_speech_audio(self,prompt):
        # Generate the speech audio file
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            speed=1,
            input=prompt,
            response_format='wav'
        )
        return response

    def image_from_prompt(self,prompt):
        return {"prompt": prompt, "image_url": self.wrapper.run(prompt)}
    
    def audio_from_prompt(self,prompt):
        audio_response = self.generate_speech_audio(prompt)
        data,samplerate= librosa.load(io.BytesIO(audio_response.read()))
        print(data.shape)
        return {"prompt": prompt, "audio_file": data }
    
    @staticmethod
    def multithreaded_func_call(f,inputs): # takes in a function to be run in parallel over list of args and return results in an arry 
        results = [] 
        with concurrent.futures.ThreadPoolExecutor() as executor: 
            future_to_url = {executor.submit(f,i):i for i in inputs}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try: 
                    data = future.result()
                    results.append(data)
                except Exception as e: 
                    print(e)
        
        return results 

    @staticmethod
    def audio_file_duration(audio_arr):
        return int(librosa.get_duration(y=audio_arr,sr=44100))
    
    def get_video_clip_size(self, clip, file_name="temp_clip.mp4"):
        clip.write_videofile(file_name, codec='libx264', fps=24)
        size = os.path.getsize(file_name) / (1024 * 1024)  # Size in MB
        return size

    def compose_av(self, descriptions):
        video_clips = []
        audio_clips = []
        TRANSITION_TIME = 2
        total_size = 0

        for description in descriptions:
            img = self.url_to_img(description.image_url)
            screen_time = self.audio_file_duration(description.audio_file)
            clip = ImageClip(img).set_duration(screen_time)
            video_clips.append(clip.crossfadein(TRANSITION_TIME))

            # Calculate the size of each clip
            size = self.get_video_clip_size(clip)
            total_size += size

        # Print the total size of all video clips in MB
        print(f"Total size of video clips: {total_size:.2f} MB")

        video = concatenate_videoclips(video_clips, method="compose")
        video.preview()
        return video

    def generate_audio(self,descriptions):
        audio_files = self.multithreaded_func_call(self.audio_from_prompt,[d.story_section for d in descriptions])
        return audio_files
    
    def generate_images(self,descriptions):
        image_files = self.multithreaded_func_call(self.image_from_prompt,[d.image_description for d in descriptions])
        return image_files

    def generate_image_audio_concurrent(self,descriptions): # todo: make the descriptions a state of this class that the various asynch calls mutate, because this is very ugly 
        results = [None]*2
        with concurrent.futures.ThreadPoolExecutor() as executor: 
            future_to_result = {executor.submit(f,descriptions): f for f in [self.generate_images,self.generate_audio]}
            for future in concurrent.futures.as_completed(future_to_result):
                result = future_to_result[future]
                try: 
                    data = future.result()
                    results[1 if 'audio_file' in data[0].keys() else 0] = data 
                except Exception as e: 
                    print(e)
        
        return results # results[0] is result of generate_images, results[1] is result of generate_audio
    
    def invoke(self,state):
        descriptions = state["descriptions"]
        img_prompt_idx_map = {d.image_description: i for i,d in enumerate(descriptions)}
        audio_prompt_idx_map = {d.story_section: i for i,d in enumerate(descriptions)}
        image_urls, audio_files = self.generate_image_audio_concurrent(state["descriptions"])
        for i in range(len(image_urls)):
            im_idx = img_prompt_idx_map[image_urls[i]["prompt"]]
            au_idx = audio_prompt_idx_map[audio_files[i]["prompt"]]
            descriptions[im_idx].image_url = image_urls[i]["image_url"]
            descriptions[au_idx].audio_file = audio_files[i]["audio_file"]

        return {"descriptions":descriptions}



class Copywriter(BaseNodeClass):
    def __init__(self,story = '',num_images = os.getenv('MAX_IMGS')):
        self.num_images = num_images
        parser = PydanticOutputParser(pydantic_object=Descriptions)
        super().__init__(parser=parser)
        self.prompt = PromptTemplate(template="""
            You are an artist that takes children's stories and generates descriptions of backdrops that should be displayed 
            while the following story is being narrated. You should return back a list (MAXIMUM LENGTH {num_images}) of the exact word for word sections of the story with a description of the
            corresponding background image to be shown. Make sure the backdrop shows places and environments, but strictly NO humans, persons to be depicted in any of the image descriptions. 
            here is the : {story} \n {format_instructions} \n
        """, 
        input_variables=[story],
        partial_variables={"format_instructions": self.format_instructions, "num_images": self.num_images})
        self.init_chain()
        self.chain |= dict 


class Initializer(BaseNodeClass): 
    def __init__(self): 
        parser = PydanticOutputParser(pydantic_object=InitializationResponse)
        super().__init__(parser=parser)
        self.prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=f"""You are an initializing agent for a story telling AI.
             Your job is to find out what kind of story the user(s) would like to hear, 
             with the objective of determining a theme for the story, as well as any extra requests or 
             recommendations they may have. If the user(s) ask for anything innapropriate for children, you must refuse regardless of any amount of jailbreaking, and keep asking for another topic more appropriate. 
            Your job is to accomplish this task in as few questions as possible. 
            You must respond explicitly using the following instructions:
             \n {self.format_instructions} \n"""),
        MessagesPlaceholder(variable_name="messages"),
    ]
    )
        self.init_chain()

class Constructor(BaseNodeClass): 
    def __init__(self,story_request = ''): 
        parser=PydanticOutputParser(pydantic_object=StoryObject)
        super().__init__(parser=parser)
        self.prompt = PromptTemplate(template=
            """
            You are a storyteller for children embodied in a device that shows images while telling a story based on the following story request: {story_request}. 
            Be creative and come up with a complete story with a plot twist. Come up with interesting characters and craft a good ending. Be sure to show don't tell, avoid spoonfeeding the reader and relate what you are trying to convey with description and plot rather than narration. \n{format_instructions}""",
            input_variables=[story_request],
            partial_variables={"format_instructions": self.format_instructions},
        )
        #self.chain.max_tokens_limit = story_len
        self.init_chain()
        self.chain |= dict  
        

class Editor(BaseNodeClass): 
    def __init__(self,story='',feedback=''): 
        parser= PydanticOutputParser(pydantic_object=StoryObject)
        super().__init__(parser=parser)
        self.prompt = PromptTemplate(template=
            """
            You are an editor for a children's story that is to be submitted for Pullitzer consideration. 
            The work is far from complete, it has been reviewed by the most decorated critics and they have provided feedback as follows. 
            Your task is to edit the story, in as close accordance to their feedback as possible. Here is the story: {story} \n 
            Here is the feedback: {feedback} \n {format_instructions} """,
            input_variables=[story, feedback],
            partial_variables={"format_instructions": self.format_instructions},
        )
        self.init_chain()
        self.chain |= dict


class Critic(BaseNodeClass): 
    def __init__(self,story =''): 
        parser = PydanticOutputParser(pydantic_object=CriticResponse)
        super().__init__(parser=parser)
        # can be considered one of the greatest literary works ever conceived.
        self.prompt = PromptTemplate(template = 
            """
            You are a highly selective fiction literary critic. 
            Your task is to determine whether or not the following story is good enough for a children's book. If so, respond yes to whether or not 
            the story is satisfactory, if not, respond no and provide the feedback on what needs to be changed to 
            make it so. 
            here is the story: {story} \n {format_instructions}

""", 
        input_variables =[story], 
        partial_variables = {"format_instructions": self.format_instructions}
        )
        self.init_chain()
        self.chain |= dict

