from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Ticket, Category


def get_summary(
    db: Session,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> Dict[str, Any]:
    open_statuses = ("new", "in_progress")

    open_by_category = {}
    for cat in db.query(Category).all():
        q = db.query(func.count(Ticket.id)).filter(
            Ticket.status.in_(open_statuses), Ticket.category_id == cat.id
        )
        if date_from:
            q = q.filter(Ticket.created_at >= date_from)
        if date_to:
            q = q.filter(Ticket.created_at <= date_to)
        open_by_category[cat.name] = q.scalar()

    answered = (
        db.query(Ticket)
        .filter(Ticket.first_response_at.isnot(None))
        .all()
    )

    total_answered = len(answered)
    overdue = 0
    for t in answered:
        norm = t.category.reaction_norm_hours
        delta = (t.first_response_at - t.created_at).total_seconds() / 3600.0
        if delta > norm:
            overdue += 1

    overdue_ratio = (overdue / float(total_answered)) if total_answered else 0.0

    return {
        "open_by_category": open_by_category,
        "overdue_ratio": round(overdue_ratio, 4),
        "total_answered": total_answered,
        "overdue_count": overdue,
    }