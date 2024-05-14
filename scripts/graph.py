
from langgraph.graph import StateGraph , END 
from typing import TypedDict, Annotated 

from agents import Initializer, Constructor, Critic, Editor 
import logging 

LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='graph.log', encoding='utf-8', level=logging.DEBUG)

def increment(current: int, new):
    print('INCREMENTING',current)
    return current + 1 

class State(TypedDict): 
    context: str 
    story_request: object # {theme: str, .... (extra params as requested)}
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
    def should_continue(state):
        LOGGER.info(state)
        if state["satisfactory"] == "yes" or state["ctr"] >= 3: 
            return "end"
        return "continue"
        
    
    def construct_graph(self):
        self.graph = StateGraph(State)
        for v,e in zip(["initializer","editor","constructor","critic"],[self.initializer,self.editor,self.constructor,self.critic]):
            self.graph.add_node(v,e.chain)
        
        self.graph.set_entry_point("initializer")
        self.graph.add_edge("initializer","constructor")
        self.graph.add_edge("constructor","critic")
        self.graph.add_conditional_edges(
            "critic",
            self.should_continue,
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
    app.invoke({"context": "tell me a bed time story"},{"recursion_limit": 3})
    print(app.get_state())

    
