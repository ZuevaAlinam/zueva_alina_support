from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.models import Ticket, Comment, User, Category


VALID_TRANSITIONS = {
    "new": {"in_progress", "closed"},
    "in_progress": {"closed"},
    "closed": set(),
}


def create_ticket(
    db: Session, author_id: int, title: str, body: str, category_id: int
) -> Ticket:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise ValueError("Category not found")
    ticket = Ticket(
        title=title,
        body=body,
        category_id=category_id,
        author_id=author_id,
        status="new",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def change_status(db: Session, ticket_id: int, new_status: str, user: User) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise ValueError("Ticket not found")
    if new_status not in VALID_TRANSITIONS.get(ticket.status, set()):
        raise ValueError("Transition %s -> %s not allowed" % (ticket.status, new_status))
    if user.role not in ("support", "admin"):
        raise PermissionError("Only support can change status")
    ticket.status = new_status
    if new_status == "closed":
        ticket.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


def add_comment(db: Session, ticket_id: int, author: User, body: str) -> Comment:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise ValueError("Ticket not found")
    comment = Comment(ticket_id=ticket_id, author_id=author.id, body=body)
    db.add(comment)
    if ticket.first_response_at is None and author.role in ("support", "admin"):
        ticket.first_response_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return comment


def list_tickets(
    db: Session,
    page: int,
    size: int,
    status: Optional[str],
    category_id: Optional[int],
) -> Tuple[List[Ticket], int]:
    query = db.query(Ticket)
    count_query = db.query(func.count(Ticket.id))
    if status:
        query = query.filter(Ticket.status == status)
        count_query = count_query.filter(Ticket.status == status)
    if category_id:
        query = query.filter(Ticket.category_id == category_id)
        count_query = count_query.filter(Ticket.category_id == category_id)
    total = count_query.scalar()
    items = (
        query.order_by(Ticket.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return items, total