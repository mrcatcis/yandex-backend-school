from datetime import datetime
from os import getenv
from typing import List

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

from models import SystemItem, SystemItemImport, SystemItemType
from utils import str_to_time, time_to_str

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
    type = Column(Enum(SystemItemType))
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
    parentId = unit.parentId
    while parentId is not None:
        session.query(Unit).filter(Unit.id == parentId).update({Unit.date: date})
        parent = session.query(Unit).get(parentId)
        parentId = parent and parent.parentId
    session.add(newUnit)
    session.commit()


def getUnit(id: str) -> Unit:
    return session.query(Unit).get(id)


def unitExist(id: str) -> bool:
    return getUnit(id) is not None


def updateUnit(unit: SystemItemImport, date: datetime):
    session.query(Unit).filter(Unit.id == unit.id).update(
        {
            Unit.url: unit.url,
            Unit.date: date,
            Unit.parentId: unit.parentId,
            Unit.type: unit.type,
            Unit.size: unit.size,
        }
    )
    parentId = unit.parentId
    while parentId is not None:
        session.query(Unit).filter(Unit.id == parentId).update({Unit.date: date})
        parent = session.query(Unit).get(parentId)
        parentId = parent and parent.parentId
    session.commit()


# get all units in folder with id=$parent_id
def get_children(parent_id: str) -> List[Unit]:
    return session.query(Unit).filter(Unit.parentId == parent_id).all()


def deleteUnit(id: str):
    unit = session.query(Unit).get(id)
    if unit.type == SystemItemType.FOLDER:
        for child in get_children(unit.id):
            deleteUnit(child.id)
    session.query(Unit).filter(Unit.id == id).delete()
    session.commit()


def getUnitInfo(id: str) -> SystemItem:
    unit = getUnit(id)
    if unit.type == SystemItemType.FOLDER:
        children = get_children(id)
        return SystemItem(
            id=unit.id,
            url=unit.url,
            date=time_to_str(unit.date),
            parentId=unit.parentId,
            type=unit.type,
            children=[getUnitInfo(item.id) for item in children],
            size=unit.size,
        )
    else:
        return SystemItem(
            id=unit.id,
            url=unit.url,
            date=time_to_str(unit.date),
            parentId=unit.parentId,
            type=unit.type,
            size=unit.size,
        )


def getUnitInfoSized(unit_info: SystemItem) -> SystemItem:
    unit_info.size = sum(
        item.size if item.size is not None else getUnitInfoSized(item).size
        for item in unit_info.children
    )
    return unit_info


def getNode(id: str) -> SystemItem:
    return getUnitInfoSized(getUnitInfo(id))


def getUnits():
    return session.query(Unit).all()

def getUpdates(date: datetime): # TODO implement
    pass

def getNodeHistory(id: str, date_start: datetime, date_end: datetime): # TODO implement
    pass