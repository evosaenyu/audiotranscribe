
from langgraph.graph import StateGraph , END 
from typing import TypedDict, Annotated 
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage,AIMessage

from agents import Initializer, Constructor, Critic, Editor 
import logging 
import json 

LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='graph.log', encoding='utf-8', level=logging.DEBUG)

class State(TypedDict): 
    messages: Annotated[list,add_messages]
    story_request: object  = {} # {theme: str, .... (extra params as requested)}
    story: str # string the current story 
    critic_feedback: object  # {satisfactory: yes or no, feedback: }
    satisfactory: str 
    feedback: str

class AgentConstructor: 

    def __init__(self,):
        self.initializer = Initializer()
        self.constructor = Constructor()
        self.critic = Critic()
        self.editor = Editor()
        self.construct_graph()
        self.revisions = 0

        self.initializer.partial_chain = self.initializer.prompt | self.initializer.model
    
    def get_user_input(self,state):
        ai_response = state["messages"][-1]
        ai_response.pretty_print()
        return {"messages": [HumanMessage(content=input("what's your response? "))]}

    def run_initializer(self,state):
        messages = state["messages"]
        response = self.initializer.partial_chain.invoke({"messages": messages})
        parsed_response = self.initializer.output_parser.parse(response.content)
        return {"messages": [response],"story_request": parsed_response['story_request']}
    

    def should_continue_initialization(self,state):
        latest = self.initializer.output_parser.parse(state["messages"][-1].content) 
        if "terminating" in latest:
            if latest["terminating"] == "yes":
                return "initialized"
        
        return "continue"


    def should_terminate(self,state):
        self.revisions += 1
        LOGGER.info(state)
        if state["satisfactory"] == "yes" or self.revisions >= 3: 
            return "end"
        return "continue"
    

    def construct_graph(self,user_input_fn=None):
        self.graph = StateGraph(State)
        for v,e in zip(["editor","constructor","critic"],[self.editor,self.constructor,self.critic]):
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
                "end": END,
                "continue": "editor"
            }
        )
        self.graph.add_edge("editor","critic")
        self.runnable = self.graph.compile()



if __name__ == "__main__":
    agent = AgentConstructor()
    app = agent.runnable 
    state = app.invoke({"messages": [HumanMessage(content = " ")]}) #{"recursion_limit": 3}
    # print(app.get_state())
    #app.invoke({"messages": []}) # {"recursion_limit": 3}
    # current_response = {'terminating': 'no'}
    # thread = {"configurable": {"thread_id": "2"}}
    # current_input = HumanMessage(content='hey')
    # while current_response['terminating'] == 'no': 
    #     for event in app.stream({"messages": [current_input] }, thread, stream_mode="values"):
    #         current_response = event["messages"][-1]
    #         current_response.pretty_print()
    #         current_input = HumanMessage(content=input("your response: "))
        
    print(state)

    
