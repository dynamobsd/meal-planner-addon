"""Réglages clé/valeur persistés (ex: préférences de goûts pour les suggestions)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AppSetting
from ..schemas import SettingIn, SettingOut

router = APIRouter(tags=["settings"])


@router.get("/settings/{cle}", response_model=SettingOut)
def get_setting(cle: str, db: Session = Depends(get_db)):
    row = db.scalar(select(AppSetting).where(AppSetting.cle == cle))
    return SettingOut(cle=cle, valeur=row.valeur if row else None)


@router.put("/settings/{cle}", response_model=SettingOut)
def put_setting(cle: str, payload: SettingIn, db: Session = Depends(get_db)):
    row = db.scalar(select(AppSetting).where(AppSetting.cle == cle))
    if row is None:
        row = AppSetting(cle=cle, valeur=payload.valeur)
        db.add(row)
    else:
        row.valeur = payload.valeur
    db.commit()
    return SettingOut(cle=cle, valeur=row.valeur)
