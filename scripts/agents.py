
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os 
from typing import List

load_dotenv() 


class BaseNodeClass: 
    def __init__(self,model='gpt-4o',parser =  StructuredOutputParser):
        self.parser = parser 
        self.model = ChatOpenAI(temperature=0,model=model,api_key=os.getenv('OPENAI_API_KEY')) 
        self.output_parser = self.parser.from_response_schemas(self.schemas)
        self.format_instructions =  self.output_parser.get_format_instructions()

    def init_chain(self):
            self.chain = self.prompt | self.model | self.output_parser 

class Initializer(BaseNodeClass): 
    def __init__(self,context=''): 
        self.schemas = [
            ResponseSchema(name = "story request", description = "the object that has a field representing each part of the user's request. At minimum it should have the theme set to a certain value"), 
            ResponseSchema(name = "question", description = "the question you'd like to ask the user, if any"), 
            ResponseSchema(name ="terminating", description = "flag to know once you have enough information to provide the theme, yes or no only.")]
        super().__init__()
        self.prompt = PromptTemplate(
            template="""You are an initializing agent for a story telling AI.
             Your job is to talk to the user and ask them what kind of story they would like to hear, 
             with the objective of determining a theme for the story, as well as any extra requests or recommendations they may have. Your job is to do so in as few questions as possible. \n {format_instructions} \n context: {context}""",
             input_variables = [context], 
             partial_variables = {'format_instructions': self.format_instructions}
        )
        self.init_chain()

        


class Constructor(BaseNodeClass): 
    def __init__(self,story_request = '',story_len=10000): 
        self.schemas = [
            ResponseSchema(
                name="story",
                description="the complete story",
            )]
        super().__init__()
        self.prompt = PromptTemplate(template=
            """
            You are a storyteller for children embodied in a device that shows images while telling a story based on the following story request: {story_request}. 
            Be creative and come up with a complete story with a plot twist and moral revelation at the end. Come up with interesting characters and craft a good ending. Limit the story token length to {story_len}. \n{format_instructions}""",
            input_variables=[story_request,story_len],
            partial_variables={"format_instructions": self.format_instructions},
        )
        self.init_chain()
        #self.chain.max_tokens_limit = story_len

        

class Editor(BaseNodeClass): 
    def __init__(self,story='',feedback=''): 
        self.schemas = [
                    ResponseSchema(
                        name="story",
                        description="the complete story",
                    )
                ] 
        super().__init__()
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


class Critic(BaseNodeClass): 
    def __init__(self,story =''): 
        self.schemas = [
            ResponseSchema( 
                name = "satisfactory", 
                description = "single word yes or no whether or not this story is satisfactory"
            ), 
            ResponseSchema(
                name = "feedback", 
                description = "a detailed description outlining which parts of the story needs to be improved if at all"
            )
        ]
        super().__init__()
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



class StoryRuntime: 
    def __init__(self,model = 'gpt-4o',story_len = 10000):

        self.model = ChatOpenAI(temperature=0,model=model,api_key=os.getenv('OPENAI_API_KEY'))

        
        # theme_response = self.init_chain.invoke({'user_response': ''})

        # self.history = [theme_response]
        self.history = []
        self.story_len = story_len # token limit for the story 


    def initializer_iterate(self,user_response):
        """
        return a finished flag, and the last AI response
        """
        self.history.append({'user_response': user_response})
        theme_response = self.init_chain.invoke({'context': self.history})
        self.history.append(theme_response)
        if self.history[-1]['terminating'].lower() == 'no':
            return False,theme_response
        
        story_response = self.main_story_startup(theme_response['theme'])
        return True,story_response

    

    # @staticmethod
    # def get_story_images(image_prompts):
    #     urls = []
    #     for p in image_prompts:
    #         prompt = f"""Generate an image for the given prompt.
    #         Make sure the image generated is consistent in style and content with the previously generated image.
    #         Scene: {p}"""
    #         print(p)
    #         urls.append(generate_image(prompt)[0])
    #     return urls 
     
        

    def iterate(self,response):
        self.history.append(self.main_chain.invoke({'user_response': response}))
    
    def retrieve_latest(self):
        return self.history[-1]

    
    def question_answer_mode(self):
        pass 

    def response_mode(self): 
        pass 

    def generate_image(self):
        pass 





#### user -> initializer -> constructor -> critic -> editor  
#####                                             -> user 
