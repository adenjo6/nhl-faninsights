"""
Pydantic schemas for Comment/Chat API.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class CommentCreate(BaseModel):
    """Create a new comment."""
    game_id: int
    content: str
    parent_comment_id: Optional[int] = None


class CommentUpdate(BaseModel):
    """Update comment content."""
    content: str


class CommentResponse(BaseModel):
    """Comment response."""
    id: int
    game_id: int
    user_id: str
    user_name: str
    user_avatar_url: Optional[str] = None
    content: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_deleted: bool
    is_flagged: bool
    parent_comment_id: Optional[int] = None
    replies_count: int = 0

    class Config:
        from_attributes = True


class CommentWithReplies(CommentResponse):
    """Comment with nested replies."""
    replies: List[CommentResponse] = []

    class Config:
        from_attributes = True
