from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    category_id: int


class TicketStatusUpdate(BaseModel):
    status: str = Field(..., regex="^(new|in_progress|closed)$")


class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1)


class TicketOut(BaseModel):
    id: int
    title: str
    body: str
    status: str
    category_id: int
    author_id: int
    assignee_id: Optional[int]
    created_at: datetime
    first_response_at: Optional[datetime]
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True
        orm_mode = True


class CommentOut(BaseModel):
    id: int
    ticket_id: int
    author_id: int
    body: str
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True


class TicketListOut(BaseModel):
    items: List[TicketOut]
    total: int
    page: int
    size: int


class TicketDetailOut(BaseModel):
    ticket: TicketOut
    comments: List[CommentOut]