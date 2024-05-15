
from langgraph.graph import StateGraph , END 
from typing import TypedDict, Annotated 
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

from agents import Initializer, Constructor, Critic, Editor 
import logging 

LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='graph.log', encoding='utf-8', level=logging.DEBUG)

def increment(current: int, new):
    print('INCREMENTING',current)
    return current + 1 

class State(TypedDict): 
    context: Annotated[list,add_messages]
    story_request: object  = {} # {theme: str, .... (extra params as requested)}
    story: str # string the current story 
    critic_feedback: object  # {satisfactory: yes or no, feedback: }
    story_len: int = 10000
    satisfactory: str 
    feedback: str
    ctr: Annotated[int, increment]

class AgentConstructor: 

    def __init__(self,):
        self.initializer = Initializer()
        self.constructor = Constructor()
        self.critic = Critic()
        self.editor = Editor()
        self.construct_graph()
    
    @staticmethod
    def continue_initialization(state):
        print(state["context"][-1])
        response = input("your response: ")
        return {"context": [HumanMessage(content=response)]}

    
    @staticmethod
    def should_continue_initialization(state):
        if "terminating" in state["context"][-1]:
            if state["context"][-1]["terminating"] == "yes":
                return "initialized"
        
        return "continue"

    @staticmethod
    def should_terminate(state):
        LOGGER.info(state)
        if state["satisfactory"] == "yes" or state["ctr"] >= 3: 
            return "end"
        return "continue"
    

    def construct_graph(self):
        self.graph = StateGraph(State)
        for v,e in zip(["initializer","editor","constructor","critic"],[self.initializer,self.editor,self.constructor,self.critic]):
            self.graph.add_node(v,e.chain)
    
        self.graph.add_node("continue_initialization",self.continue_initialization)
        self.graph.add_edge("continue_initialization","initializer")
        self.graph.set_entry_point("initializer")
        self.graph.add_conditional_edges(
            "initializer",
            self.should_continue_initialization,
            {
                "continue": "continue_initialization",
                "initialized": "constructor"
            }
        )
        # self.graph.add_edge("initializer","constructor")
        self.graph.add_edge("constructor","critic")
        self.graph.add_conditional_edges(
            "critic",
            self.should_terminate,
            {
                "end": END,
                "continue": "editor"
            }
        )
        self.graph.add_edge("editor","critic")
        self.runnable = self.graph.compile()



if __name__ == "__main__":
    agent = AgentConstructor()
    app = agent.runnable 
    # app.invoke({"context": [HumanMessage(content = "tell me a bedtime story")]},{"recursion_limit": 3})
    # print(app.get_state())

    thread = {"configurable": {"thread_id": "2"}}
    inputs = [HumanMessage(content="hi! what's your name? ")]
    for event in app.stream({"context": inputs}, thread, stream_mode="values"):
        event["context"][-1].pretty_print()

    
