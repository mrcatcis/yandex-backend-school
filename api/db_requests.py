from datetime import datetime
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
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy.orm.session import Session
from utils import str_to_time

from models import SystemItem, SystemItemType, SystemItemImport

POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
DATABASE_HOST = getenv("DATABASE_HOST")
DATABASE_PORT = getenv("DATABASE_PORT")
POSTGRES_DB = getenv("POSTGRES_DB")

engine = create_engine(
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{POSTGRES_DB}"
)

Base = declarative_base()

STRING_SIZE = 256


class Unit(Base):
    __tablename__ = "unit"
    id = Column(
        String(length=STRING_SIZE),
        primary_key=True,
        nullable=False,
        unique=True,
        autoincrement=False,
    )
    url = Column(String(length=STRING_SIZE), nullable=True)
    date = Column(DateTime)
    parentId = Column(String(length=STRING_SIZE), nullable=True)
    type = Enum(SystemItemType)
    size = Column(BigInteger, nullable=True)


Base.metadata.create_all(engine)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


def addUnit(unit: SystemItemImport, date: datetime):
    newUnit = Unit(
        id=unit.id,
        url=unit.url,
        date=date,
        parentId=unit.parentId,
        type=unit.type,
        size=unit.size,
    )
    session.add(newUnit)
    session.commit()


def unitExist(id: str) -> bool:
    units = session.query(Unit).filter_by(id=id).all()
    return len(units) > 0


def updateUnit(unit: SystemItemImport, date: datetime):
    session.query(Unit).filter(Unit.id==unit.id).update(
        {
            Unit.url: unit.url,
            Unit.date: date,
            Unit.parentId: unit.parentId,
            Unit.type: unit.type,
            Unit.size: unit.size,
        }
    )
    session.commit()


def getUnits():
    units = session.query(Unit).all()
    return units
