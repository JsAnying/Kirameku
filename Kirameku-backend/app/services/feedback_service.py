from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackUpdate


def create_feedback(session: Session, data: FeedbackCreate) -> None:
    session.add(Feedback(**data.model_dump()))
    session.commit()


def list_feedback(session: Session, status: str | None, type: str | None, page: int, size: int):
    filters = []
    if status:
        filters.append(Feedback.status == status)
    if type:
        filters.append(Feedback.type == type)
    total = session.exec(select(func.count()).select_from(Feedback).where(*filters)).one()
    items = session.exec(select(Feedback).where(*filters)
                         .order_by(Feedback.created_at.desc(), Feedback.id.desc())
                         .offset((page - 1) * size).limit(size)).all()
    return {"items": items, "total": total}


def get_feedback(session: Session, feedback_id: int) -> Feedback:
    item = session.get(Feedback, feedback_id)
    if not item:
        raise HTTPException(404, "反馈不存在")
    return item


def update_feedback(session: Session, feedback_id: int, data: FeedbackUpdate):
    item = get_feedback(session, feedback_id)
    item.status = data.status
    item.admin_note = data.admin_note
    item.updated_at = datetime.now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_feedback(session: Session, feedback_id: int):
    session.delete(get_feedback(session, feedback_id))
    session.commit()
