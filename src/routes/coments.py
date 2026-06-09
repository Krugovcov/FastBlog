from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, status, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import coments as repository_coments
from src.entity.models import User, Role

from src.schemas.coment import CommentaryResponseSchema, CommentaryUpdateSchema
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(tags=["coments"])


async def get_comments_by_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    
    comments = await repository_coments.get_comments_by_post(db, post_id, user)
    return comments

@router.get("/", response_model=List[CommentaryResponseSchema], status_code=status.HTTP_200_OK)
async def get_all_coments(
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(auth_service.get_current_user)
):
    return await repository_coments.get_coments(db)


@router.get("/{coment_id}", response_model=CommentaryResponseSchema, status_code=status.HTTP_200_OK)
async def get_single_coment(
    coment_id: int, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    coment = await repository_coments.get_coment(coment_id, db)
    if not coment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return coment


@router.post("/", response_model=CommentaryResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_coment(
    post_id: int = Form(...), 
    content: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
   
    from src.entity.models import Post
    from sqlalchemy import select
    
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found to comment on")

    return await repository_coments.create_coment(
        content=content, 
        db=db, 
        user=user,
        post=post
    )


@router.put("/{coment_id}", response_model=CommentaryResponseSchema, status_code=status.HTTP_200_OK)
async def update_coment( 
    coment_id: int, 
    body: CommentaryUpdateSchema, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    coment = await repository_coments.update_coment(coment_id, body, db, user)
    return coment


@router.delete("/{coment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coment(  # FIXED: Pointed to comment logic
    coment_id: int, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    await repository_coments.delete_coment(coment_id, db, user)
    return None




# --------------- Admin routes -----------------
admin_required = RoleAccess([Role.ADMIN])


@router.get("/admin/all", response_model=List[CommentaryResponseSchema], dependencies=[Depends(admin_required)])
async def admin_get_all_coments(db: AsyncSession = Depends(get_db)):
    return await repository_coments.get_all_coments_admin(db)


@router.delete("/admin/{coment_id}", dependencies=[Depends(admin_required)], status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_coment(coment_id: int, db: AsyncSession = Depends(get_db)):
    success = await repository_coments.admin_delete_photo(coment_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return None


@router.put("/admin/{coment_id}", response_model=CommentaryResponseSchema, dependencies=[Depends(admin_required)])
async def admin_update_coment(
    coment_id: int, 
    body: CommentaryUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    coment = await repository_coments.admin_update_coment(coment_id, body, db)
    if not coment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return coment