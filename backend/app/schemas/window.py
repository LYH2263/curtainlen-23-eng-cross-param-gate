from typing import Optional

from pydantic import BaseModel


class WindowUpdate(BaseModel):
    name: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    fullness: Optional[float] = None
    note: Optional[str] = None
