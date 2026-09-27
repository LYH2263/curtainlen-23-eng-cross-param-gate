from fastapi import APIRouter, HTTPException
from app.repositories import fabrics as repo
from app.schemas.fabric import FabricUpdate
router = APIRouter()
@router.get("/fabrics")
def list_fabrics(): return {"items": repo.list_fabrics()}
@router.get("/fabrics/{fid}")
def get_fabric(fid: int):
    r = repo.get_fabric(fid)
    if not r: raise HTTPException(404)
    return r
@router.put("/fabrics/{fid}")
def put_fabric(fid: int, body: FabricUpdate):
    r = repo.update_fabric(fid, body.model_dump(exclude_none=True))
    if not r: raise HTTPException(404)
    return r
