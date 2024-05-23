
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum



class terminationEnum(Enum): 
    yes = 'yes'
    no = 'no'

class DescriptionItem(BaseModel): 
    story_section: str = Field(description="the exact section of the story to be read while the related image_description is showing") # hmm.. 
    image_description: str = Field(description="extremely vividly detailed description of the backdrop")
    image_url: Optional[str] = Field(default="",description= "the url of the image generated using the image description")

class Descriptions(BaseModel):
    descriptions: List[DescriptionItem] = Field(description="a list of descriptions, each one an extremely vividly detailed description of the backdrop")

class InitializationResponse(BaseModel):
    story_request: dict = Field(description="an object that has a field representing each part of the user's request. At minimum it should have the theme field set to a certain value")
    terminating: terminationEnum = Field(description="flag to know once you have enough information to provide the theme, yes or no only.")
    question: str = Field(default="",description="the question you'd like to ask the user, if any")

class StoryObject(BaseModel):
    story:str = Field(description="the complete story")

class CriticResponse(BaseModel):
    satisfactory: terminationEnum = Field(description="single word yes or no whether or not this story is satisfactory")
    feedback: str = Field(description="a detailed description outlining which parts of the story needs to be improved if at all")
