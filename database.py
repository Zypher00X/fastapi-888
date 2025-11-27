from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# สร้าง engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # สำหรับ SQLite
)

# session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class สำหรับ model
Base = declarative_base()
