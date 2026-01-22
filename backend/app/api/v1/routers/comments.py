"""
Comments/Chat API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.v1.deps import get_db, get_current_user, require_admin
from app.crud import comment as comment_crud
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentWithReplies
)


router = APIRouter()


@router.get("/game/{game_id}", response_model=List[CommentWithReplies])
def get_game_comments(
    game_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get comments for a specific game.

    Returns top-level comments with nested replies.
    """
    comments = comment_crud.get_comments_by_game(
        db,
        game_id=game_id,
        skip=skip,
        limit=limit,
        parent_only=True
    )

    # Add replies to each comment
    result = []
    for comment in comments:
        replies = comment_crud.get_replies(db, comment.id)
        result.append(CommentWithReplies(
            id=comment.id,
            game_id=comment.game_id,
            user_id=comment.user_id,
            user_name=comment.user_name,
            user_avatar_url=comment.user_avatar_url,
            content=comment.content,
            created_at=comment.created_at,
            edited_at=comment.edited_at,
            is_deleted=comment.is_deleted,
            is_flagged=comment.is_flagged,
            parent_comment_id=comment.parent_comment_id,
            replies_count=len(replies),
            replies=[
                CommentResponse(
                    id=r.id,
                    game_id=r.game_id,
                    user_id=r.user_id,
                    user_name=r.user_name,
                    user_avatar_url=r.user_avatar_url,
                    content=r.content,
                    created_at=r.created_at,
                    edited_at=r.edited_at,
                    is_deleted=r.is_deleted,
                    is_flagged=r.is_flagged,
                    parent_comment_id=r.parent_comment_id,
                    replies_count=0
                )
                for r in replies
            ]
        ))

    return result


@router.post("", response_model=CommentResponse, status_code=201)
def create_comment(
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new comment (requires authentication).
    """
    # Add user info from Clerk
    comment_dict = comment_data.dict()
    comment_dict["user_id"] = current_user["user_id"]
    comment_dict["user_name"] = current_user["user_name"]
    comment_dict["user_avatar_url"] = current_user.get("avatar_url")

    comment = comment_crud.create_comment(db, comment_dict)

    return CommentResponse(
        id=comment.id,
        game_id=comment.game_id,
        user_id=comment.user_id,
        user_name=comment.user_name,
        user_avatar_url=comment.user_avatar_url,
        content=comment.content,
        created_at=comment.created_at,
        edited_at=comment.edited_at,
        is_deleted=comment.is_deleted,
        is_flagged=comment.is_flagged,
        parent_comment_id=comment.parent_comment_id,
        replies_count=0
    )


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    update_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a comment (only by comment author).
    """
    comment = comment_crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check ownership
    if comment.user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    updated_comment = comment_crud.update_comment(db, comment_id, update_data.content)

    return CommentResponse(
        id=updated_comment.id,
        game_id=updated_comment.game_id,
        user_id=updated_comment.user_id,
        user_name=updated_comment.user_name,
        user_avatar_url=updated_comment.user_avatar_url,
        content=updated_comment.content,
        created_at=updated_comment.created_at,
        edited_at=updated_comment.edited_at,
        is_deleted=updated_comment.is_deleted,
        is_flagged=updated_comment.is_flagged,
        parent_comment_id=updated_comment.parent_comment_id,
        replies_count=0
    )


@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a comment (soft delete - only by author or admin).
    """
    comment = comment_crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check ownership or admin
    if comment.user_id != current_user["user_id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    comment_crud.delete_comment(db, comment_id)
    return None


@router.post("/{comment_id}/flag", status_code=204)
def flag_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Flag a comment for moderation (requires authentication).
    """
    success = comment_crud.flag_comment(db, comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")

    return None
