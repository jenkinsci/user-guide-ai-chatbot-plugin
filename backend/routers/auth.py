from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import schemas, crud, models

router = APIRouter(prefix="/api/auth", tags=["Auth"])
