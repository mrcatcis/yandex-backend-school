from fastapi import FastAPI, Response, status
from db_requests import (
    getUnits,
    addUnit,
    unitExist,
    updateUnit,
    deleteUnit,
    getNode,
)
from models import (
    SystemItemType,
    SystemItem,
    SystemItemImport,
    SystemItemImportRequest,
    Error,
)
from utils import time_to_str, str_to_time
from datetime import datetime

app = FastAPI()


@app.get("/get_items/")
def get_item() -> SystemItemImport:
    return getUnits()


@app.delete("/delete/{id}")
def delete_item(id: str, time: datetime, response: Response):
    time = time_to_str(time)
    if time is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Error(400, "Validation Failed")
    if not unitExist(id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return Error(code=404, message="Item not found")
    deleteUnit(id)


@app.post("/imports/")
def import_items(request: SystemItemImportRequest, response: Response):
    for item in request.items:
        if unitExist(item.id):
            updateUnit(item, request.updateDate)
        else:
            addUnit(item, request.updateDate)


@app.get("/nodes/{id}")
def get_info(id: str, response: Response):
    if not unitExist(id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return Error(code=404, message="Item not found")
    return getNode(id)
