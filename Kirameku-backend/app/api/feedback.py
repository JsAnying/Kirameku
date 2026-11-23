from collections import deque
from threading import Lock
from time import monotonic
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session
from app.deps import get_session, get_current_user
from app.schemas.feedback import FeedbackCreate, FeedbackUpdate, FeedbackOut, FeedbackList, FeedbackType, FeedbackStatus
from app.services import feedback_service

router = APIRouter(prefix="/api/feedback", tags=["反馈"])

# 单进程限频：IP 仅短暂保留于内存，不写入反馈数据。
_attempts: dict[str, deque[float]] = {}
_lock = Lock()


def limit_feedback(request: Request):
    now = monotonic()
    host = request.client.host if request.client else "unknown"
    with _lock:
        for key in list(_attempts):
            queue = _attempts[key]
            while queue and queue[0] <= now - 60:
                queue.popleft()
            if not queue:
                del _attempts[key]
        queue = _attempts.setdefault(host, deque())
        if len(queue) >= 3:
            wait = max(1, int(60 - (now - queue[0])) + 1)
            raise HTTPException(429, "提交太频繁，请稍后再试", headers={"Retry-After": str(wait)})
        queue.append(now)


@router.post("", status_code=201, dependencies=[Depends(limit_feedback)])
def submit_feedback(data: FeedbackCreate, session: Session = Depends(get_session)):
    feedback_service.create_feedback(session, data)
    return {"message": "反馈已收到，谢谢你的建议"}


@router.get("/admin", response_model=FeedbackList, dependencies=[Depends(get_current_user)])
def list_feedback(status: FeedbackStatus | None = None, type: FeedbackType | None = None,
                  page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                  session: Session = Depends(get_session)):
    return feedback_service.list_feedback(session, status, type, page, size)


@router.get("/admin/{feedback_id}", response_model=FeedbackOut, dependencies=[Depends(get_current_user)])
def get_feedback(feedback_id: int, session: Session = Depends(get_session)):
    return feedback_service.get_feedback(session, feedback_id)


@router.patch("/admin/{feedback_id}", response_model=FeedbackOut, dependencies=[Depends(get_current_user)])
def update_feedback(feedback_id: int, data: FeedbackUpdate, session: Session = Depends(get_session)):
    return feedback_service.update_feedback(session, feedback_id, data)


@router.delete("/admin/{feedback_id}", dependencies=[Depends(get_current_user)])
def delete_feedback(feedback_id: int, session: Session = Depends(get_session)):
    feedback_service.delete_feedback(session, feedback_id)
    return {"ok": True}
