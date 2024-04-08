from typing import Optional
from pydantic import BaseModel


class SettingsModel(BaseModel):
    user_admin: str
    food_l1_pct: float
    food_l2_pct: float


class UpdateSettingsModel(BaseModel):
    user_admin: Optional[str] = None
    food_l1_pct: Optional[float] = None
    food_l2_pct: Optional[float] = None


class StatisticsModel(BaseModel):
    total_orders: int
    total_delivered: int
    total_earnings: float
    earnings_payed: float


#
