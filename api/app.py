from fastapi import FastAPI, WebSocket,  WebSocketDisconnect
from src.graph import AgentConstructor

from src.utils import upload_video,delete_tmpfile


class ConnectionManager:
    """Class defining socket events"""
    def __init__(self):
        """init method, keeping track of connections"""
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        """connect event"""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message, websocket: WebSocket):
        """Direct Message"""
        await websocket.send_json(message)
        return 0
    
    def disconnect(self, websocket: WebSocket):
        """disconnect event"""
        self.active_connections.remove(websocket)
        websocket.close(code=1000, reason="request fulfilled")
        return 0


app = FastAPI()
manager = ConnectionManager()

@app.websocket("/generate")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        agent = AgentConstructor(ws=websocket) 
        state = await agent.generate(revision_limit=2)
        print(state)
        video_filepath = await agent.director.compose_av(state["descriptions"])

        video_url = upload_video(video_filepath,state["story_request"])
        await manager.send_personal_message({"status": 200, "generation": True,"response": state["story"],"video_url": video_url},websocket)
    except WebSocketDisconnect:
        print('client disconnected')

    manager.disconnect(websocket) 
        
    delete_tmpfile(video_filepath)
    for g in state["descriptions"]: delete_tmpfile(g.audio_file)




