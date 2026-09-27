from fastapi import APIRouter, Body
from app.repositories import settings_repo
router = APIRouter()
@router.get("/settings")
def settings(): return settings_repo.get_all()
@router.put("/settings")
def put_settings(body: dict = Body(...)):
    for k, v in body.items(): settings_repo.set_value(k, v)
    return settings_repo.get_all()
