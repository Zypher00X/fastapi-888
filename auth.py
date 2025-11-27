from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
import os
import re

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
serializer = URLSafeTimedSerializer(SECRET_KEY)

# ใช้ Argon2 แทน bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# verify password
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

# สร้าง session token
def create_session_token(email: str):
    return serializer.dumps(email)

# ตรวจสอบ token และดึง email
def verify_session_token(token: str, max_age: int = 3600):
    try:
        email = serializer.loads(token, max_age=max_age)
        return email
    except Exception:
        return None

def is_password_strong(password: str) -> bool:
    """
    ตรวจสอบความแข็งแรงของ password:
    - ความยาวอย่างน้อย 8 ตัวอักษร
    - มีตัวพิมพ์ใหญ่ 1 ตัวขึ้นไป
    - มีตัวพิมพ์เล็ก 1 ตัวขึ้นไป
    - มีตัวเลข 1 ตัวขึ้นไป
    - มีสัญลักษณ์พิเศษ 1 ตัวขึ้นไป
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True