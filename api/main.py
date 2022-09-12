from fastapi import FastAPI
from db_requests import getUnits, addUnit, unitExist, updateUnit
from models import (
    SystemItemType,
    SystemItem,
    SystemItemImport,
    SystemItemImportRequest,
    Error,
)
from utils import time_to_str, str_to_time

app = FastAPI()


@app.get("/get_units/")
def get_unit() -> SystemItemImport:
    return getUnits()


@app.post("/add_unit/")
def add_unit(unit: SystemItemImport):
    addUnit(unit.id)


@app.post("/imports/")
def imports(request: SystemItemImportRequest):
    updateDate = str_to_time(request.updateDate)
    for item in request.items:
        if unitExist(item.id):
            updateUnit(item, updateDate)
        else:
            addUnit(item, updateDate)
