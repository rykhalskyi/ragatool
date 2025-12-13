from fastapi import APIRouter, Depends
from typing import List
from sqlite3 import Connection
from app.dependencies import get_db
from app.schemas.setting import Setting, SettingCreate
from app.crud import crud_setting

router = APIRouter()

@router.get("/", response_model=List[Setting])
def read_settings(db: Connection = Depends(get_db)):
    return crud_setting.get_settings(db)

@router.put("/", response_model=List[Setting])
def update_settings(settings: List[SettingCreate], db: Connection = Depends(get_db)):
    crud_setting.update_settings(db, settings)
    return crud_setting.get_settings(db)
