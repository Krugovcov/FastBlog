from typing import Optional, List
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.entity.models import User, Post, Role, Comment
from src.schemas.coment import CommentaryCreateSchema, CommentaryUpdateSchema, CommentaryResponseSchema


async def get_coments(db: AsyncSession) -> List[CommentaryResponseSchema]:
    stmt = select(Comment).options(selectinload(Comment.user))
    result = await db.execute(stmt)
    comments = result.scalars().all()
    return [CommentaryResponseSchema.model_validate(c) for c in comments]


async def get_coment(coment_id: int, db: AsyncSession) -> Optional[CommentaryResponseSchema]:
    stmt = select(Comment).filter_by(id=coment_id).options(selectinload(Comment.user))
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    return CommentaryResponseSchema.model_validate(comment) if comment else None


async def create_coment(
    content: str,
    db: AsyncSession,
    user: User,
    post: Post
) -> CommentaryResponseSchema:
    new_coment = Comment(
        content=content,
        post_id=post.id,
        user_id=user.id
    )
    
    db.add(new_coment)
    await db.commit()
    await db.refresh(new_coment)
    return CommentaryResponseSchema.model_validate(new_coment)


async def update_coment(coment_id: int, body: CommentaryUpdateSchema, db: AsyncSession, user: User) -> CommentaryResponseSchema:
    stmt = select(Comment).filter_by(id=coment_id)
    result = await db.execute(stmt)
    coment = result.scalar_one_or_none()

    if not coment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if coment.user_id != user.id and user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(status_code=403, detail="Not enough permissions to update this comment")

    if body.content is not None and body.content != coment.content:
        coment.content = body.content

    await db.commit()
    await db.refresh(coment)
    return CommentaryResponseSchema.model_validate(coment)


async def delete_coment(coment_id: int, db: AsyncSession, user: User):
    stmt = select(Comment).filter_by(id=coment_id)
    result = await db.execute(stmt)
    coment = result.scalar_one_or_none()

    if not coment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if coment.user_id != user.id and user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(status_code=403, detail="Not enough permissions to delete this comment")
   
    await db.delete(coment)
    await db.commit()

    return {"detail": "Comment deleted successfully"}

async def get_comments_by_post(db: AsyncSession, post_id: int, user: User):
    
    post = await db.get(Post, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view comments for this post")
    stmt = (
        select(Comment)
        .filter_by(post_id=post.id)
        .options(selectinload(Comment.user))
    )
    comments = await db.execute(stmt)
    result = comments.scalars().all()
    return [CommentaryResponseSchema.model_validate(comment) for comment in result]


# --------------- Admin methods -----------------

async def get_all_coments_admin(db: AsyncSession) -> List[CommentaryResponseSchema]:
    result = await db.execute(select(Comment))
    coment = result.scalars().all()
    return [CommentaryResponseSchema.model_validate(p) for p in coment]


async def admin_delete_photo(coment_id: int, db: AsyncSession) -> bool:
    result = await db.execute(select(Comment).where(Comment.id == coment_id))
    comment = result.scalar_one_or_none() 
    
    if not comment:
        return False
        
    await db.delete(comment)
    await db.commit()
    return True


async def admin_update_coment(coment_id: int, body: CommentaryUpdateSchema, db: AsyncSession) -> Optional[CommentaryResponseSchema]:
    result = await db.execute(select(Comment).where(Comment.id == coment_id))
    coment = result.scalar_one_or_none()
    if not coment:
        return None
        
    if body.content is not None:
        coment.content = body.content
        
    await db.commit()
    await db.refresh(coment)
    return CommentaryResponseSchema.model_validate(coment)