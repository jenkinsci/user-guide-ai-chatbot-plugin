from pydantic import BaseModel, EmailStr, ConfigDict, AwareDatetime
from typing import List, Optional
from datetime import datetime, date
import models

# ==========================================
# 0. SHARED CONFIGURATION
# ==========================================


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseConfigModel):
    """
    Base model for all responses.
    ConfigDict(from_attributes=True) is the Pydantic V2 equivalent of orm_mode=True.
    It tells Pydantic to read data using the dot notation (e.g. object.field)
    from SQLAlchemy database objects.
    """

    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    n_entities_deleted: int
