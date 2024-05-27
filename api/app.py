from fastapi import FastAPI, WebSocket
from src.graph import AgentConstructor

from src.utils import upload_video,delete_tmpfile
app = FastAPI()

@app.websocket("/generate")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent = AgentConstructor(ws=websocket) 
    state = await agent.generate(revision_limit=2)
    print(state)
    video_filepath = agent.director.compose_av(state["descriptions"])

    video_url = upload_video(video_filepath,state["story_request"])
    await websocket.send_json({"status": 200, "generation": True,"response": state["story"],"video_url": video_url})
    await websocket.close(code=1000, reason="request fulfilled")
        

    delete_tmpfile(video_filepath)
    for g in state["descriptions"]: delete_tmpfile(g.audio_file)




