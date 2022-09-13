from fastapi import FastAPI, Response, status
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from db_requests import (
    getUnits,
    addUnit,
    unitExist,
    updateUnit,
    deleteUnit,
    getNode,
    getUpdates,
    getNodeHistory,
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


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Overrides FastAPI default validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            Error(code=status.HTTP_400_BAD_REQUEST, message="Validation Failed")
        ),
    )


@app.get("/get_items/")
def get_item() -> SystemItemImport:
    return getUnits()


@app.delete("/delete/{id}")
def delete_item(id: str, time: datetime, response: Response):
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


@app.get("/updates/")
def get_updates(date: datetime, response: Response):
    return getUpdates(date)


@app.get("/node/{id}/history")
def get_node_history(
    id: str, dateStart: datetime, dateEnd: datetime, response: Response
):
    return getNodeHistory(id, dateStart, dateEnd)
