from pydantic import BaseModel
from typing import List
from enum import Enum as EnumClass

class SystemItemType(EnumClass):
    FILE = "FILE"
    FOLDER = "FOLDER"

class SystemItem(BaseModel):
    id: str
    url: str | None = None
    date: str
    parent_id: str | None = None
    type: SystemItemType
    size: int | None
    children: List[str] | None = None

class SystemItemImport(BaseModel):
    id: str
    url: str | None = None
    parent_id: str | None = None
    type: SystemItemType
    size: int | None
    
class SystemItemImportRequest(BaseModel):
    items: List[SystemItemImport]
    updateDate: str

class Error(BaseModel):
    code: int
    message: str