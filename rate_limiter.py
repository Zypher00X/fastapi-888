import time
from collections import defaultdict

# เก็บ attempts ทั้ง 2 แบบ
attempts_by_email = defaultdict(list)  # key: email
attempts_by_ip = defaultdict(list)     # key: IP

MAX_ATTEMPTS = 5       # ลองผิดได้สูงสุด 5 ครั้ง
BLOCK_TIME = 300       # 5 นาที = 300 วินาที


def _cleanup(attempt_list):
    """ลบ attempts ที่เก่าเกิน BLOCK_TIME"""
    now = time.time()
    return [t for t in attempt_list if now - t < BLOCK_TIME]


def get_remaining_block_time(attempt_list):
    """คืนเวลาที่เหลือจนกว่าจะ login ได้ใหม่"""
    if not attempt_list:
        return 0
    now = time.time()
    # เวลาที่ oldest attempt จะครบ BLOCK_TIME
    oldest = min(attempt_list)
    remaining = BLOCK_TIME - (now - oldest)
    return max(0, int(remaining))


def is_blocked(email: str, ip: str):
    """เช็คว่า email หรือ IP อยู่ในสถานะถูกบล็อคหรือไม่"""

    # clean attempts
    attempts_by_email[email] = _cleanup(attempts_by_email[email])
    attempts_by_ip[ip] = _cleanup(attempts_by_ip[ip])

    email_blocked = len(attempts_by_email[email]) >= MAX_ATTEMPTS
    ip_blocked = len(attempts_by_ip[ip]) >= MAX_ATTEMPTS

    if email_blocked or ip_blocked:
        # เวลา remaining ทั้งจาก email และ IP
        return True, max(
            get_remaining_block_time(attempts_by_email[email]),
            get_remaining_block_time(attempts_by_ip[ip])
        )

    return False, 0


def add_attempt(email: str, ip: str):
    """บันทึก attempt ของ email และ IP"""
    now = time.time()
    attempts_by_email[email].append(now)
    attempts_by_ip[ip].append(now)


def reset_attempts(email: str, ip: str):
    """ล้าง attempts เมื่อ login สำเร็จ"""
    attempts_by_email[email] = []
    attempts_by_ip[ip] = []
