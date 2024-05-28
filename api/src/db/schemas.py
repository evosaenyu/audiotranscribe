from pydantic import BaseModel

class UserBase(BaseModel):
    uid: str
    email: str = ""
    firstname: str = ""
    lastname: str  = ""

class UserCreate(UserBase):
    pass

class User(UserBase):
    uid: str

    class Config:
        orm_mode = True