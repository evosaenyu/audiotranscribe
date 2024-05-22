
from langgraph.graph import StateGraph , END 
from typing import TypedDict, Annotated 
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage,AIMessage

from src.agents import Initializer, Constructor, Critic, Editor , Copywriter 
import logging 
import json

from src.responses import *

LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='graph.log', encoding='utf-8', level=logging.DEBUG)

class State(TypedDict): 
    messages: Annotated[list,add_messages]
    story_request: InitializationResponse # {theme: str, .... (extra params as requested)}
    story: StoryObject # string the current story 
    satisfactory: CriticResponse
    feedback: CriticResponse
    descriptions: Descriptions

class AgentConstructor: 

    def __init__(self,ws=None):
        self.initializer = Initializer()
        self.constructor = Constructor()
        self.critic = Critic()
        self.editor = Editor()
        self.copywriter = Copywriter()
        # self.construct_graph()
        self.revisions = 0
        self.rev_limit = 3
        self.ws = ws 

        self.initializer.partial_chain = self.initializer.prompt | self.initializer.model
    
    @staticmethod
    def str_to_msg(text): #for external functions to be able to use 
        return {"messages": [HumanMessage(content=text)]}
    
    async def get_user_input(self,state):
        ai_response = state["messages"][-1]
        ai_response.pretty_print()
        
        if self.ws: 
            _ = await self.ws.send_json({"status": 200, "generation": False, "response": ai_response.content })
            msg = await self.ws.receive_json()
            if type(msg) == str: msg = json.loads(msg)
            print(msg)
            msg = msg["response"] 
        else:
            msg = input("what's your response? ")
        
        return self.str_to_msg(msg)

    def run_initializer(self,state):
        messages = state["messages"]
        response = self.initializer.partial_chain.invoke({"messages": messages})
        parsed_response = self.initializer.parser.parse(response.content)
        return {"messages": [response],"story_request": parsed_response.story_request}
    

    async def should_continue_initialization(self,state):
        latest = self.initializer.parser.parse(state["messages"][-1].content) 
        if latest.terminating == terminationEnum.yes:
            _ = await self.ws.send_json({"status": 200, "generation": False, "response": "dreaming something up just for you ..."})
            return "initialized"

        return "continue"


    def should_terminate(self,state):
        self.revisions += 1
        LOGGER.info(state)
        if state["satisfactory"] == terminationEnum.yes or self.revisions >= self.rev_limit: 
            return "art"
        return "continue"
    

    def construct_graph(self,user_input_fn):
        self.graph = StateGraph(State)
        self.revisions = 0

        for v,e in zip(["editor","constructor","critic","copywriter"],[self.editor,self.constructor,self.critic,self.copywriter]):
            self.graph.add_node(v,e.chain)
    
        self.graph.add_node("initializer",self.run_initializer)
        self.graph.add_node("get_user_input",self.get_user_input if not user_input_fn else user_input_fn)
        self.graph.add_edge("get_user_input","initializer")
        self.graph.set_entry_point("initializer")
        self.graph.add_conditional_edges(
            "initializer",
            self.should_continue_initialization,
            {
                "continue": "get_user_input",
                "initialized": "constructor"
            }
        )
        # self.graph.add_edge("initializer","constructor")
        self.graph.add_edge("constructor","critic")
        self.graph.add_conditional_edges(
            "critic",
            self.should_terminate,
            {
                "art": "copywriter",
                "continue": "editor"
            }
        )
        self.graph.add_edge("editor","critic")
        self.graph.add_edge("copywriter",END)
        self.runnable = self.graph.compile()

        return self.runnable

    async def generate(self,user_input_fn=None,revision_limit=3):
        self.rev_limit = revision_limit
        app = self.construct_graph(user_input_fn=user_input_fn)
        return await app.ainvoke({"messages": [HumanMessage(content = " ")]})




if __name__ == "__main__":
    agent = AgentConstructor()
    state = agent.generate() #{"recursion_limit": 3}

        
    print(state)

    
