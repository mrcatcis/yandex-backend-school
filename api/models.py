from pydantic import BaseModel
from typing import List
import enum

class SystemItemType(enum.Enum):
    FILE = "FILE"
    FOLDER = "FOLDER"

class SystemItem(BaseModel):
    id: str
    url: str | None = None
    date: str
    parentId: str | None = None
    type: SystemItemType
    size: int | None
    children: List[str] | None = None

class SystemItemImport(BaseModel):
    id: str
    url: str | None = None
    parentId: str | None = None
    type: SystemItemType
    size: int | None
    
class SystemItemImportRequest(BaseModel):
    items: List[SystemItemImport]
    updateDate: str

class Error(BaseModel):
    code: int
    message: str