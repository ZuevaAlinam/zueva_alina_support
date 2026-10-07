"""Тесты бизнес-правил варианта 2."""
from datetime import datetime, timedelta
from app import models, auth
from app.services import ticket_service, summary_service

def test_first_response_fixed_on_support_comment(db_session):
    """Первый комментарий сотрудника фиксирует first_response_at."""
    user = models.User(username="u1", password_hash=auth.hash_password("x"), role="user")
    support = models.User(username="s1", password_hash=auth.hash_password("x"), role="support")
    cat = models.Category(name="Тест", reaction_norm_hours=4)
    db_session.add_all([user, support, cat]); db_session.commit()

    t = ticket_service.create_ticket(db_session, user.id, "T", "B", cat.id)
    assert t.first_response_at is None

    ticket_service.add_comment(db_session, t.id, support, "Первый ответ")
    db_session.refresh(t)
    assert t.first_response_at is not None

def test_user_comment_does_not_fix_first_response(db_session):
    """Комментарий обычного пользователя не фиксирует first_response_at."""
    user = models.User(username="u2", password_hash=auth.hash_password("x"), role="user")
    cat = models.Category(name="Тест", reaction_norm_hours=4)
    db_session.add_all([user, cat]); db_session.commit()

    t = ticket_service.create_ticket(db_session, user.id, "T", "B", cat.id)
    ticket_service.add_comment(db_session, t.id, user, "Уточнение")
    db_session.refresh(t)
    assert t.first_response_at is None

def test_status_transitions_restricted(db_session):
    """Нельзя закрыть заявку из статуса new минуя in_progress."""
    user = models.User(username="u3", password_hash=auth.hash_password("x"), role="user")
    support = models.User(username="s3", password_hash=auth.hash_password("x"), role="support")
    cat = models.Category(name="Тест", reaction_norm_hours=4)
    db_session.add_all([user, support, cat]); db_session.commit()

    t = ticket_service.create_ticket(db_session, user.id, "T", "B", cat.id)
    # new -> in_progress
    ticket_service.change_status(db_session, t.id, "in_progress", support)
    # in_progress -> closed
    ticket_service.change_status(db_session, t.id, "closed", support)
    db_session.refresh(t)
    assert t.status == "closed"
    assert t.closed_at is not None

def test_overdue_ratio_computed(db_session):
    """Доля нарушений норматива считается по заявкам с первым ответом."""
    user = models.User(username="u4", password_hash=auth.hash_password("x"), role="user")
    support = models.User(username="s4", password_hash=auth.hash_password("x"), role="support")
    cat = models.Category(name="Тест", reaction_norm_hours=1)
    db_session.add_all([user, support, cat]); db_session.commit()

    # Заявка 1: ответ через 0.5 часа — в норме
    t1 = models.Ticket(title="T1", body="B", category_id=cat.id, author_id=user.id,
                       created_at=datetime.utcnow() - timedelta(hours=10),
                       first_response_at=datetime.utcnow() - timedelta(hours=9, minutes=30),
                       status="closed")
    # Заявка 2: ответ через 5 часов — нарушение
    t2 = models.Ticket(title="T2", body="B", category_id=cat.id, author_id=user.id,
                       created_at=datetime.utcnow() - timedelta(hours=10),
                       first_response_at=datetime.utcnow() - timedelta(hours=5),
                       status="closed")
    db_session.add_all([t1, t2]); db_session.commit()

    summary = summary_service.get_summary(db_session, None, None)
    assert summary["overdue_count"] == 1
    assert summary["overdue_ratio"] == 0.5