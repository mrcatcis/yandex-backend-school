from os import getenv

from fastapi import HTTPException
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Table,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, backref, relationship
from sqlalchemy.orm.session import Session

POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
DATABASE_HOST = getenv("DATABASE_HOST")
DATABASE_PORT = getenv("DATABASE_PORT")
POSTGRES_DB = getenv("POSTGRES_DB")

engine = create_engine(
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{POSTGRES_DB}"
)

Base = declarative_base()


class Unit(Base):
    __tablename__ = "unit"
    id = Column(
        String(length=256),
        primary_key=True,
        nullable=False,
        unique=True,
        autoincrement=False,
    )


Base.metadata.create_all(engine)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


def addUnit(id: str):
    newUnit = Unit(id=id)
    session.add(newUnit)
    session.commit()


def getUnits():
    units = session.query(Unit).all()
    for unit in units:
        yield unit.id
