from datetime import datetime, timedelta
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
    and_,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy.orm.session import Session


from models import (
    SystemItem,
    SystemItemImport,
    SystemItemType,
    SystemItemHistoryUnit,
    SystemItemHistoryResponse,
)
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
    history = relationship("History", back_populates="unit")


class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    unit_id = Column(
        String(length=STRING_SIZE),
        ForeignKey("unit.id"),
    )
    unit = relationship("Unit", back_populates="history")
    url = Column(String(length=STRING_SIZE), nullable=True)
    date = Column(DateTime)
    parentId = Column(String(length=STRING_SIZE), nullable=True)
    type = Column(Enum(SystemItemType))
    size = Column(BigInteger, nullable=True)


Base.metadata.create_all(engine)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()


def updateParentDate(parentId: str, date: datetime):
    if parentId is None:
        return
    parent = session.query(Unit).get(parentId)
    while parent is not None and parent.id is not None:
        size = getNode(parent.id).size
        old_unit = History(
            unit_id=parent.id,
            url=parent.url,
            parentId=parent.parentId,
            size=size,
            type=parent.type,
            date=parent.date,
        )
        session.add(old_unit)
        session.commit()

        session.query(Unit).filter(Unit.id == parent.id).update({Unit.date: date})
        session.commit()
        parent = session.query(Unit).get(parent.parentId)


def addUnit(unit: SystemItemImport, date: datetime):
    newUnit = Unit(
        id=unit.id,
        url=unit.url,
        date=date,
        parentId=unit.parentId,
        type=unit.type,
        size=unit.size,
    )
    updateParentDate(unit.parentId, date)
    session.add(newUnit)
    session.commit()


def getUnit(id: str) -> Unit:
    return session.query(Unit).get(id)


def unitExist(id: str) -> bool:
    return getUnit(id) is not None


def updateUnit(unit: SystemItemImport, date: datetime):

    size = getNode(unit.id).size
    unit = session.query(Unit).get(unit.id)
    old_unit = History(
        unit_id=unit.id,
        url=unit.url,
        date=unit.date,
        parentId=unit.parentId,
        type=unit.type,
        size=size,
    )
    session.add(old_unit)
    session.commit()

    session.query(Unit).filter(Unit.id == unit.id).update(
        {
            Unit.url: unit.url,
            Unit.date: date,
            Unit.parentId: unit.parentId,
            Unit.type: unit.type,
            Unit.size: unit.size,
        }
    )
    session.commit()

    updateParentDate(unit.parentId, date)
    


# get all units in folder with id=parent_id
def get_children(parent_id: str) -> List[Unit]:
    return session.query(Unit).filter(Unit.parentId == parent_id).all()


def deleteUnit(id: str, date: datetime):
    parentId = session.query(Unit).get(id).parentId

    def onlyDelete(id: str):
        unit = session.query(Unit).get(id)
        if unit.type == SystemItemType.FOLDER:
            for child in get_children(unit.id):
                onlyDelete(child.id)
        # delete all history
        session.query(History).filter(History.unit_id == id).delete()
        session.commit()
        # delete unit
        session.query(Unit).filter(Unit.id == id).delete()
        session.commit()

    onlyDelete(id)

    updateParentDate(parentId, date)


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


def deleteUnits():
    session.query(Unit).delete()
    session.query(History).delete()
    session.commit()

def getHistory():
    return session.query(History).all()

def getUpdates(date: datetime):
    day_ago = date - timedelta(days=1)
    updated = (
        session.query(Unit)
        .filter(
            and_(
                day_ago <= Unit.date,
                Unit.date <= date,
                Unit.type == SystemItemType.FILE,
            )
        )
        .all()
    )
    return SystemItemHistoryResponse(
        items=[
            SystemItemHistoryUnit(
                id=item.id,
                url=item.url,
                parentId=item.parentId,
                type=item.type,
                size=item.size,
                date=item.date,
            )
            for item in updated
        ]
    )


def getNodeHistory(
    id: str, date_start: datetime, date_end: datetime
) -> SystemItemHistoryResponse:
    nodeHistory = (
        session.query(History)
        .filter(
            and_(
                History.unit_id == id,
                date_start <= History.date,
                History.date < date_end,
            )
        )
        .all()
    )
    return SystemItemHistoryResponse(
        items=[
            SystemItemHistoryUnit(
                id=item.unit_id,
                url=item.url,
                parentId=item.parentId,
                type=item.type,
                date=item.date,
                size=item.size,
            )
            for item in nodeHistory
        ]
    )
