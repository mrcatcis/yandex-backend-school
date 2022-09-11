from fastapi import FastAPI
from db_requests import getUnits, addUnit
from models import (
    SystemItemType,
    SystemItem,
    SystemItemImport,
    SystemItemImportRequest,
    Error,
)

app = FastAPI()


@app.get("/get_units/")
def get_unit() -> SystemItemImport:
    return list(getUnits())


@app.post("/add_unit/")
def add_unit(unit: SystemItemImport):
    addUnit(unit.id)


@app.post("/imports/")
def root(item: SystemItemImportRequest):
    return item
