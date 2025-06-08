from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime

class ValuePoint(BaseModel):
    """
    Defines the structure for a "ValuePoint" (VP).

    ValuePoints represent discrete units of value or interaction within the
    system, such as tasks, contracts, payments, earnings, or settlements.
    They are used to model workflows and track user progress or obligations.
    """
    id: str  # Unique identifier for the ValuePoint
    title: str  # Human-readable title or name of the VP
    vp_type: Literal["payment", "contract", "task", "earn", "settle"]  # The specific type of the VP
    price_usd: Optional[float] = None  # Price in USD, if applicable
    price_sat: Optional[int] = None  # Price in satoshis, if applicable
    next: List[str] = Field(default_factory=list)  # List of IDs of child ValuePoints that can follow this one
    expires: Optional[datetime] = None  # Optional expiration date/time for the VP
    interface: str  # UI slug or path identifier for the markdown file defining the VP's interface
    creditable: bool = True  # Whether completing this VP grants credits to the user
    btc_commit: bool = False  # Whether this VP involves a Bitcoin on-chain commitment or transaction

class UserContext(BaseModel):
    """
    Defines the structure for user-specific data and state.

    This model holds information about a user, including their active and
    completed ValuePoints, credit balances, last known input, and other
    infrastructure-related details necessary for their interaction with the system.
    """
    user_id: str  # Unique identifier for the user (often a username)
    active_vps: List[str] = Field(default_factory=list)  # List of IDs of ValuePoints currently active for the user
    completed_vps: List[str] = Field(default_factory=list)  # List of IDs of ValuePoints completed by the user
    credits_usd: float = 0.0  # User's current balance in USD
    credits_sat: int = 0  # User's current balance in satoshis
    last_input: Optional[str] = None  # Stores the last input or action text from the user
    infra: Dict = Field(default_factory=dict)  # Dictionary for user-specific infrastructure details (e.g., local paths, mirror URLs, LNURL)
