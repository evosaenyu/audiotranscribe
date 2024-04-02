
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os 

load_dotenv() 


class StoryAgent: 
    def __init__(self):

        self.model = ChatOpenAI(temperature=0,api_key=os.getenv('OPENAI_API_KEY'))

        initializer_schemas = [
            ResponseSchema(name = "theme", description = "the requested story theme from the user, if determined yet"), 
            ResponseSchema(name = "question", description = "the question you'd like to ask the user, if any"), 
            ResponseSchema(name ="terminating", description = "flag to know once you have enough information to provide the theme, yes or no only.")]
        initializer_parser =StructuredOutputParser.from_response_schemas(initializer_schemas)
        init_format_instructions = initializer_parser.get_format_instructions() 
        initializer_prompt = PromptTemplate(template = """You are an initializing agent for a story telling AI.
             Your job is to talk to the user and ask them what kind of story they would like to hear, 
             with the objective of determining a theme for the story. Your job is to do so in as few questions as possible. \n {init_format_instructions} \n context: {context}""", 
             input_variables = ['context'], 
             partial_variables={"init_format_instructions": init_format_instructions},
            )
        self.init_chain =  initializer_prompt | self.model | initializer_parser
        # theme_response = self.init_chain.invoke({'user_response': ''})

        # self.history = [theme_response]
        self.history = []
 

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

    
    def main_story_startup(self,theme):     
        response_schemas = [
            ResponseSchema(
                name="imageDescriptions", 
                description="array of descriptions of the image relating to corresponding the plot description point"),
            ResponseSchema(
                name="plotDescriptions",
                description="array of detailed, descriptive narrations of the plot point.",
            )
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions() 
        prompt = PromptTemplate(
            
            template=
            """
            You are a storyteller for children embodied in a device that shows images while telling a story based on the theme of {theme}. 
            Be creative and come up with a complete story with a plot twist and moral revelation at the end. Come up with interesting characters and craft a good ending. Limit the number of story responses to 7. \n{format_instructions}""",
            input_variables=[theme],
            partial_variables={"format_instructions": format_instructions},
        )
        
        self.main_chain = prompt | self.model | output_parser 
        response = self.main_chain.invoke([{'theme': theme}])
        self.history = [response]
        return response 
     
        

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



