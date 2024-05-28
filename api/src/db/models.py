from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from databases import Database
import os 

DATABASE_URL = f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPWD')}@{os.getenv('DB_URL')}"

database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    uid = Column(String, primary_key=True, index=True)
    firstname = Column(String, index=True,nullable=True)
    lastname = Column(String,  index=True,nullable=True) 
    email = Column(String, index=True,nullable=True)



# Create the database tables
Base.metadata.create_all(bind=engine)