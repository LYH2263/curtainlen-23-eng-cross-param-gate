from pydantic import BaseModel

class WindowUpdate(BaseModel):
    width: float | None = None
    height: float | None = None
    fullness: float | None = None
    note: str | None = None

class FabricUpdate(BaseModel):
    fabric_width: float | None = None
    hem_top: float | None = None
    hem_bottom: float | None = None
    note: str | None = None
