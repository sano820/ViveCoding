from pydantic import BaseModel
from typing import List, Optional
import datetime

class PostBase(BaseModel):
    channel: str
    body: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    business_id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class BusinessBase(BaseModel):
    name: str
    category: str
    address: str
    strengths: List[str] = []
    tone: str = "정중하고 친근한 톤"

class BusinessCreate(BusinessBase):
    pass

class Business(BusinessBase):
    id: int
    posts: List[Post] = []

    class Config:
        orm_mode = True
