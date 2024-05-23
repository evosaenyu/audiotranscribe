
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
import concurrent.futures

import cv2
import urllib
import numpy as np

from src.responses import *

from moviepy.editor import * 

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
    
    def __init__(self,model='dall-e-3'):
        self.wrapper = DallEAPIWrapper(api_key=os.getenv('OPENAI_API_KEY'),model=model)
    
    @staticmethod
    def url_to_img(url):
        req = urllib.request.urlopen(url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        return img 
    
    def image_from_prompt(self,prompt):
        return {"prompt": prompt, "image_url": self.wrapper.run(prompt)}
    
    def parallel_image_calls(self,prompts):
        results = [] 
        with concurrent.futures.ThreadPoolExecutor() as executor: 
            future_to_url = {executor.submit(self.image_from_prompt,prompt):prompt for prompt in prompts}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try: 
                    data = future.result()
                    results.append(data)
                except Exception as e: 
                    print(e)
        
        return results 

    def compose_av(self,descriptions):
        clips = []
        for description in descriptions:
            img = self.url_to_img(description.image_url)
            clip = ImageClip(img).set_duration(3)
            clips.append(clip.crossfadein(2))
        
        video = concatenate(clips,method="compose")
        #video.preview()
        return video


    
    def generate_images_parallel(self,descriptions):
        prompt_idx_map = {d.image_description: i for i,d in enumerate(descriptions)}
        prompt_image_pairs = self.parallel_image_calls([d.image_description for d in descriptions])
        for res in prompt_image_pairs:
            idx = prompt_idx_map[res["prompt"]]
            descriptions[idx].image_url = res["image_url"]
        return descriptions 
    
    def invoke(self,state):
        updated = self.generate_images_parallel(state["descriptions"])
        return {"descriptions":updated}



class Copywriter(BaseNodeClass):
    def __init__(self,story = '',num_images =7):
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

