from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime

class ValuePoint(BaseModel):
    id: str
    title: str
    vp_type: Literal["payment", "contract", "task", "earn", "settle"]
    price_usd: Optional[float] = None
    price_sat: Optional[int] = None
    next: List[str] = Field(default_factory=list)  # child VPs
    expires: Optional[datetime] = None
    interface: str  # UI slug to load
    creditable: bool = True
    btc_commit: bool = False

class UserContext(BaseModel):
    user_id: str
    active_vps: List[str] = Field(default_factory=list)
    completed_vps: List[str] = Field(default_factory=list)
    credits_usd: float = 0.0
    credits_sat: int = 0
    last_input: Optional[str] = None
    infra: Dict = Field(default_factory=dict)  # local path, mirror URL, LNURL, etc.
