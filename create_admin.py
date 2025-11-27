from database import SessionLocal, engine, Base
from models import Admin
from auth import hash_password

# สร้าง tables ถ้ายังไม่สร้าง
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# กำหนด admin email/password
admin_email = "sewkuy6@gmail.com"
admin_password = "Admin@123"  # ใช้ password test

# hash password
hashed_pw = hash_password(admin_password)

# สร้าง Admin
existing_admin = db.query(Admin).filter(Admin.email == admin_email).first()
if not existing_admin:
    admin = Admin(email=admin_email, password_hash=hashed_pw)
    db.add(admin)
    db.commit()
    print(f"Admin created: {admin_email}")
else:
    print("Admin already exists!")

db.close()
