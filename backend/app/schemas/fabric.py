from typing import Optional

from pydantic import BaseModel


class FabricUpdate(BaseModel):
    name: Optional[str] = None
    fabric_width: Optional[float] = None
    hem_top: Optional[float] = None
    hem_bottom: Optional[float] = None
    note: Optional[str] = None
