from datetime import datetime, timedelta
from os import getenv
from typing import List

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    and_,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy.orm.session import Session

from config import (
    DATABASE_HOST,
    DATABASE_PORT,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_USER,
    STRING_SIZE,
)
from models import (
    SystemItem,
    SystemItemHistoryResponse,
    SystemItemHistoryUnit,
    SystemItemImport,
    SystemItemImportRequest,
    SystemItemType,
)
from utils import time_to_str

engine = create_engine(
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{POSTGRES_DB}"
)

Base = declarative_base()


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


class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    unit_id = Column(String(length=STRING_SIZE))
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
    last_parent = parent
    while parent is not None and parent.parentId is not None:
        session.query(Unit).filter(Unit.id == parent.id).update({Unit.date: date})
        session.commit()
        last_parent = parent
        parent = session.query(Unit).get(parent.parentId)
    return last_parent


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


def updateUnit(unit: SystemItemImport, date: datetime):
    # unit = session.query(Unit).get(unit.id)

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


def getUnit(id: str) -> Unit:
    return session.query(Unit).get(id)


def unitExist(id: str) -> bool:
    return getUnit(id) is not None


# get all units in folder with id=parent_id
def get_children(parent_id: str) -> List[Unit]:
    return session.query(Unit).filter(Unit.parentId == parent_id).all()


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
    if not unit_info.children:
        return unit_info
    unit_info.size = sum(
        item.size if item.type == SystemItemType.FILE else getUnitInfoSized(item).size
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
    id: str,
    date_start: datetime | None,
    date_end: datetime | None,
) -> SystemItemHistoryResponse:
    if date_start is None:
        nodeHistory = (
            session.query(History)
            .filter(
                History.unit_id == id,
            )
            .all()
        )

    else:
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


def dumpSystemItem(item: SystemItem) -> None:
    dump = History(
        unit_id=item.id,
        url=item.url,
        parentId=item.parentId,
        type=item.type,
        date=item.date,
        size=item.size,
    )
    if (
        session.query(History)
        .filter(
            and_(
                History.unit_id == dump.unit_id,
                History.date == dump.date,
                History.url == dump.url,
                History.parentId == dump.parentId,
                History.type == dump.type,
                History.size == dump.size,
            )
        )
        .first()
        is None
    ):
        session.add(dump)
        session.commit()


def dumpEndParent(end_parent_id):
    def recDumpChilds(unit: SystemItem):
        dumpSystemItem(unit)
        for item in unit.children or []:
            recDumpChilds(item)

    node = getNode(end_parent_id)
    recDumpChilds(node)


def dumpAll():
    parents = session.query(Unit).filter(Unit.parentId == None).all()
    for parent in parents:
        dumpEndParent(parent.id)


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
    updateSizes(date)
    dumpAll()


def updateSizes(date: datetime):
    parents = session.query(Unit).filter(Unit.parentId == None).all()

    def recUpdateUnit(unit: SystemItem):
        current_item = getUnit(unit.id)
        if current_item.size != unit.size:
            updateUnit(unit, date)
        for item in unit.children or []:
            recUpdateUnit(item)

    for parent in parents:
        recUpdateUnit(getNode(parent.id))
    dumpAll()


def importItems(imported: SystemItemImportRequest):
    for item in imported.items:
        if unitExist(item.id):
            updateUnit(item, imported.updateDate)
        else:
            addUnit(item, imported.updateDate)
    updateSizes(imported.updateDate)
