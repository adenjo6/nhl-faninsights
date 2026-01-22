"""
CRUD operations for Comment model (chat/discussion system).
"""
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime
from app.models.comment import Comment


def create_comment(db: Session, comment_data: dict) -> Comment:
    """Create a new comment."""
    comment = Comment(**comment_data)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comment_by_id(db: Session, comment_id: int) -> Optional[Comment]:
    """Get a comment by ID with user info."""
    return db.query(Comment).options(
        joinedload(Comment.replies)
    ).filter(Comment.id == comment_id).first()


def get_comments_by_game(
    db: Session,
    game_id: int,
    skip: int = 0,
    limit: int = 100,
    parent_only: bool = True
) -> List[Comment]:
    """Get comments for a game."""
    query = db.query(Comment).filter(Comment.game_id == game_id)

    if parent_only:
        query = query.filter(Comment.parent_comment_id == None)

    return query.order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()


def get_replies(db: Session, parent_comment_id: int) -> List[Comment]:
    """Get replies to a comment."""
    return db.query(Comment).filter(
        Comment.parent_comment_id == parent_comment_id
    ).order_by(Comment.created_at).all()


def update_comment(db: Session, comment_id: int, content: str) -> Optional[Comment]:
    """Update comment content."""
    comment = get_comment_by_id(db, comment_id)
    if not comment:
        return None

    comment.content = content
    comment.edited_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: int) -> bool:
    """Delete a comment (soft delete by setting is_deleted)."""
    comment = get_comment_by_id(db, comment_id)
    if not comment:
        return False

    comment.is_deleted = True
    comment.content = "[deleted]"
    db.commit()
    return True


def flag_comment(db: Session, comment_id: int) -> bool:
    """Flag a comment for moderation."""
    comment = get_comment_by_id(db, comment_id)
    if not comment:
        return False

    comment.is_flagged = True
    db.commit()
    return True
