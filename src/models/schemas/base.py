# models/schemas/base.py
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, Dict, List

class TimestampModel(BaseModel):
    created_at: datetime
    updated_at: datetime

    #class Config:
    #    orm_mode = True


