from pydantic import BaseModel, ConfigDict
from datetime import datetime

# ==========================================
# CHAT SCHEMAS
# ==========================================

# Data required to create a new chat
class ChatCreateRequest(BaseModel):
    title: str

# Data returned to the client
class ChatResponse(BaseModel):
    id: int
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    
    # Enables automatic mapping from SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)