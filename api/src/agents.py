
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAI as LCOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_community.llms import Ollama
from langchain_core.messages import SystemMessage

import concurrent.futures

import io 
from openai import OpenAI

from elevenlabs.client import ElevenLabs
from elevenlabs import play, stream, save

import cv2
import urllib
import numpy as np

from src.responses import *


from moviepy.editor import * 

from src.utils import * 

from dotenv import load_dotenv
import os 

load_dotenv(os.path.join(os.getcwd(),'..','.env'),override=True)

class BaseNodeClass: 
    def __init__(self,
                 parser,
                 model = Ollama(base_url=os.getenv('OLLAMA_URL'),model='llama3') if os.getenv("OLLAMA", "False") == 'True' else  ChatOpenAI(openai_api_key=os.getenv('OPENAI_API_KEY'),model='gpt-4-turbo')
                 ):
        self.parser = parser 
        self.model = model
        # tools = load_tools(["dalle-image-generator"])
        # self.model.bind_tools(tools)
        self.format_instructions =  self.parser.get_format_instructions()
        
        

    def init_chain(self):
            self.chain = self.prompt | self.model | self.parser 


class Director(BaseNodeClass): 
    
    def __init__(self,model='dall-e-3',voice_model="nova"):
        self.client = ElevenLabs(api_key=os.getenv('XI_API_KEY')) # Defaults to ELEVEN_API_KEY)
        self.voice = voice_model
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    @staticmethod
    def url_to_img(url):
        req = urllib.request.urlopen(url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        img= cv2.cvtColor(img , cv2.COLOR_BGR2RGB)
        return img 
    

    def generate_speech_audio(self,prompt,voice="Rachel"):
        # Generate the speech audio file
        filepath = generate_filepath('speech.mp3')

        _ = self.client.generate()
        audio = self.client.generate(
            text=prompt,
            voice="zCP9CbYitekLThIz72yG",
            model="eleven_turbo_v2"
            )
        save(audio,filepath)


        return filepath

    def image_from_prompt(self,prompt,model="dall-e-3"):
        response = self.openai_client.images.generate(
            model=model,
            prompt=prompt + "\n Safe image only, nothing that violates content policies.",
            style="natural",
            size="1024x1024",
            quality="standard",
            n=1,
            )

        return {"prompt": prompt, "image_url": response.data[0].url}
    
    def audio_from_prompt(self,prompt):
        audio_file = self.generate_speech_audio(prompt)
        return {"prompt": prompt, "audio_file": audio_file }

    def compose_av(self, descriptions):
        video_clips = []
        audio_clips = []
        TRANSITION_TIME = 2
        total_size = 0

        for description in descriptions:
            img = self.url_to_img(description.image_url)
            screen_time,sample_rate = audio_file_info(description.audio_file)
            audioclip = AudioFileClip(description.audio_file,fps=sample_rate) # change framerate to not be hardcoded 
            clip = ImageClip(img).set_duration(screen_time)
            audio_clips.append(audioclip)
            video_clips.append(clip.crossfadein(TRANSITION_TIME))

        track = concatenate_audioclips(audio_clips)
        video = concatenate_videoclips(video_clips, method="compose")
        video.audio = track 
        filepath = generate_filepath('generated.mp4')
        audio_filepath = generate_filepath('soundtrack.mp3')
        track.write_audiofile(audio_filepath,fps=sample_rate)
        #video.preview()
        #video.write_videofile(filepath,fps=24,threads=8)
        print("video compiled, writing")
        outfilepath = vidwrite(filepath,[f for f in video.iter_frames(fps=24)],audio_filepath,framerate=24)
        #compressed_filepath = compress_video(filepath,os.path.getsize(filepath)/50) # compression ratio
        #delete_tmpfile(filepath)
        total_size = get_video_clip_size(video)
        print(f"Total size of video clips: {total_size:.2f} MB") # Print the total size of all video clips in MB

        return outfilepath 

    def generate_audio(self,descriptions):
        audio_files = multithreaded_func_call(self.audio_from_prompt,[d.story_section for d in descriptions],workers=2) #rate limit from api 
        return audio_files
    
    def generate_images(self,descriptions):
        image_files = multithreaded_func_call(self.image_from_prompt,[d.image_description for d in descriptions],workers=8)
        return image_files

    def generate_image_audio_concurrent(self,descriptions): # todo: make the descriptions a state of this class that the various asynch calls mutate, because this is very ugly 
        results = [None]*2
        with concurrent.futures.ThreadPoolExecutor() as executor: 
            future_to_input = {executor.submit(f,descriptions): f for f in [self.generate_images,self.generate_audio]}
            for future in concurrent.futures.as_completed(future_to_input):
                input_func = future_to_input[future]
                data = future.result()
                results[1 if 'audio_file' in data[0].keys() else 0] = data 
    
        return results # results[0] is result of generate_images, results[1] is result of generate_audio
    
    def invoke(self,state):
        descriptions = state["descriptions"]
        image_urls, audio_files = self.generate_image_audio_concurrent(state["descriptions"])
        for i in range(len(image_urls)):
            descriptions[i].image_url = image_urls[i]["image_url"]
            descriptions[i].audio_file = audio_files[i]["audio_file"]

        return {"descriptions":descriptions}



class Copywriter(BaseNodeClass):
    def __init__(self,story_section = '',num_images = int(os.getenv('MAX_IMGS'))):
        self.num_images = num_images
        parser = PydanticOutputParser(pydantic_object=DescriptionItem)
        super().__init__(parser=parser)

        self.prompt = PromptTemplate(template="""
            You are an artist that takes excerpts from children's short stories and produces a descriptions of the backdrop that should be displayed while the story is being narrated. The description will be sent to an artist who will produce the images based on your description, so make sure to be as detailed as possible. Make sure the backdrop shows places and environments, but strictly NO humans, person, or writing,text, or captioning to be depicted in any of the image descriptions. 
            Here is the story excerpt: \n {story_section} \n {format_instructions} \n
            please output your response in the demanded json format
        """, 
        input_variables=[story_section],
        partial_variables={"format_instructions": self.format_instructions})
        self.init_chain()
    
    def splice_story(self,story):
        SPLIT_CHAR = '.'
        chunks = [s for s in story.split(SPLIT_CHAR) if len(s) > 1]
        if len(chunks) <= self.num_images:
            prompts = chunks 
        else:
            prompts = [(SPLIT_CHAR).join(c) for c in chunk_into_n(chunks,self.num_images)]
        
        return [p for p in prompts if len(p) > 1]
    
    def generate_descriptions(self,prompt):
        return self.chain.invoke({"story_section": prompt})
    
    def commission(self,state):
        prompts = self.splice_story(state["story"])
        image_descriptions = multithreaded_func_call(self.generate_descriptions,prompts)
        return {"descriptions": image_descriptions}



class Initializer(BaseNodeClass): 
    def __init__(self): 
        parser = PydanticOutputParser(pydantic_object=InitializationResponse)
        super().__init__(parser=parser)
        self.model = ChatOllama(base_url=os.getenv('OLLAMA_URL'),model='llama3') if os.getenv('OLLAMA','False') == 'True' else ChatOpenAI(temperature=0.0,model='gpt-4-turbo',api_key=os.getenv('OPENAI_API_KEY'))
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
            You are a storyteller for children embodied in a device that shows images while telling an ultra short story based on the following story request: {story_request}. 
            Be creative and come up with a complete extremely short story with a plot twist. Come up with interesting characters and craft a good ending. Be sure to show don't tell, avoid spoonfeeding the reader and relate what you are trying to convey with description and plot rather than narration. \n{format_instructions}""",
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
            You are an editor for a children's ultra short story that is to be submitted for Pullitzer consideration. 
            The work is far from complete, it has been reviewed by the most decorated critics and they have provided feedback as follows. 
            Your task is to edit the story, in as close accordance to their feedback as possible without unnecessarily increasing word count. Here is the story: {story} \n 
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
            Your task is to determine whether or not the following ultra short story is good enough for a children's book. If so, respond yes to whether or not 
            the story is satisfactory, if not, respond no and provide the feedback on what needs to be changed to 
            make it so. 
            here is the story: {story} \n {format_instructions}

""", 
        input_variables =[story], 
        partial_variables = {"format_instructions": self.format_instructions}
        )
        self.init_chain()
        self.chain |= dict

# def splice_story(story):
#     SPLIT_CHAR = '.'
#     chunks = [s for s in story.split(SPLIT_CHAR) if len(s) > 1]
#     if len(chunks) <= 7:
#         prompts = chunks 
#     else:
#         prompts = [(SPLIT_CHAR).join(c) for c in chunk_into_n(chunks,7)]
    
#     return [p for p in prompts if len(p) > 1]