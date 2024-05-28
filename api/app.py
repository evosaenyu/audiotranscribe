from fastapi import FastAPI, WebSocket,  WebSocketDisconnect, HTTPException, Depends
from src.graph import AgentConstructor

from sqlalchemy.orm import Session
from typing import List
from src.db import models, schemas
from src.db.models import SessionLocal, database
import asyncio

from src.sample import response

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



app = FastAPI(ws_ping_interval=None)
manager = ConnectionManager()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.websocket("/generate_fake")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.send_personal_message({"status": 200,"generation": False, "response": """{\n  "story_request": {},\n  "terminating": "no",\n  "question": "What kind of story would you like to hear? Please specify a theme or any particular elements you\'d like included."\n}""" },websocket)
    await websocket.receive_json()
    await manager.send_personal_message({"status": 200, "generation": False, "response": "dreaming something up just for you ..."},websocket)
    await asyncio.sleep(5)
    await manager.send_personal_message({"status":200,"generation":False,"response":"bringing story to life..."},websocket)
    await asyncio.sleep(5)
    await manager.send_personal_message({"status":200,"generation":False,"response":"filling in the plot devices..."},websocket)
    await asyncio.sleep(5)
    await manager.send_personal_message({"status": 200, "generation": False, "response": "adding finishing touches..." },websocket)
    await asyncio.sleep(5)
    await manager.send_personal_message({"status": 200, "generation": True,"response": response.story,"video_url": response.video_url},websocket)
    manager.disconnect(websocket)


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

@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.uid == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

