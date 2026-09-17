from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from dotenv import load_dotenv

class Base(DeclarativeBase):
    pass

load_dotenv()
db_url = os.getenv("DB_URL")

engine = create_engine(db_url)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

