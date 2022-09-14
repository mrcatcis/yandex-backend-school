from datetime import datetime

from fastapi import FastAPI, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from db_requests import (
    addUnit,
    deleteUnit,
    getNode,
    getNodeHistory,
    getUnits,
    getUpdates,
    unitExist,
    updateUnit,
    deleteUnits,
    getHistory
)
from models import (
    Error,
    SystemItemHistoryResponse,
    SystemItemImport,
    SystemItemImportRequest,
)
from utils import str_to_time, time_to_str

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


@app.delete("/delete/")
def delete_items():
    return deleteUnits()

@app.get("/get_history/")
def get_history():
    return getHistory()

@app.delete("/delete/{id}")
def delete_item(id: str, date: datetime, response: Response):
    if not unitExist(id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return Error(code=404, message="Item not found")
    deleteUnit(id, date)


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
    if not unitExist(id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return Error(code=404, message="Item not found")
    return getNodeHistory(id, dateStart, dateEnd)

# !TODO save history after full processing import task, 
# !     save on operations with childs if it's not an empty folder(size changed)
# !     probably do full backup where parentID == None and watch changed
# !     deploy MVP to yandex server