from fastapi import FastAPI, WebSocket
from src.graph import AgentConstructor

app = FastAPI()

@app.websocket("/generate")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent = AgentConstructor(ws=websocket) 
    state = await agent.generate(revision_limit=10)
    await websocket.send_json({"status": 200, "generation": True,"response": state["story"]})
    await websocket.close(code=1000, reason="request fulfilled")


