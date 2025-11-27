from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request, Form, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User, Admin
from auth import hash_password, verify_password, create_session_token, verify_session_token, is_password_strong
from rate_limiter import is_blocked, add_attempt, reset_attempts
from fastapi import Request

load_dotenv()  # โหลดไฟล์ .env

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
USER_SESSION_EXPIRE_MINUTES = int(os.getenv("USER_SESSION_EXPIRE_MINUTES", 30))
ADMIN_SESSION_EXPIRE_MINUTES = int(os.getenv("ADMIN_SESSION_EXPIRE_MINUTES", 60))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

print("SECRET_KEY:", SECRET_KEY)
print("DATABASE_URL:", DATABASE_URL)

# สร้าง tables ใน DB
Base.metadata.create_all(bind=engine)
print("Database tables created!")

app = FastAPI()

templates = Jinja2Templates(directory="templates")  # ชี้ไปที่โฟลเดอร์ templates

# dependency สำหรับ session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# หน้า login
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# หน้า signup
@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "error": None  # เพิ่ม default
    })

# หน้า signup POST
@app.post("/signup")
def signup_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # ตรวจสอบ password strength
    if not is_password_strong(password):
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Password must be at least 8 characters, include uppercase, lowercase, number, and special character!"
        })

    # ตรวจสอบ email ซ้ำ
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already registered!"})

    # hash password
    hashed_pw = hash_password(password)

    # สร้าง user
    new_user = User(email=email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()

    # redirect ไป login
    response = RedirectResponse(url="/login", status_code=303)
    return response

# หน้า login POST
@app.post("/login")
def login_post(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    
    print("Client IP:", request.client.host)   # ⭐ เพิ่มบรรทัดนี้

    client_ip = request.client.host  # ดึง IP ของผู้ใช้

    # ⛔ เช็คว่าถูกบล็อคไหม
    blocked, remaining = is_blocked(email, client_ip)

    if blocked:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Too many login attempts. Try again in {remaining} seconds."
        })

    # ตรวจสอบ admin
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin and verify_password(password, admin.password_hash):
        token = create_session_token(email)
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie(
            key="admin_session",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/"
        )
        reset_attempts(email, client_ip)
        return response

    # ตรวจสอบ user
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.password_hash):
        token = create_session_token(email)
        response = RedirectResponse(url="/user/dashboard", status_code=303)
        response.set_cookie(
            key="user_session",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/"
        )
        reset_attempts(email, client_ip)
        return response

    # ❌ ถ้า login ผิด —> เพิ่ม attempt ทั้ง email + IP
    add_attempt(email, client_ip)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Invalid credentials"
    })

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(admin_session: str = Cookie(None), request: Request = None):
    from auth import verify_session_token
    email = verify_session_token(admin_session, max_age=ADMIN_SESSION_EXPIRE_MINUTES*60)
    if not email:
        return RedirectResponse("/login")
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@app.get("/user/dashboard", response_class=HTMLResponse)
def user_dashboard(user_session: str = Cookie(None), request: Request = None):
    from auth import verify_session_token
    email = verify_session_token(user_session, max_age=USER_SESSION_EXPIRE_MINUTES*60)
    if not email:
        return RedirectResponse("/login")
    return templates.TemplateResponse("user_dashboard.html", {"request": request})

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_session")
    response.delete_cookie("admin_session")
    return response
