from fastapi import APIRouter, HTTPException
from app.repositories import windows as repo
from app.schemas.window import WindowUpdate
router = APIRouter()
@router.get("/windows")
def list_windows(): return {"items": repo.list_windows()}
@router.get("/windows/{wid}")
def get_window(wid: int):
    r = repo.get_window(wid)
    if not r: raise HTTPException(404)
    return r
@router.put("/windows/{wid}")
def put_window(wid: int, body: WindowUpdate):
    r = repo.update_window(wid, body.model_dump(exclude_none=True))
    if not r: raise HTTPException(404)
    return r
