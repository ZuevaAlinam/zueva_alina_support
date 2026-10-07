from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models, schemas, auth
from app.services import ticket_service, summary_service

Base.metadata.create_all(bind=engine)

app = FastAPI(title="zueva_alina support service")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if not request.cookies.get(auth.SESSION_COOKIE):
        return RedirectResponse("/login")
    return RedirectResponse("/tickets")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter_by(username=username).first()
    if not user or not auth.verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Неверные данные"}
        )
    token = auth.create_session(user.id)
    response = RedirectResponse("/tickets", status_code=302)
    response.set_cookie(
        auth.SESSION_COOKIE, token, httponly=True, max_age=auth.SESSION_MAX_AGE
    )
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/login")
    response.delete_cookie(auth.SESSION_COOKIE)
    return response


@app.get("/tickets", response_class=HTMLResponse)
def tickets_page(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    user_id = auth.get_current_user_id(request)
    items, total = ticket_service.list_tickets(db, page, size, status, category_id)
    categories = db.query(models.Category).all()
    return templates.TemplateResponse(
        "tickets_list.html",
        {
            "request": request,
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "status": status,
            "category_id": category_id,
            "categories": categories,
            "user": db.query(models.User).filter(models.User.id == user_id).first(),
        },
    )


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail_page(ticket_id: int, request: Request, db: Session = Depends(get_db)):
    auth.get_current_user_id(request)
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404)
    comments = (
        db.query(models.Comment)
        .filter_by(ticket_id=ticket_id)
        .order_by(models.Comment.created_at)
        .all()
    )
    return templates.TemplateResponse(
        "ticket_detail.html",
        {"request": request, "ticket": ticket, "comments": comments},
    )


@app.get("/summary", response_class=HTMLResponse)
def summary_page(request: Request, db: Session = Depends(get_db)):
    auth.get_current_user_id(request)
    data = summary_service.get_summary(db, None, None)
    return templates.TemplateResponse(
        "summary.html", {"request": request, "data": data}
    )


@app.post("/api/auth/login")
def api_login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=payload.username).first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = auth.create_session(user.id)
    response = JSONResponse({"ok": True})
    response.set_cookie(
        auth.SESSION_COOKIE, token, httponly=True, max_age=auth.SESSION_MAX_AGE
    )
    return response


@app.post("/api/auth/logout")
def api_logout():
    response = JSONResponse({"ok": True}, status_code=204)
    response.delete_cookie(auth.SESSION_COOKIE)
    return response


@app.get("/api/tickets", response_model=schemas.TicketListOut)
def api_list_tickets(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    auth.get_current_user_id(request)
    items, total = ticket_service.list_tickets(db, page, size, status, category_id)
    return {"items": items, "total": total, "page": page, "size": size}


@app.get("/api/tickets/{ticket_id}", response_model=schemas.TicketDetailOut)
def api_ticket_detail(ticket_id: int, request: Request, db: Session = Depends(get_db)):
    auth.get_current_user_id(request)
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404)
    comments = (
        db.query(models.Comment)
        .filter_by(ticket_id=ticket_id)
        .order_by(models.Comment.created_at)
        .all()
    )
    return {"ticket": ticket, "comments": comments}


@app.post("/api/tickets", response_model=schemas.TicketOut, status_code=201)
def api_create_ticket(
    payload: schemas.TicketCreate, request: Request, db: Session = Depends(get_db)
):
    user_id = auth.get_current_user_id(request)
    try:
        return ticket_service.create_ticket(
            db, user_id, payload.title, payload.body, payload.category_id
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.patch("/api/tickets/{ticket_id}/status", response_model=schemas.TicketOut)
def api_change_status(
    ticket_id: int,
    payload: schemas.TicketStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = auth.get_current_user_id(request)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    try:
        return ticket_service.change_status(db, ticket_id, payload.status, user)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))


@app.post(
    "/api/tickets/{ticket_id}/comments",
    response_model=schemas.CommentOut,
    status_code=201,
)
def api_add_comment(
    ticket_id: int,
    payload: schemas.CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = auth.get_current_user_id(request)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    try:
        return ticket_service.add_comment(db, ticket_id, user, payload.body)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get("/api/summary")
def api_summary(request: Request, db: Session = Depends(get_db)):
    auth.get_current_user_id(request)
    return summary_service.get_summary(db, None, None)