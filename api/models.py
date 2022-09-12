from datetime import datetime, timezone
import enum
from typing import List

from pydantic import BaseModel, Field, validator



class SystemItemType(enum.Enum):
    FILE = "FILE"
    FOLDER = "FOLDER"

def convert_datetime_to_iso_8601_with_z_suffix(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
def transform_to_utc_datetime(dt: datetime) -> datetime:
    return dt.astimezone(tz=timezone.utc)



class SystemItem(BaseModel):
    id: str
    url: str | None = None
    date: str
    parentId: str | None = None
    type: SystemItemType
    size: int | None
    children: List["SystemItem"] | None = None


class SystemItemImport(BaseModel):
    id: str
    url: str | None = None
    parentId: str | None = None
    type: SystemItemType
    size: int | None


class SystemItemImportRequest(BaseModel):
    items: List[SystemItemImport]
    updateDate: datetime


class Error(BaseModel):
    code: int
    message: str
