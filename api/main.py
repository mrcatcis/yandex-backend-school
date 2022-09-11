from fastapi import FastAPI
from models import (
    SystemItemType,
    SystemItem,
    SystemItemImport,
    SystemItemImportRequest,
    Error,
)

app = FastAPI()


@app.post("/imports/")
async def root(item: SystemItemImportRequest):
    return item
